"""
Calculate Online KPIs for the last 8 weeks.
"""
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd
from loguru import logger

from weekly_report.src.adapters.qlik import load_data as load_qlik_data
from weekly_report.src.adapters.shopify import load_data as load_shopify_data
from weekly_report.src.adapters.dema import load_data as load_dema_spend_data
from weekly_report.src.periods.calculator import get_week_date_range


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
    
    # Reverse to match order
    weeks_to_analyze = weeks_to_analyze[::-1]
    last_year_weeks = last_year_weeks[::-1]
    
    logger.info(f"Calculating Online KPIs for weeks: {weeks_to_analyze}")
    logger.info(f"Last year weeks: {last_year_weeks}")
    
    # Collect all weeks
    all_weeks = list(set(weeks_to_analyze + last_year_weeks))
    
    # Load data for all weeks
    qlik_data = {}
    shopify_data = {}
    dema_spend_data = {}
    
    for week_str in all_weeks:
        week_path = data_root / week_str
        if week_path.exists():
            try:
                # Load Qlik data
                qlik_df = load_qlik_data(week_path)
                qlik_data[week_str] = qlik_df
                
                # Load Shopify data
                shopify_df = load_shopify_data(week_path)
                shopify_data[week_str] = shopify_df
                
                # Load DEMA spend data
                dema_df = load_dema_spend_data(week_path)
                dema_spend_data[week_str] = dema_df
            except Exception as e:
                logger.warning(f"Failed to load data for week {week_str}: {e}")
    
    # Calculate KPIs for each week
    kpis_list = []
    
    for week_idx, week_str in enumerate(weeks_to_analyze):
        if week_str not in qlik_data or week_str not in shopify_data:
            logger.warning(f"Missing data for week {week_str}")
            continue
        
        qlik_df = qlik_data[week_str]
        shopify_df = shopify_data[week_str]
        dema_df = dema_spend_data.get(week_str, pd.DataFrame())
        
        # Calculate KPIs
        week_kpis = calculate_week_kpis(qlik_df, shopify_df, dema_df, week_str)
        
        # Add last year comparison
        last_year_week = last_year_weeks[week_idx]
        if last_year_week in qlik_data:
            last_year_kpis = calculate_week_kpis(
                qlik_data[last_year_week],
                shopify_data.get(last_year_week, pd.DataFrame()),
                dema_spend_data.get(last_year_week, pd.DataFrame()),
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
    new_customers = online_df[online_df['New/Returning Customer'] == 'New Customer']['Customer E-mail'].nunique()
    returning_customers = online_df[online_df['New/Returning Customer'] == 'Returning Customer']['Customer E-mail'].nunique()
    
    # New customer revenue
    new_customer_df = online_df[online_df['New/Returning Customer'] == 'New Customer']
    new_customer_revenue = new_customer_df['Net Revenue'].sum()
    
    # Returning customer revenue
    returning_customer_df = online_df[online_df['New/Returning Customer'] == 'Returning Customer']
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
        cos = dema_df['Marketing spend'].sum()
    elif not dema_df.empty and 'Cost' in dema_df.columns:
        cos = dema_df['Cost'].sum()
    else:
        cos = 0
    
    # New Customer CAC (Customer Acquisition Cost)
    new_customer_cac = cos / new_customers if new_customers > 0 else 0
    
    # Total Orders
    total_orders = online_df['Order No'].nunique()
    
    return {
        'week': week_str,
        'aov_new_customer': aov_new_customer,
        'aov_returning_customer': aov_returning_customer,
        'cos': cos,
        'conversion_rate': conversion_rate,
        'new_customers': new_customers,
        'returning_customers': returning_customers,
        'sessions': sessions,
        'new_customer_cac': new_customer_cac,
        'total_orders': total_orders
    }

