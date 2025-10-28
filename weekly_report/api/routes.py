"""FastAPI routes for weekly report API."""

from fastapi import FastAPI, HTTPException, Query, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from pathlib import Path
import tempfile
import os
import shutil
from datetime import datetime
from loguru import logger
import pandas as pd
import pandas as pd

from weekly_report.src.periods.calculator import get_periods_for_week, get_week_date_range, get_ytd_periods_for_week, validate_iso_week
from weekly_report.src.metrics.table1 import calculate_table1_for_periods, calculate_table1_for_periods_with_ytd
from weekly_report.src.metrics.markets import calculate_top_markets_for_weeks
from weekly_report.src.metrics.online_kpis import calculate_online_kpis_for_weeks
from weekly_report.src.metrics.contribution import calculate_contribution_for_weeks
from weekly_report.src.metrics.gender_sales import calculate_gender_sales_for_weeks
from weekly_report.src.metrics.men_category_sales import calculate_men_category_sales_for_weeks
from weekly_report.src.metrics.women_category_sales import calculate_women_category_sales_for_weeks
from weekly_report.src.metrics.category_sales import calculate_category_sales_for_weeks
from weekly_report.src.metrics.top_products import calculate_top_products_for_weeks
from weekly_report.src.metrics.top_products_gender import calculate_top_products_by_gender_for_weeks
from weekly_report.src.metrics.sessions_per_country import calculate_sessions_per_country_for_weeks
from weekly_report.src.metrics.conversion_per_country import calculate_conversion_per_country_for_weeks
from weekly_report.src.metrics.new_customers_per_country import calculate_new_customers_per_country_for_weeks
from weekly_report.src.metrics.returning_customers_per_country import calculate_returning_customers_per_country_for_weeks
from weekly_report.src.metrics.aov_new_customers_per_country import calculate_aov_new_customers_per_country_for_weeks
from weekly_report.src.metrics.aov_returning_customers_per_country import calculate_aov_returning_customers_per_country_for_weeks
from weekly_report.src.metrics.marketing_spend_per_country import calculate_marketing_spend_per_country_for_weeks
from weekly_report.src.metrics.ncac_per_country import calculate_ncac_per_country_for_weeks
from weekly_report.src.metrics.contribution_new_per_country import calculate_contribution_new_per_country_for_weeks
from weekly_report.src.metrics.contribution_new_total_per_country import calculate_contribution_new_total_per_country_for_weeks
from weekly_report.src.metrics.contribution_returning_per_country import calculate_contribution_returning_per_country_for_weeks
from weekly_report.src.metrics.contribution_returning_total_per_country import calculate_contribution_returning_total_per_country_for_weeks
from weekly_report.src.metrics.total_contribution_per_country import calculate_total_contribution_per_country_for_weeks
from weekly_report.src.metrics.batch_calculator import calculate_all_metrics
from weekly_report.src.pdf.table1_builder import build_table1_pdf
from weekly_report.src.cache.manager import metrics_cache, raw_data_cache
from weekly_report.src.config import load_config
from weekly_report.src.utils.file_metadata import extract_file_metadata


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
    marketing_spend: float
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


class ContributionData(BaseModel):
    week: str
    gross_revenue_new: float
    gross_revenue_returning: float
    contribution_new: float
    contribution_returning: float
    contribution_total: float
    last_year: Optional[Dict[str, Any]] = None


class ContributionResponse(BaseModel):
    contributions: List[ContributionData]
    period_info: Dict[str, Any]


class GenderSalesData(BaseModel):
    week: str
    men_unisex_sales: float
    women_sales: float
    total_sales: float
    last_year: Optional[Dict[str, Any]] = None


class GenderSalesResponse(BaseModel):
    gender_sales: List[GenderSalesData]
    period_info: Dict[str, Any]


class MenCategorySalesData(BaseModel):
    week: str
    categories: Dict[str, float]
    last_year: Optional[Dict[str, Any]] = None


class MenCategorySalesResponse(BaseModel):
    men_category_sales: List[MenCategorySalesData]
    period_info: Dict[str, Any]


class WomenCategorySalesData(BaseModel):
    week: str
    categories: Dict[str, float]
    last_year: Optional[Dict[str, Any]] = None


class WomenCategorySalesResponse(BaseModel):
    women_category_sales: List[WomenCategorySalesData]
    period_info: Dict[str, Any]


class CategorySalesData(BaseModel):
    week: str
    categories: Dict[str, float]
    last_year: Optional[Dict[str, Any]] = None


class CategorySalesResponse(BaseModel):
    category_sales: List[CategorySalesData]
    period_info: Dict[str, Any]


class ProductData(BaseModel):
    rank: int
    gender: str
    category: str
    product: str
    color: str
    gross_revenue: float
    sales_qty: int


class TopProductsData(BaseModel):
    week: str
    products: List[ProductData]
    top_total: Dict[str, Any]
    grand_total: Dict[str, Any]


class TopProductsResponse(BaseModel):
    top_products: List[TopProductsData]
    period_info: Dict[str, Any]


class SessionsPerCountryData(BaseModel):
    week: str
    countries: Dict[str, float]
    last_year: Optional[Dict[str, Any]] = None


class SessionsPerCountryResponse(BaseModel):
    sessions_per_country: List[SessionsPerCountryData]
    period_info: Dict[str, Any]


class ConversionPerCountryData(BaseModel):
    week: str
    countries: Dict[str, Dict[str, Any]]
    last_year: Optional[Dict[str, Any]] = None


class ConversionPerCountryResponse(BaseModel):
    conversion_per_country: List[ConversionPerCountryData]
    period_info: Dict[str, Any]


class NewCustomersPerCountryData(BaseModel):
    week: str
    countries: Dict[str, float]
    last_year: Optional[Dict[str, Any]] = None


class NewCustomersPerCountryResponse(BaseModel):
    new_customers_per_country: List[NewCustomersPerCountryData]
    period_info: Dict[str, Any]


class ReturningCustomersPerCountryData(BaseModel):
    week: str
    countries: Dict[str, float]
    last_year: Optional[Dict[str, Any]] = None


class ReturningCustomersPerCountryResponse(BaseModel):
    returning_customers_per_country: List[ReturningCustomersPerCountryData]
    period_info: Dict[str, Any]


class AOVNewCustomersPerCountryData(BaseModel):
    week: str
    countries: Dict[str, float]
    last_year: Optional[Dict[str, Any]] = None


class AOVNewCustomersPerCountryResponse(BaseModel):
    aov_new_customers_per_country: List[AOVNewCustomersPerCountryData]
    period_info: Dict[str, Any]


class AOVReturningCustomersPerCountryData(BaseModel):
    week: str
    countries: Dict[str, float]
    last_year: Optional[Dict[str, Any]] = None


class AOVReturningCustomersPerCountryResponse(BaseModel):
    aov_returning_customers_per_country: List[AOVReturningCustomersPerCountryData]
    period_info: Dict[str, Any]


class MarketingSpendPerCountryData(BaseModel):
    week: str
    countries: Dict[str, float]
    last_year: Optional[Dict[str, Any]] = None


class MarketingSpendPerCountryResponse(BaseModel):
    marketing_spend_per_country: List[MarketingSpendPerCountryData]
    period_info: Dict[str, Any]


class nCACPerCountryData(BaseModel):
    week: str
    countries: Dict[str, float]
    last_year: Optional[Dict[str, Any]] = None


class nCACPerCountryResponse(BaseModel):
    ncac_per_country: List[nCACPerCountryData]
    period_info: Dict[str, Any]


class ContributionNewPerCountryData(BaseModel):
    week: str
    countries: Dict[str, float]
    last_year: Optional[Dict[str, Any]] = None


class ContributionNewPerCountryResponse(BaseModel):
    contribution_new_per_country: List[ContributionNewPerCountryData]
    period_info: Dict[str, Any]


class ContributionNewTotalPerCountryResponse(BaseModel):
    contribution_new_total_per_country: List[ContributionNewPerCountryData]  # Same data structure, different metric
    period_info: Dict[str, Any]


class ContributionReturningPerCountryResponse(BaseModel):
    contribution_returning_per_country: List[ContributionNewPerCountryData]  # Same data structure
    period_info: Dict[str, Any]


class ContributionReturningTotalPerCountryResponse(BaseModel):
    contribution_returning_total_per_country: List[ContributionNewPerCountryData]  # Same data structure
    period_info: Dict[str, Any]


class TotalContributionPerCountryResponse(BaseModel):
    total_contribution_per_country: List[ContributionNewPerCountryData]  # Same data structure
    period_info: Dict[str, Any]


class BatchMetricsResponse(BaseModel):
    """Unified response containing all metrics calculated in a single batch."""
    periods: Dict[str, Any]
    metrics: Dict[str, Any]
    markets: List[Any]
    kpis: List[Any]
    contribution: List[Any]
    gender_sales: List[Any]
    men_category_sales: List[Any]
    women_category_sales: List[Any]
    category_sales: Dict[str, Any]
    products_new: Dict[str, Any]
    products_gender: Dict[str, Any]
    sessions_per_country: List[Any]
    conversion_per_country: List[Any]
    new_customers_per_country: List[Any]
    returning_customers_per_country: List[Any]
    aov_new_customers_per_country: List[Any]
    aov_returning_customers_per_country: List[Any]
    marketing_spend_per_country: List[Any]
    ncac_per_country: List[Any]
    contribution_new_per_country: List[Any]
    contribution_new_total_per_country: List[Any]
    contribution_returning_per_country: List[Any]
    contribution_returning_total_per_country: List[Any]
    total_contribution_per_country: List[Any]


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


@app.get("/api/contribution", response_model=ContributionResponse)
async def get_contribution(
    base_week: str = Query(..., description="Base ISO week like '2025-42'"),
    num_weeks: int = Query(8, description="Number of weeks to analyze")
):
    """Get Contribution metrics for the last N weeks."""
    
    try:
        if not validate_iso_week(base_week):
            raise HTTPException(status_code=400, detail=f"Invalid ISO week format: {base_week}")
        
        if num_weeks < 1 or num_weeks > 52:
            raise HTTPException(status_code=400, detail=f"Number of weeks must be between 1 and 52")
        
        config = load_config(week=base_week)
        contribution_data = calculate_contribution_for_weeks(base_week, num_weeks, config.data_root)
        
        response = ContributionResponse(**contribution_data)
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        logger.error(f"Error getting Contribution metrics for {base_week}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/gender-sales", response_model=GenderSalesResponse)
async def get_gender_sales(
    base_week: str = Query(..., description="Base ISO week like '2025-42'"),
    num_weeks: int = Query(8, description="Number of weeks to analyze")
):
    """Get Gender Sales metrics for the last N weeks."""
    
    try:
        if not validate_iso_week(base_week):
            raise HTTPException(status_code=400, detail=f"Invalid ISO week format: {base_week}")
        
        if num_weeks < 1 or num_weeks > 52:
            raise HTTPException(status_code=400, detail=f"Number of weeks must be between 1 and 52")
        
        config = load_config(week=base_week)
        data_path = config.data_root / "raw" / base_week
        gender_sales_data = calculate_gender_sales_for_weeks(base_week, num_weeks, data_path)
        
        # Format response
        response = GenderSalesResponse(
            gender_sales=gender_sales_data,
            period_info={
                "latest_week": base_week,
                "latest_dates": "N/A"  # Could add date range if needed
            }
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        logger.error(f"Error getting Gender Sales metrics for {base_week}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/men-category-sales", response_model=MenCategorySalesResponse)
async def get_men_category_sales(
    base_week: str = Query(..., description="Base ISO week like '2025-42'"),
    num_weeks: int = Query(8, description="Number of weeks to analyze")
):
    """Get Men Category Sales metrics for the last N weeks."""
    
    try:
        if not validate_iso_week(base_week):
            raise HTTPException(status_code=400, detail=f"Invalid ISO week format: {base_week}")
        
        if num_weeks < 1 or num_weeks > 52:
            raise HTTPException(status_code=400, detail=f"Number of weeks must be between 1 and 52")
        
        config = load_config(week=base_week)
        data_path = config.data_root / "raw" / base_week
        men_category_sales_data = calculate_men_category_sales_for_weeks(base_week, num_weeks, data_path)
        
        # Format response
        response = MenCategorySalesResponse(
            men_category_sales=men_category_sales_data,
            period_info={
                "latest_week": base_week,
                "latest_dates": "N/A"  # Could add date range if needed
            }
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        logger.error(f"Error getting Men Category Sales metrics for {base_week}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/women-category-sales", response_model=WomenCategorySalesResponse)
async def get_women_category_sales(
    base_week: str = Query(..., description="Base ISO week like '2025-42'"),
    num_weeks: int = Query(8, description="Number of weeks to analyze")
):
    """Get Women Category Sales metrics for the last N weeks."""
    
    try:
        if not validate_iso_week(base_week):
            raise HTTPException(status_code=400, detail=f"Invalid ISO week format: {base_week}")
        
        if num_weeks < 1 or num_weeks > 52:
            raise HTTPException(status_code=400, detail=f"Number of weeks must be between 1 and 52")
        
        config = load_config(week=base_week)
        data_path = config.data_root / "raw" / base_week
        women_category_sales_data = calculate_women_category_sales_for_weeks(base_week, num_weeks, data_path)
        
        # Format response
        response = WomenCategorySalesResponse(
            women_category_sales=women_category_sales_data,
            period_info={
                "latest_week": base_week,
                "latest_dates": "N/A"  # Could add date range if needed
            }
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        logger.error(f"Error getting Women Category Sales metrics for {base_week}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/category-sales", response_model=CategorySalesResponse)
async def get_category_sales(
    base_week: str = Query(..., description="Base ISO week like '2025-42'"),
    num_weeks: int = Query(8, description="Number of weeks to analyze")
):
    """Get Category Sales metrics for the last N weeks."""
    
    try:
        if not validate_iso_week(base_week):
            raise HTTPException(status_code=400, detail=f"Invalid ISO week format: {base_week}")
        
        if num_weeks < 1 or num_weeks > 52:
            raise HTTPException(status_code=400, detail=f"Number of weeks must be between 1 and 52")
        
        config = load_config(week=base_week)
        # Pass the week-specific data path
        data_path = config.data_root / "raw" / base_week
        category_sales_data = calculate_category_sales_for_weeks(base_week, num_weeks, data_path)
        
        # Format response
        response = CategorySalesResponse(
            category_sales=category_sales_data,
            period_info={
                "latest_week": base_week,
                "latest_dates": "N/A"  # Could add date range if needed
            }
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        logger.error(f"Error getting Category Sales metrics for {base_week}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/top-products", response_model=TopProductsResponse)
async def get_top_products(
    base_week: str = Query(..., description="Base ISO week like '2025-42'"),
    num_weeks: int = Query(1, description="Number of weeks to analyze"),
    top_n: int = Query(20, description="Number of top products to return"),
    customer_type: str = Query('new', description="Customer type: 'new' or 'returning'")
):
    """Get Top Products metrics for the last N weeks."""
    
    try:
        if not validate_iso_week(base_week):
            raise HTTPException(status_code=400, detail=f"Invalid ISO week format: {base_week}")
        
        if num_weeks < 1 or num_weeks > 52:
            raise HTTPException(status_code=400, detail=f"Number of weeks must be between 1 and 52")
        
        if top_n < 1 or top_n > 100:
            raise HTTPException(status_code=400, detail=f"Number of top products must be between 1 and 100")
        
        if customer_type not in ['new', 'returning']:
            raise HTTPException(status_code=400, detail=f"Customer type must be 'new' or 'returning'")
        
        config = load_config(week=base_week)
        data_path = config.data_root / "raw" / base_week
        top_products_data = calculate_top_products_for_weeks(base_week, num_weeks, data_path, top_n, customer_type)
        
        # Format response
        response = TopProductsResponse(
            top_products=top_products_data,
            period_info={
                "latest_week": base_week,
                "latest_dates": "N/A"  # Could add date range if needed
            }
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        logger.error(f"Error getting Top Products metrics for {base_week}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/top-products-gender", response_model=TopProductsResponse)
async def get_top_products_by_gender(
    base_week: str = Query(..., description="Base ISO week like '2025-42'"),
    num_weeks: int = Query(1, description="Number of weeks to analyze"),
    top_n: int = Query(20, description="Number of top products to return"),
    gender_filter: str = Query('men', description="Gender filter: 'men' or 'women'")
):
    """Get Top Products by Gender metrics for the last N weeks."""
    
    try:
        if not validate_iso_week(base_week):
            raise HTTPException(status_code=400, detail=f"Invalid ISO week format: {base_week}")
        
        if num_weeks < 1 or num_weeks > 52:
            raise HTTPException(status_code=400, detail=f"Number of weeks must be between 1 and 52")
        
        if top_n < 1 or top_n > 100:
            raise HTTPException(status_code=400, detail=f"Number of top products must be between 1 and 100")
        
        if gender_filter not in ['men', 'women']:
            raise HTTPException(status_code=400, detail=f"Gender filter must be 'men' or 'women'")
        
        config = load_config(week=base_week)
        data_path = config.data_root / "raw" / base_week
        top_products_data = calculate_top_products_by_gender_for_weeks(base_week, num_weeks, data_path, gender_filter, top_n)
        
        # Format response
        response = TopProductsResponse(
            top_products=top_products_data,
            period_info={
                "latest_week": base_week,
                "latest_dates": "N/A"  # Could add date range if needed
            }
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        logger.error(f"Error getting Top Products by Gender metrics for {base_week}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/sessions-per-country", response_model=SessionsPerCountryResponse)
async def get_sessions_per_country(
    base_week: str = Query(..., description="Base ISO week like '2025-42'"),
    num_weeks: int = Query(8, description="Number of weeks to analyze")
):
    """Get Sessions per Country metrics for the last N weeks."""
    
    try:
        if not validate_iso_week(base_week):
            raise HTTPException(status_code=400, detail=f"Invalid ISO week format: {base_week}")
        
        if num_weeks < 1 or num_weeks > 52:
            raise HTTPException(status_code=400, detail=f"Number of weeks must be between 1 and 52")
        
        config = load_config(week=base_week)
        data_path = config.data_root / "raw" / base_week
        sessions_data = calculate_sessions_per_country_for_weeks(base_week, num_weeks, data_path)
        
        # Format response
        response = SessionsPerCountryResponse(
            sessions_per_country=sessions_data,
            period_info={
                "latest_week": base_week,
                "latest_dates": "N/A"  # Could add date range if needed
            }
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        logger.error(f"Error getting Sessions per Country metrics for {base_week}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/conversion-per-country", response_model=ConversionPerCountryResponse)
async def get_conversion_per_country(
    base_week: str = Query(..., description="Base ISO week like '2025-42'"),
    num_weeks: int = Query(8, description="Number of weeks to analyze")
):
    """Get Conversion per Country metrics for the last N weeks."""
    
    try:
        if not validate_iso_week(base_week):
            raise HTTPException(status_code=400, detail=f"Invalid ISO week format: {base_week}")
        
        if num_weeks < 1 or num_weeks > 52:
            raise HTTPException(status_code=400, detail=f"Number of weeks must be between 1 and 52")
        
        config = load_config(week=base_week)
        data_path = config.data_root / "raw" / base_week
        conversion_data = calculate_conversion_per_country_for_weeks(base_week, num_weeks, data_path)
        
        # Format response
        response = ConversionPerCountryResponse(
            conversion_per_country=conversion_data,
            period_info={
                "latest_week": base_week,
                "latest_dates": "N/A"
            }
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        logger.error(f"Error getting Conversion per Country metrics for {base_week}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/new-customers-per-country", response_model=NewCustomersPerCountryResponse)
async def get_new_customers_per_country(
    base_week: str = Query(..., description="Base ISO week like '2025-42'"),
    num_weeks: int = Query(8, description="Number of weeks to analyze")
):
    """Get New Customers per Country metrics for the last N weeks."""
    
    try:
        if not validate_iso_week(base_week):
            raise HTTPException(status_code=400, detail=f"Invalid ISO week format: {base_week}")
        
        if num_weeks < 1 or num_weeks > 52:
            raise HTTPException(status_code=400, detail=f"Number of weeks must be between 1 and 52")
        
        config = load_config(week=base_week)
        data_path = config.data_root / "raw" / base_week
        new_customers_data = calculate_new_customers_per_country_for_weeks(base_week, num_weeks, data_path)
        
        # Format response
        response = NewCustomersPerCountryResponse(
            new_customers_per_country=new_customers_data,
            period_info={
                "latest_week": base_week,
                "latest_dates": "N/A"
            }
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        logger.error(f"Error getting New Customers per Country metrics for {base_week}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/returning-customers-per-country", response_model=ReturningCustomersPerCountryResponse)
async def get_returning_customers_per_country(
    base_week: str = Query(..., description="Base ISO week like '2025-42'"),
    num_weeks: int = Query(8, description="Number of weeks to analyze")
):
    """Get Returning Customers per Country metrics for the last N weeks."""
    
    try:
        if not validate_iso_week(base_week):
            raise HTTPException(status_code=400, detail=f"Invalid ISO week format: {base_week}")
        
        if num_weeks < 1 or num_weeks > 52:
            raise HTTPException(status_code=400, detail=f"Number of weeks must be between 1 and 52")
        
        config = load_config(week=base_week)
        data_path = config.data_root / "raw" / base_week
        returning_customers_data = calculate_returning_customers_per_country_for_weeks(base_week, num_weeks, data_path)
        
        # Format response
        response = ReturningCustomersPerCountryResponse(
            returning_customers_per_country=returning_customers_data,
            period_info={
                "latest_week": base_week,
                "latest_dates": "N/A"
            }
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        logger.error(f"Error getting Returning Customers per Country metrics for {base_week}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/aov-new-customers-per-country", response_model=AOVNewCustomersPerCountryResponse)
async def get_aov_new_customers_per_country(
    base_week: str = Query(..., description="Base ISO week like '2025-42'"),
    num_weeks: int = Query(8, description="Number of weeks to analyze")
):
    """Get AOV for New Customers per Country metrics for the last N weeks."""
    
    try:
        if not validate_iso_week(base_week):
            raise HTTPException(status_code=400, detail=f"Invalid ISO week format: {base_week}")
        
        if num_weeks < 1 or num_weeks > 52:
            raise HTTPException(status_code=400, detail=f"Number of weeks must be between 1 and 52")
        
        config = load_config(week=base_week)
        data_path = config.data_root / "raw" / base_week
        aov_data = calculate_aov_new_customers_per_country_for_weeks(base_week, num_weeks, data_path)
        
        # Format response
        response = AOVNewCustomersPerCountryResponse(
            aov_new_customers_per_country=aov_data,
            period_info={
                "latest_week": base_week,
                "latest_dates": "N/A"
            }
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        logger.error(f"Error getting AOV New Customers per Country metrics for {base_week}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/aov-returning-customers-per-country", response_model=AOVReturningCustomersPerCountryResponse)
async def get_aov_returning_customers_per_country(
    base_week: str = Query(..., description="Base ISO week like '2025-42'"),
    num_weeks: int = Query(8, description="Number of weeks to analyze")
):
    """Get AOV for Returning Customers per Country metrics for the last N weeks."""
    
    try:
        if not validate_iso_week(base_week):
            raise HTTPException(status_code=400, detail=f"Invalid ISO week format: {base_week}")
        
        if num_weeks < 1 or num_weeks > 52:
            raise HTTPException(status_code=400, detail=f"Number of weeks must be between 1 and 52")
        
        config = load_config(week=base_week)
        data_path = config.data_root / "raw" / base_week
        aov_data = calculate_aov_returning_customers_per_country_for_weeks(base_week, num_weeks, data_path)
        
        # Format response
        response = AOVReturningCustomersPerCountryResponse(
            aov_returning_customers_per_country=aov_data,
            period_info={
                "latest_week": base_week,
                "latest_dates": "N/A"
            }
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        logger.error(f"Error getting AOV Returning Customers per Country metrics for {base_week}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/marketing-spend-per-country", response_model=MarketingSpendPerCountryResponse)
async def get_marketing_spend_per_country(
    base_week: str = Query(..., description="Base ISO week like '2025-42'"),
    num_weeks: int = Query(8, description="Number of weeks to analyze")
):
    """Get Marketing Spend per Country metrics for the last N weeks."""
    
    try:
        if not validate_iso_week(base_week):
            raise HTTPException(status_code=400, detail=f"Invalid ISO week format: {base_week}")
        
        if num_weeks < 1 or num_weeks > 52:
            raise HTTPException(status_code=400, detail=f"Number of weeks must be between 1 and 52")
        
        config = load_config(week=base_week)
        data_path = config.data_root / "raw" / base_week
        spend_data = calculate_marketing_spend_per_country_for_weeks(base_week, num_weeks, data_path)
        
        # Format response
        response = MarketingSpendPerCountryResponse(
            marketing_spend_per_country=spend_data,
            period_info={
                "latest_week": base_week,
                "latest_dates": "N/A"
            }
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        logger.error(f"Error getting Marketing Spend per Country metrics for {base_week}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/ncac-per-country", response_model=nCACPerCountryResponse)
async def get_ncac_per_country(
    base_week: str = Query(..., description="Base ISO week like '2025-42'"),
    num_weeks: int = Query(8, description="Number of weeks to analyze")
):
    """Get nCAC per country metrics for the last N weeks."""
    
    try:
        if not validate_iso_week(base_week):
            raise HTTPException(status_code=400, detail=f"Invalid ISO week format: {base_week}")
        
        if num_weeks < 1 or num_weeks > 52:
            raise HTTPException(status_code=400, detail=f"Number of weeks must be between 1 and 52")
        
        config = load_config(week=base_week)
        data_path = config.data_root / "raw" / base_week
        ncac_data = calculate_ncac_per_country_for_weeks(base_week, num_weeks, data_path)
        
        # Format response
        response = nCACPerCountryResponse(
            ncac_per_country=ncac_data,
            period_info={
                "latest_week": base_week,
                "latest_dates": "N/A"
            }
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        logger.error(f"Error getting nCAC per country metrics for {base_week}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/contribution-new-per-country", response_model=ContributionNewPerCountryResponse)
async def get_contribution_new_per_country(
    base_week: str = Query(..., description="Base ISO week like '2025-42'"),
    num_weeks: int = Query(8, description="Number of weeks to analyze")
):
    """Get Contribution per New Customer per Country metrics for the last N weeks."""
    
    try:
        if not validate_iso_week(base_week):
            raise HTTPException(status_code=400, detail=f"Invalid ISO week format: {base_week}")
        
        if num_weeks < 1 or num_weeks > 52:
            raise HTTPException(status_code=400, detail=f"Number of weeks must be between 1 and 52")
        
        config = load_config(week=base_week)
        data_path = config.data_root / "raw" / base_week
        contribution_data = calculate_contribution_new_per_country_for_weeks(base_week, num_weeks, data_path)
        
        # Format response
        response = ContributionNewPerCountryResponse(
            contribution_new_per_country=contribution_data,
            period_info={
                "latest_week": base_week,
                "latest_dates": "N/A"
            }
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        logger.error(f"Error getting Contribution per New Customer per Country metrics for {base_week}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/contribution-new-total-per-country")
async def get_contribution_new_total_per_country(
    base_week: str = Query(..., description="Base ISO week like '2025-42'"),
    num_weeks: int = Query(8, description="Number of weeks to analyze")
):
    """Get Total Contribution per Country for new customers for the last N weeks."""
    
    try:
        if not validate_iso_week(base_week):
            raise HTTPException(status_code=400, detail=f"Invalid ISO week format: {base_week}")
        
        if num_weeks < 1 or num_weeks > 52:
            raise HTTPException(status_code=400, detail=f"Number of weeks must be between 1 and 52")
        
        config = load_config(week=base_week)
        data_path = config.data_root / "raw" / base_week
        contribution_data = calculate_contribution_new_total_per_country_for_weeks(base_week, num_weeks, data_path)
        
        # Format response
        response = ContributionNewTotalPerCountryResponse(
            contribution_new_total_per_country=contribution_data,
            period_info={
                "latest_week": base_week,
                "latest_dates": "N/A"
            }
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        logger.error(f"Error getting Total Contribution per Country metrics for {base_week}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/contribution-returning-per-country")
async def get_contribution_returning_per_country(
    base_week: str = Query(..., description="Base ISO week like '2025-42'"),
    num_weeks: int = Query(8, description="Number of weeks to analyze")
):
    """Get Contribution per Returning Customer per Country metrics for the last N weeks."""
    
    try:
        if not validate_iso_week(base_week):
            raise HTTPException(status_code=400, detail=f"Invalid ISO week format: {base_week}")
        
        if num_weeks < 1 or num_weeks > 52:
            raise HTTPException(status_code=400, detail=f"Number of weeks must be between 1 and 52")
        
        config = load_config(week=base_week)
        data_path = config.data_root / "raw" / base_week
        contribution_data = calculate_contribution_returning_per_country_for_weeks(base_week, num_weeks, data_path)
        
        # Format response
        response = ContributionReturningPerCountryResponse(
            contribution_returning_per_country=contribution_data,
            period_info={
                "latest_week": base_week,
                "latest_dates": "N/A"
            }
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        logger.error(f"Error getting Contribution per Returning Customer per Country metrics for {base_week}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/contribution-returning-total-per-country")
async def get_contribution_returning_total_per_country(
    base_week: str = Query(..., description="Base ISO week like '2025-42'"),
    num_weeks: int = Query(8, description="Number of weeks to analyze")
):
    """Get Total Contribution per Country for returning customers for the last N weeks."""
    
    try:
        if not validate_iso_week(base_week):
            raise HTTPException(status_code=400, detail=f"Invalid ISO week format: {base_week}")
        
        if num_weeks < 1 or num_weeks > 52:
            raise HTTPException(status_code=400, detail=f"Number of weeks must be between 1 and 52")
        
        config = load_config(week=base_week)
        data_path = config.data_root / "raw" / base_week
        contribution_data = calculate_contribution_returning_total_per_country_for_weeks(base_week, num_weeks, data_path)
        
        # Format response
        response = ContributionReturningTotalPerCountryResponse(
            contribution_returning_total_per_country=contribution_data,
            period_info={
                "latest_week": base_week,
                "latest_dates": "N/A"
            }
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        logger.error(f"Error getting Total Contribution per Country for returning customers for {base_week}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/total-contribution-per-country")
async def get_total_contribution_per_country(
    base_week: str = Query(..., description="Base ISO week like '2025-42'"),
    num_weeks: int = Query(8, description="Number of weeks to analyze")
):
    """Get Total Contribution per Country for all customers for the last N weeks."""
    
    try:
        if not validate_iso_week(base_week):
            raise HTTPException(status_code=400, detail=f"Invalid ISO week format: {base_week}")
        
        if num_weeks < 1 or num_weeks > 52:
            raise HTTPException(status_code=400, detail=f"Number of weeks must be between 1 and 52")
        
        config = load_config(week=base_week)
        data_path = config.data_root / "raw" / base_week
        contribution_data = calculate_total_contribution_per_country_for_weeks(base_week, num_weeks, data_path)
        
        # Format response
        response = TotalContributionPerCountryResponse(
            total_contribution_per_country=contribution_data,
            period_info={
                "latest_week": base_week,
                "latest_dates": "N/A"
            }
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        logger.error(f"Error getting Total Contribution per Country for {base_week}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/batch/all-metrics")
async def get_batch_all_metrics(
    base_week: str = Query(..., description="Base ISO week like '2025-42'"),
    num_weeks: int = Query(8, description="Number of weeks to analyze")
):
    """Get all metrics in a single batch request for optimal performance."""
    
    try:
        if not validate_iso_week(base_week):
            raise HTTPException(status_code=400, detail=f"Invalid ISO week format: {base_week}")
        
        if num_weeks < 1 or num_weeks > 52:
            raise HTTPException(status_code=400, detail=f"Number of weeks must be between 1 and 52")
        
        config = load_config(week=base_week)
        
        logger.info(f"Starting batch calculation for {base_week} with {num_weeks} weeks")
        all_metrics = calculate_all_metrics(base_week, config.data_root, num_weeks)
        
        response = BatchMetricsResponse(**all_metrics)
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        logger.error(f"Error getting batch all metrics for {base_week}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    week: str = Form(...),
    file_type: str = Form(..., description="qlik, dema_spend, dema_gm2, or shopify")
):
    """
    Upload data file for specific week and type.
    Validates file type, extracts date range, saves to correct location.
    """
    try:
        # Validate week format
        if not validate_iso_week(week):
            raise HTTPException(status_code=400, detail="Invalid ISO week format")
        
        # Validate file_type
        allowed_types = ["qlik", "dema_spend", "dema_gm2", "shopify", "budget"]
        if file_type not in allowed_types:
            raise HTTPException(status_code=400, detail=f"Invalid file type. Must be one of {allowed_types}")
        
        # Validate file extension
        file_extension = Path(file.filename).suffix.lower()
        if file_type == "qlik" and file_extension not in ['.xlsx', '.csv']:
            raise HTTPException(status_code=400, detail="Qlik file must be .xlsx or .csv")
        if file_type in ["dema_spend", "dema_gm2", "shopify", "budget"] and file_extension != '.csv':
            raise HTTPException(status_code=400, detail=f"{file_type} file must be .csv")
        
        # Create target directory
        config = load_config(week=week)
        target_dir = config.raw_data_path / file_type
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Delete existing files in the directory (except .DS_Store)
        for existing_file in target_dir.glob("*.*"):
            if not existing_file.name.startswith('.'):
                existing_file.unlink()
                logger.info(f"Deleted old file: {existing_file}")
        
        # Save file
        target_path = target_dir / file.filename
        with target_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"File uploaded: {target_path}")
        
        # Clear caches to ensure fresh data after upload
        raw_data_cache.clear()
        logger.info("Cleared raw data cache after file upload")
        
        # Extract metadata (date range)
        metadata = extract_file_metadata(target_path, file_type)
        
        return {
            "success": True,
            "file_path": str(target_path),
            "metadata": metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


def validate_file_dimensions(file_path: Path, file_type: str) -> Dict[str, Any]:
    """Validate that required columns/dimensions exist in the file."""
    
    result = {
        "has_country": False,
        "columns": []
    }
    
    if not file_path.exists():
        return result
    
    try:
        if file_type in ["dema_spend", "dema_gm2"]:
            # Try semicolon first, then comma
            try:
                df = pd.read_csv(file_path, sep=';', encoding='utf-8', nrows=1, quotechar='"')
            except:
                df = pd.read_csv(file_path, sep=',', encoding='utf-8', nrows=1, quotechar='"')
            
            # Strip whitespace and quotes from column names
            df.columns = df.columns.str.strip().str.replace('"', '')
            result["columns"] = df.columns.tolist()
            
            # Check for country dimension (case insensitive)
            result["has_country"] = any("country" in col.lower() for col in df.columns)
        
        elif file_type == "shopify":
            # Try to load the file
            try:
                df = pd.read_csv(file_path, sep=';', encoding='utf-8', nrows=1, quotechar='"')
            except:
                df = pd.read_csv(file_path, sep=',', encoding='utf-8', nrows=1, quotechar='"')
            
            df.columns = df.columns.str.strip().str.replace('"', '')
            result["columns"] = df.columns.tolist()
            result["has_country"] = any("country" in col.lower() for col in df.columns)
        
        elif file_type == "qlik":
            # For Qlik, check if it's CSV or Excel
            if file_path.suffix == '.csv':
                try:
                    df = pd.read_csv(file_path, sep=';', encoding='utf-8', nrows=1, quotechar='"')
                except:
                    df = pd.read_csv(file_path, sep=',', encoding='utf-8', nrows=1, quotechar='"')
                df.columns = df.columns.str.strip().str.replace('"', '')
            else:
                df = pd.read_excel(file_path, nrows=1)
            
            result["columns"] = df.columns.tolist()
            result["has_country"] = any("country" in col.lower() for col in df.columns)
        
        elif file_type == "budget":
            # Budget files don't need country dimension - they use Market instead
            try:
                df = pd.read_csv(file_path, sep=',', encoding='utf-8', nrows=1, quotechar='"')
            except:
                try:
                    df = pd.read_csv(file_path, sep=';', encoding='utf-8', nrows=1, quotechar='"')
                except:
                    df = pd.DataFrame()
            
            df.columns = df.columns.str.strip().str.replace('"', '')
            result["columns"] = df.columns.tolist()
            # Check for Market dimension instead of Country
            result["has_country"] = any("market" in col.lower() for col in df.columns)
    
    except Exception as e:
        logger.error(f"Error validating dimensions for {file_path}: {e}")
    
    return result


@app.get("/api/file-dimensions")
async def get_file_dimensions(week: str = Query(...)):
    """Get validation status for required dimensions in data files."""
    try:
        if not validate_iso_week(week):
            raise HTTPException(status_code=400, detail="Invalid ISO week format")
        
        config = load_config(week=week)
        raw_path = config.raw_data_path
        
        result = {}
        
        # Check each file type
        for file_type in ["qlik", "dema_spend", "dema_gm2", "shopify", "budget"]:
            type_path = raw_path / file_type
            if type_path.exists():
                files = list(type_path.glob("*.*"))
                # Filter out hidden files
                files = [f for f in files if not f.name.startswith('.')]
                
                if files:
                    # Get the most recently modified file
                    latest_file = max(files, key=lambda f: f.stat().st_mtime)
                    validation = validate_file_dimensions(latest_file, file_type)
                    
                    result[file_type] = {
                        "filename": latest_file.name,
                        "has_country": validation["has_country"],
                        "columns": validation["columns"]
                    }
                else:
                    result[file_type] = {
                        "filename": None,
                        "has_country": None,
                        "columns": []
                    }
            else:
                result[file_type] = {
                    "filename": None,
                    "has_country": None,
                    "columns": []
                }
        
        return result
        
    except Exception as e:
        logger.error(f"Error validating file dimensions: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate file dimensions")


@app.get("/api/file-metadata")
async def get_file_metadata(week: str = Query(...)):
    """Get metadata for all data files in a specific week - only check if files exist."""
    try:
        if not validate_iso_week(week):
            raise HTTPException(status_code=400, detail="Invalid ISO week format")
        
        config = load_config(week=week)
        raw_path = config.raw_data_path
        
        metadata = {}
        for file_type in ["qlik", "dema_spend", "dema_gm2", "shopify"]:
            type_path = raw_path / file_type
            if type_path.exists():
                files = list(type_path.glob("*.*"))
                # Filter out hidden files (.DS_Store, etc.)
                files = [f for f in files if not f.name.startswith('.')]
                if files:
                    # Get the most recently modified file
                    latest_file = max(files, key=lambda f: f.stat().st_mtime)
                    # Only return basic file info - don't read the entire file
                    metadata[file_type] = {
                        "filename": latest_file.name,
                        "uploaded_at": datetime.fromtimestamp(latest_file.stat().st_mtime).isoformat()
                    }
        
        return metadata
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file metadata: {e}")
        raise HTTPException(status_code=500, detail="Failed to get file metadata")


@app.get("/api/budget-data")
async def get_budget_data(week: str = Query(...)):
    """Get budget data for a specific week."""
    try:
        if not validate_iso_week(week):
            raise HTTPException(status_code=400, detail="Invalid ISO week format")
        
        config = load_config(week=week)
        budget_path = config.raw_data_path / "budget"
        
        if not budget_path.exists():
            return {"error": "No budget data available for this week"}
        
        # Load budget data
        from weekly_report.src.adapters.budget import load_data
        budget_df = load_data(config.raw_data_path)
        
        if budget_df.empty:
            return {"error": "Budget file is empty"}
        
        # Convert sample data to dict, handling NaN and infinite values
        sample_dicts = []
        for _, row in budget_df.head(5).iterrows():
            row_dict = {}
                for col, val in row.items():
                # Check for NaN
                if pd.isna(val):
                    row_dict[col] = None
                # Check for infinite values using math
                elif isinstance(val, float) and (val == float('inf') or val == float('-inf')):
                    row_dict[col] = None
                else:
                    row_dict[col] = str(val) if isinstance(val, (int, float)) else val
            sample_dicts.append(row_dict)
        
        # Return basic structure
        return {
            "week": week,
            "columns": budget_df.columns.tolist(),
            "row_count": len(budget_df),
            "sample_data": sample_dicts
        }
        
    except FileNotFoundError:
        return {"error": "No budget data found"}
    except Exception as e:
        logger.error(f"Error loading budget data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load budget data: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
