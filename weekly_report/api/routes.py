"""FastAPI routes for weekly report API."""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from pathlib import Path
import tempfile
import os
from loguru import logger

from weekly_report.src.periods.calculator import get_periods_for_week, get_week_date_range, get_ytd_periods_for_week, validate_iso_week
from weekly_report.src.metrics.table1 import calculate_table1_for_periods, calculate_table1_for_periods_with_ytd
from weekly_report.src.metrics.markets import calculate_top_markets_for_weeks
from weekly_report.src.metrics.online_kpis import calculate_online_kpis_for_weeks
from weekly_report.src.pdf.table1_builder import build_table1_pdf
from weekly_report.src.cache.manager import metrics_cache
from weekly_report.src.config import load_config


# Pydantic models
class PeriodsResponse(BaseModel):
    actual: str
    last_week: str
    last_year: str
    year_2023: str
    date_ranges: Dict[str, Dict[str, str]]
    ytd_periods: Dict[str, Dict[str, str]]


class MetricsResponse(BaseModel):
    periods: Dict[str, Dict[str, Any]]


class GeneratePDFRequest(BaseModel):
    base_week: str
    periods: List[str]


class MarketData(BaseModel):
    country: str
    weeks: Dict[str, float]  # Explicit dict type
    average: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "country": "United States",
                "weeks": {"2025-42": 450000, "2024-42": 420000},
                "average": 435000
            }
        }

class MarketsResponse(BaseModel):
    markets: List[MarketData]  # Use explicit model instead of Dict[str, Any]
    period_info: Dict[str, str]


class KPIData(BaseModel):
    week: str
    aov_new_customer: float
    aov_returning_customer: float
    cos: float
    conversion_rate: float
    new_customers: int
    returning_customers: int
    sessions: int
    new_customer_cac: float
    total_orders: int
    last_year: Optional[Dict[str, Any]] = None


class OnlineKPIsResponse(BaseModel):
    kpis: List[KPIData]
    period_info: Dict[str, Any]


# Initialize FastAPI app
app = FastAPI(
    title="Weekly Report API",
    description="API for generating weekly report tables",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001", "http://localhost:3002", "http://127.0.0.1:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/periods", response_model=PeriodsResponse)
async def get_periods(base_week: str = Query(..., description="Base ISO week like '2025-42'")):
    """Get period information for a base week."""
    
    try:
        # Validate input
        if not validate_iso_week(base_week):
            raise HTTPException(status_code=400, detail=f"Invalid ISO week format: {base_week}")
        
        # Calculate periods
        periods = get_periods_for_week(base_week)
        
        # Get YTD periods
        ytd_periods = get_ytd_periods_for_week(base_week)
        
        # Get date ranges for each period
        date_ranges = {}
        for period_name, period_week in periods.items():
            try:
                date_ranges[period_name] = get_week_date_range(period_week)
            except Exception as e:
                logger.warning(f"Could not get date range for {period_week}: {e}")
                date_ranges[period_name] = {
                    'start': 'N/A',
                    'end': 'N/A', 
                    'display': 'N/A'
                }
        
        return PeriodsResponse(
            actual=periods['actual'],
            last_week=periods['last_week'],
            last_year=periods['last_year'],
            year_2023=periods['year_2023'],
            date_ranges=date_ranges,
            ytd_periods=ytd_periods
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting periods for {base_week}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/metrics/table1", response_model=MetricsResponse)
async def get_table1_metrics(
    base_week: str = Query(..., description="Base ISO week like '2025-42'"),
    periods: str = Query("actual,last_week,last_year,year_2023", description="Comma-separated list of periods"),
    include_ytd: bool = Query(True, description="Include YTD columns")
):
    """Get Table 1 metrics for specified periods."""
    
    try:
        # Validate input
        if not validate_iso_week(base_week):
            raise HTTPException(status_code=400, detail=f"Invalid ISO week format: {base_week}")
        
        # Parse periods
        requested_periods = [p.strip() for p in periods.split(',')]
        valid_periods = ['actual', 'last_week', 'last_year', 'year_2023']
        
        for period in requested_periods:
            if period not in valid_periods:
                raise HTTPException(status_code=400, detail=f"Invalid period: {period}")
        
        # Check cache first
        cached_result = metrics_cache.get(base_week, requested_periods)
        if cached_result and not include_ytd:
            return MetricsResponse(periods=cached_result)
        
        # Calculate all periods
        all_periods = get_periods_for_week(base_week)
        
        # Filter to requested periods
        filtered_periods = {k: v for k, v in all_periods.items() if k in requested_periods}
        
        # Load config to get data root
        config = load_config(week=base_week)
        
        # Calculate metrics
        if include_ytd:
            metrics_results = calculate_table1_for_periods_with_ytd(filtered_periods, Path(config.data_root))
        else:
            metrics_results = calculate_table1_for_periods(filtered_periods, Path(config.data_root))
        
        # Cache the results
        metrics_cache.set(base_week, requested_periods, metrics_results)
        
        return MetricsResponse(periods=metrics_results)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting metrics for {base_week}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/generate/pdf")
async def generate_pdf(request: GeneratePDFRequest):
    """Generate PDF with confirmed data."""
    
    try:
        # Validate input
        if not validate_iso_week(request.base_week):
            raise HTTPException(status_code=400, detail=f"Invalid ISO week format: {request.base_week}")
        
        # Calculate periods
        all_periods = get_periods_for_week(request.base_week)
        
        # Filter to requested periods
        filtered_periods = {k: v for k, v in all_periods.items() if k in request.periods}
        
        # Load config
        config = load_config(week=request.base_week)
        
        # Calculate metrics
        metrics_results = calculate_table1_for_periods(filtered_periods, Path(config.data_root))
        
        # Generate PDF using the professional builder
        output_path = config.reports_path / f"table1_{request.base_week}.pdf"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Build the PDF
        pdf_path = build_table1_pdf(metrics_results, filtered_periods, output_path)
        
        logger.info(f"Generated PDF: {pdf_path}")
        
        return {
            "success": True,
            "file_path": str(pdf_path),
            "download_url": f"/api/download/{pdf_path.name}"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating PDF for {request.base_week}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/download/{filename}")
async def download_file(filename: str):
    """Download generated PDF file."""
    
    try:
        # Security: only allow PDF files
        if not filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Look for file in reports directory
        config = load_config()
        reports_path = Path(config.data_root) / "reports"
        
        # Find the file
        file_path = None
        for subdir in reports_path.iterdir():
            if subdir.is_dir():
                potential_file = subdir / filename
                if potential_file.exists():
                    file_path = potential_file
                    break
        
        if not file_path:
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Error downloading file {filename}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/cache/clear")
async def clear_cache():
    """Clear all cached metrics and raw data."""
    try:
        metrics_cache.clear()
        # Also clear raw data cache
        from weekly_report.src.metrics.table1 import raw_data_cache
        raw_data_cache.clear()
        return {"success": True, "message": "All caches cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")


@app.post("/api/cache/invalidate/{base_week}")
async def invalidate_cache(base_week: str):
    """Invalidate cache for a specific week."""
    try:
        metrics_cache.invalidate(base_week)
        return {"success": True, "message": f"Cache invalidated for {base_week}"}
    except Exception as e:
        logger.error(f"Error invalidating cache for {base_week}: {e}")
        raise HTTPException(status_code=500, detail="Failed to invalidate cache")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "weekly-report-api"}


@app.get("/api/debug/markets")
async def debug_markets(
    base_week: str = Query(..., description="Base ISO week like '2025-42'"),
    num_weeks: int = Query(8, description="Number of weeks to analyze")
):
    """Debug endpoint to see raw markets data."""
    
    config = load_config(week=base_week)
    markets_data = calculate_top_markets_for_weeks(base_week, num_weeks, config.data_root)
    
    # Return raw data without Pydantic
    return markets_data


@app.get("/api/markets/top", response_model=MarketsResponse)
async def get_top_markets(
    base_week: str = Query(..., description="Base ISO week like '2025-42'"),
    num_weeks: int = Query(8, description="Number of weeks to analyze")
):
    """Get top markets based on average Online Gross Revenue over last N weeks."""
    
    try:
        # Validate input
        if not validate_iso_week(base_week):
            raise HTTPException(status_code=400, detail=f"Invalid ISO week format: {base_week}")
        
        if num_weeks < 1 or num_weeks > 52:
            raise HTTPException(status_code=400, detail=f"Number of weeks must be between 1 and 52")
        
        # Load config to get data root
        config = load_config(week=base_week)
        
        # Calculate top markets - use data_root not raw_data_path
        markets_data = calculate_top_markets_for_weeks(base_week, num_weeks, config.data_root)
        
        # Debug: Log raw data
        logger.info(f"Raw data - First market weeks count: {len(markets_data['markets'][0]['weeks'])}")
        logger.info(f"Raw data - Sample weeks: {list(markets_data['markets'][0]['weeks'].keys())[:5]}")
        
        response = MarketsResponse(**markets_data)
        
        # Debug: Log after Pydantic
        logger.info(f"After Pydantic - First market weeks count: {len(response.markets[0].weeks)}")
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        logger.error(f"Error getting top markets for {base_week}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/online-kpis", response_model=OnlineKPIsResponse)
async def get_online_kpis(
    base_week: str = Query(..., description="Base ISO week like '2025-42'"),
    num_weeks: int = Query(8, description="Number of weeks to analyze")
):
    """Get Online KPIs for the last N weeks."""
    
    try:
        # Validate input
        if not validate_iso_week(base_week):
            raise HTTPException(status_code=400, detail=f"Invalid ISO week format: {base_week}")
        
        if num_weeks < 1 or num_weeks > 52:
            raise HTTPException(status_code=400, detail=f"Number of weeks must be between 1 and 52")
        
        # Load config to get data root
        config = load_config(week=base_week)
        
        # Calculate Online KPIs - use data_root not raw_data_path
        kpis_data = calculate_online_kpis_for_weeks(base_week, num_weeks, config.data_root)
        
        response = OnlineKPIsResponse(**kpis_data)
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        logger.error(f"Error getting Online KPIs for {base_week}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
