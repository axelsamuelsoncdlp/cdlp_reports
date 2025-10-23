"""
Calculate Contribution metrics for new and returning customers.
"""
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd
from loguru import logger

from weekly_report.src.metrics.table1 import load_all_raw_data
from weekly_report.src.periods.calculator import get_week_date_range


def calculate_contribution_for_weeks(base_week: str, num_weeks: int, data_root: Path) -> Dict[str, Any]:
    """
    Calculate Contribution metrics for the last N weeks.
    
    Returns:
        Dict with 'contributions' (list of contribution data) and 'period_info' (metadata)
    """
    # Generate weeks to analyze (same logic as online_kpis.py)
    weeks_to_analyze = []
    last_year_weeks = []
    
    year, week_num = map(int, base_week.split('-'))
    
    # Generate current year weeks
    for i in range(num_weeks):
        week = week_num - num_weeks + 1 + i
        if week <= 0:
            prev_year = year - 1
            days_in_prev_year = pd.Timestamp(f"{prev_year}-12-31").timetuple().tm_yday
            weeks_in_prev_year = pd.Timestamp(f"{prev_year}-12-31").isocalendar()[1]
            week = weeks_in_prev_year + week
            year_str = f"{prev_year}-{week:02d}"
        else:
            year_str = f"{year}-{week:02d}"
        weeks_to_analyze.append(year_str)
    
    # Generate last year weeks
    for i in range(num_weeks):
        week = week_num - num_weeks + 1 + i
        if week <= 0:
            prev_year = year - 2
            days_in_prev_year = pd.Timestamp(f"{prev_year}-12-31").timetuple().tm_yday
            weeks_in_prev_year = pd.Timestamp(f"{prev_year}-12-31").isocalendar()[1]
            week = weeks_in_prev_year + week
            year_str = f"{prev_year}-{week:02d}"
        else:
            year_str = f"{year-1}-{week:02d}"
        last_year_weeks.append(year_str)
    
    logger.info(f"Calculating Contribution metrics for weeks: {weeks_to_analyze}")
    
    # Load data
    latest_data_path = data_root / "raw" / base_week
    qlik_df = pd.DataFrame()
    dema_df = pd.DataFrame()
    dema_gm2_df = pd.DataFrame()
    
    if latest_data_path.exists():
        try:
            all_raw_data = load_all_raw_data(latest_data_path)
            qlik_df = all_raw_data.get('qlik', pd.DataFrame())
            dema_df = all_raw_data.get('dema_spend', pd.DataFrame())
            dema_gm2_df = all_raw_data.get('dema_gm2', pd.DataFrame())
            
            # Pre-compute ISO week columns
            if not qlik_df.empty and 'Date' in qlik_df.columns:
                qlik_df['Date'] = pd.to_datetime(qlik_df['Date'], errors='coerce')
                iso_cal = qlik_df['Date'].dt.isocalendar()
                qlik_df['iso_week'] = iso_cal['year'].astype(str) + '-' + iso_cal['week'].astype(str).str.zfill(2)
            
            if not dema_df.empty and 'Days' in dema_df.columns:
                dema_df['Days'] = pd.to_datetime(dema_df['Days'], errors='coerce')
                iso_cal = dema_df['Days'].dt.isocalendar()
                dema_df['iso_week'] = iso_cal['year'].astype(str) + '-' + iso_cal['week'].astype(str).str.zfill(2)
            
            if not dema_gm2_df.empty and 'Days' in dema_gm2_df.columns:
                dema_gm2_df['Days'] = pd.to_datetime(dema_gm2_df['Days'], errors='coerce')
                iso_cal = dema_gm2_df['Days'].dt.isocalendar()
                dema_gm2_df['iso_week'] = iso_cal['year'].astype(str) + '-' + iso_cal['week'].astype(str).str.zfill(2)
                
        except Exception as e:
            logger.warning(f"Failed to load data for week {base_week}: {e}")
    
    # Calculate contributions for each week
    contributions_list = []
    
    for week_idx, week_str in enumerate(weeks_to_analyze):
        # Filter data for this week
        week_qlik_df = qlik_df[qlik_df['iso_week'] == week_str].copy() if not qlik_df.empty and 'iso_week' in qlik_df.columns else pd.DataFrame()
        week_dema_df = dema_df[dema_df['iso_week'] == week_str].copy() if not dema_df.empty and 'iso_week' in dema_df.columns else pd.DataFrame()
        week_dema_gm2_df = dema_gm2_df[dema_gm2_df['iso_week'] == week_str].copy() if not dema_gm2_df.empty and 'iso_week' in dema_gm2_df.columns else pd.DataFrame()
        
        if week_qlik_df.empty:
            logger.warning(f"Missing data for week {week_str}")
            continue
        
        # Calculate contribution metrics
        week_contributions = calculate_week_contributions(week_qlik_df, week_dema_df, week_dema_gm2_df, week_str)
        
        # Add last year comparison
        last_year_week = last_year_weeks[week_idx]
        last_year_qlik_df = qlik_df[qlik_df['iso_week'] == last_year_week].copy() if not qlik_df.empty and 'iso_week' in qlik_df.columns else pd.DataFrame()
        last_year_dema_df = dema_df[dema_df['iso_week'] == last_year_week].copy() if not dema_df.empty and 'iso_week' in dema_df.columns else pd.DataFrame()
        last_year_dema_gm2_df = dema_gm2_df[dema_gm2_df['iso_week'] == last_year_week].copy() if not dema_gm2_df.empty and 'iso_week' in dema_gm2_df.columns else pd.DataFrame()
        
        if not last_year_qlik_df.empty:
            last_year_contributions = calculate_week_contributions(
                last_year_qlik_df,
                last_year_dema_df,
                last_year_dema_gm2_df,
                last_year_week
            )
            week_contributions['last_year'] = last_year_contributions
        
        contributions_list.append(week_contributions)
    
    # Get latest week date range
    latest_week = weeks_to_analyze[-1]
    date_range = get_week_date_range(latest_week)
    
    return {
        'contributions': contributions_list,
        'period_info': {
            'latest_week': latest_week,
            'latest_dates': date_range
        }
    }


def calculate_week_contributions(qlik_df: pd.DataFrame, dema_df: pd.DataFrame, dema_gm2_df: pd.DataFrame, week_str: str) -> Dict[str, Any]:
    """Calculate contribution metrics for a single week."""
    
    # Filter for online sales only
    online_df = qlik_df[qlik_df['Sales Channel'] == 'Online']
    
    # Gross Revenue by customer type
    new_customer_df = online_df[online_df['New/Returning Customer'] == 'New']
    returning_customer_df = online_df[online_df['New/Returning Customer'] == 'Returning']
    
    gross_revenue_new = new_customer_df['Gross Revenue'].sum()
    gross_revenue_returning = returning_customer_df['Gross Revenue'].sum()
    gross_revenue_total = online_df['Gross Revenue'].sum()
    
    # Get GM2 from dema_gm2 data - check if we have split by customer type
    gm2_new = 0
    gm2_returning = 0
    gm2_total = 0
    
    if not dema_gm2_df.empty:
        # Check if we have customer type split
        if 'New vs Returning Customer' in dema_gm2_df.columns:
            # New format with customer type split
            new_rows = dema_gm2_df[dema_gm2_df['New vs Returning Customer'] == 'New']
            returning_rows = dema_gm2_df[dema_gm2_df['New vs Returning Customer'] == 'Returning']
            
            logger.info(f"Week {week_str}: Found {len(new_rows)} New rows and {len(returning_rows)} Returning rows in GM2 data")
            
            gm2_new = new_rows['Gross margin 2 - Dema MTA'].sum() if 'Gross margin 2 - Dema MTA' in new_rows.columns else 0
            gm2_returning = returning_rows['Gross margin 2 - Dema MTA'].sum() if 'Gross margin 2 - Dema MTA' in returning_rows.columns else 0
            
            logger.info(f"Week {week_str}: GM2 New={gm2_new:.2f}, GM2 Returning={gm2_returning:.2f}")
        else:
            # Old format - allocate proportionally based on gross revenue
            gm2_total = dema_gm2_df['Gross margin 2 - Dema MTA'].sum() if 'Gross margin 2 - Dema MTA' in dema_gm2_df.columns else 0
            gm2_new = (gm2_total * gross_revenue_new / gross_revenue_total) if gross_revenue_total > 0 else 0
            gm2_returning = (gm2_total * gross_revenue_returning / gross_revenue_total) if gross_revenue_total > 0 else 0
    
    gm2_total = gm2_new + gm2_returning
    
    # Get marketing spend
    marketing_spend = dema_df['Marketing spend'].sum() if not dema_df.empty and 'Marketing spend' in dema_df.columns else 0
    
    # Calculate GM3 (Contribution)
    # Marketing spend allocation: 70% new, 30% returning
    marketing_new = marketing_spend * 0.7
    marketing_returning = marketing_spend * 0.3
    
    contribution_new = gm2_new - marketing_new
    contribution_returning = gm2_returning - marketing_returning
    contribution_total = gm2_total - marketing_spend
    
    return {
        'week': week_str,
        'gross_revenue_new': float(gross_revenue_new),
        'gross_revenue_returning': float(gross_revenue_returning),
        'contribution_new': float(contribution_new),
        'contribution_returning': float(contribution_returning),
        'contribution_total': float(contribution_total)
    }

