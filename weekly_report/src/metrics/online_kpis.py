"""
Calculate Online KPIs for the last 8 weeks.
"""
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd
from loguru import logger

from weekly_report.src.metrics.table1 import load_all_raw_data
from weekly_report.src.periods.calculator import get_week_date_range


def get_iso_week_from_date(date_str: str) -> str:
    """Convert date string to ISO week format."""
    try:
        date = pd.to_datetime(date_str)
        year, week, _ = date.isocalendar()
        return f"{year}-{week:02d}"
    except Exception as e:
        logger.warning(f"Could not parse date {date_str}: {e}")
        return None


def filter_data_by_iso_week(df: pd.DataFrame, iso_week: str, date_column: str = 'Date') -> pd.DataFrame:
    """Filter dataframe by ISO week (iso_week column must already exist)."""
    if df.empty or 'iso_week' not in df.columns:
        return df
    
    filtered = df[df['iso_week'] == iso_week].copy()
    return filtered


def calculate_online_kpis_for_weeks(base_week: str, num_weeks: int, data_root: Path) -> Dict[str, Any]:
    """
    Calculate Online KPIs for the last N weeks.
    
    Returns:
        Dict with 'kpis' (list of KPI data) and 'period_info' (metadata)
    """
    # Generate weeks to analyze
    weeks_to_analyze = []
    last_year_weeks = []
    
    # Parse base week
    year, week_num = map(int, base_week.split('-'))
    
    # Generate current year weeks
    for i in range(num_weeks):
        week = week_num - num_weeks + 1 + i
        if week <= 0:
            # Adjust for previous year
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
            # Adjust for previous year
            prev_year = year - 2
            days_in_prev_year = pd.Timestamp(f"{prev_year}-12-31").timetuple().tm_yday
            weeks_in_prev_year = pd.Timestamp(f"{prev_year}-12-31").isocalendar()[1]
            week = weeks_in_prev_year + week
            year_str = f"{prev_year}-{week:02d}"
        else:
            year_str = f"{year-1}-{week:02d}"
        last_year_weeks.append(year_str)
    
    logger.info(f"Calculating Online KPIs for weeks: {weeks_to_analyze}")
    logger.info(f"Last year weeks: {last_year_weeks}")
    
    # Collect all weeks
    all_weeks = list(set(weeks_to_analyze + last_year_weeks))
    
    # Load data once from the raw directory using cached loader
    latest_data_path = data_root / "raw"  # Single directory, not week-specific
    qlik_df = pd.DataFrame()
    shopify_df = pd.DataFrame()
    dema_df = pd.DataFrame()
    
    if latest_data_path.exists():
        try:
            # Load all raw data using cached loader (loads once, caches in memory)
            logger.info(f"Loading raw data from {latest_data_path}")
            all_raw_data = load_all_raw_data(latest_data_path)
            
            qlik_df = all_raw_data.get('qlik', pd.DataFrame())
            dema_df = all_raw_data.get('dema_spend', pd.DataFrame())
            
            # Shopify data is loaded separately as it's not in load_all_raw_data
            from weekly_report.src.adapters.shopify import load_data as load_shopify_data
            shopify_df = load_shopify_data(latest_data_path)
            
            # Pre-compute ISO week column for all dataframes to avoid repeated computation
            if not qlik_df.empty and 'Date' in qlik_df.columns:
                qlik_df['Date'] = pd.to_datetime(qlik_df['Date'], errors='coerce')
                iso_cal = qlik_df['Date'].dt.isocalendar()
                qlik_df['iso_week'] = iso_cal['year'].astype(str) + '-' + iso_cal['week'].astype(str).str.zfill(2)
                logger.info(f"Pre-computed ISO weeks for Qlik data: {qlik_df.shape}")
            
            if not dema_df.empty and 'Days' in dema_df.columns:
                dema_df['Days'] = pd.to_datetime(dema_df['Days'], errors='coerce')
                iso_cal = dema_df['Days'].dt.isocalendar()
                dema_df['iso_week'] = iso_cal['year'].astype(str) + '-' + iso_cal['week'].astype(str).str.zfill(2)
                logger.info(f"Pre-computed ISO weeks for DEMA data: {dema_df.shape}")
            
            if not shopify_df.empty and 'Day' in shopify_df.columns:
                shopify_df['Day'] = pd.to_datetime(shopify_df['Day'], errors='coerce')
                iso_cal = shopify_df['Day'].dt.isocalendar()
                shopify_df['iso_week'] = iso_cal['year'].astype(str) + '-' + iso_cal['week'].astype(str).str.zfill(2)
                logger.info(f"Pre-computed ISO weeks for Shopify data: {shopify_df.shape}")
                
        except Exception as e:
            logger.warning(f"Failed to load data for week {base_week}: {e}")
    
    # Calculate KPIs for each week
    kpis_list = []
    
    for week_idx, week_str in enumerate(weeks_to_analyze):
        # Filter data for this week (iso_week column already computed)
        week_qlik_df = filter_data_by_iso_week(qlik_df, week_str, 'Date')
        
        # Filter Shopify data by week (iso_week column already computed)
        week_shopify_df = shopify_df.copy()
        if not shopify_df.empty and 'iso_week' in shopify_df.columns:
            week_shopify_df = shopify_df[shopify_df['iso_week'] == week_str].copy()
        
        # Filter DEMA data by week (iso_week column already computed)
        week_dema_df = dema_df.copy()
        if not dema_df.empty and 'iso_week' in dema_df.columns:
            week_dema_df = dema_df[dema_df['iso_week'] == week_str].copy()
        
        if week_qlik_df.empty:
            logger.warning(f"Missing data for week {week_str}")
            continue
        
        # Calculate KPIs
        week_kpis = calculate_week_kpis(week_qlik_df, week_shopify_df, week_dema_df, week_str)
        
        # Add last year comparison
        last_year_week = last_year_weeks[week_idx]
        last_year_qlik_df = filter_data_by_iso_week(qlik_df, last_year_week, 'Date')
        
        # Filter Shopify data for last year
        last_year_shopify_df = shopify_df.copy()
        if not shopify_df.empty and 'iso_week' in shopify_df.columns:
            last_year_shopify_df = shopify_df[shopify_df['iso_week'] == last_year_week].copy()
        
        # Filter DEMA data for last year
        last_year_dema_df = dema_df.copy()
        if not dema_df.empty and 'iso_week' in dema_df.columns:
            last_year_dema_df = dema_df[dema_df['iso_week'] == last_year_week].copy()
        
        if not last_year_qlik_df.empty:
            last_year_kpis = calculate_week_kpis(
                last_year_qlik_df,
                last_year_shopify_df,  # Use filtered shopify data for last year
                last_year_dema_df,  # Use filtered dema data for last year
                last_year_week
            )
            week_kpis['last_year'] = last_year_kpis
        
        kpis_list.append(week_kpis)
    
    # Get latest week date range
    latest_week = weeks_to_analyze[-1]
    date_range = get_week_date_range(latest_week)
    
    return {
        'kpis': kpis_list,
        'period_info': {
            'latest_week': latest_week,
            'latest_dates': date_range
        }
    }


def calculate_week_kpis(qlik_df: pd.DataFrame, shopify_df: pd.DataFrame, dema_df: pd.DataFrame, week_str: str) -> Dict[str, Any]:
    """Calculate KPIs for a single week."""
    
    # Filter for online sales only
    online_df = qlik_df[qlik_df['Sales Channel'] == 'Online']
    
    # Calculate metrics
    gross_revenue = online_df['Gross Revenue'].sum()
    net_revenue = online_df['Net Revenue'].sum()
    
    # New/Returning customers
    new_customers = online_df[online_df['New/Returning Customer'] == 'New']['Customer E-mail'].nunique()
    returning_customers = online_df[online_df['New/Returning Customer'] == 'Returning']['Customer E-mail'].nunique()
    
    # New customer revenue
    new_customer_df = online_df[online_df['New/Returning Customer'] == 'New']
    new_customer_revenue = new_customer_df['Net Revenue'].sum()
    
    # Returning customer revenue
    returning_customer_df = online_df[online_df['New/Returning Customer'] == 'Returning']
    returning_customer_revenue = returning_customer_df['Net Revenue'].sum()
    
    # Calculate AOVs
    aov_new_customer = new_customer_revenue / new_customers if new_customers > 0 else 0
    aov_returning_customer = returning_customer_revenue / returning_customers if returning_customers > 0 else 0
    
    # Sessions from Shopify
    if not shopify_df.empty and 'Sessions' in shopify_df.columns:
        sessions = shopify_df['Sessions'].sum()
    else:
        sessions = 0
    
    # Conversion rate
    unique_orders = online_df['Order No'].nunique()
    conversion_rate = (unique_orders / sessions * 100) if sessions > 0 else 0
    
    # COS (Cost of Sale) - from DEMA spend
    if not dema_df.empty and 'Marketing spend' in dema_df.columns:
        marketing_spend = dema_df['Marketing spend'].sum()
    elif not dema_df.empty and 'Cost' in dema_df.columns:
        marketing_spend = dema_df['Cost'].sum()
    else:
        marketing_spend = 0
    
    # Calculate CoS as percentage: marketing spend / gross sales * 100
    cos = (marketing_spend / gross_revenue * 100) if gross_revenue > 0 else 0
    
    # New Customer CAC (Customer Acquisition Cost)
    new_customer_cac = marketing_spend / new_customers if new_customers > 0 else 0
    
    # Total Orders
    total_orders = online_df['Order No'].nunique()
    
    return {
        'week': week_str,
        'aov_new_customer': float(aov_new_customer),
        'aov_returning_customer': float(aov_returning_customer),
        'cos': float(cos),
        'marketing_spend': float(marketing_spend),
        'conversion_rate': float(conversion_rate),
        'new_customers': int(new_customers),
        'returning_customers': int(returning_customers),
        'sessions': int(sessions),
        'new_customer_cac': float(new_customer_cac),
        'total_orders': int(total_orders)
    }

