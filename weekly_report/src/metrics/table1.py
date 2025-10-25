"""Table 1 metrics calculation module."""

import pandas as pd
from typing import Dict, Any, Optional
from pathlib import Path
from loguru import logger

from weekly_report.src.adapters import qlik, dema, dema_gm2, shopify
from weekly_report.src.periods.calculator import get_week_date_range, get_ytd_periods_for_week
from weekly_report.src.cache.manager import RawDataCache

# Global raw data cache - holds Excel data in memory for 2 hours
raw_data_cache = RawDataCache(max_age_hours=2)


def calculate_table1_metrics(
    qlik_df: pd.DataFrame, 
    dema_spend_df: pd.DataFrame, 
    dema_gm2_df: pd.DataFrame, 
    period_week: str
) -> Dict[str, Any]:
    """
    Calculate all 13 metrics for Table 1 from Qlik and Dema data.
    
    Args:
        qlik_df: Qlik data DataFrame
        dema_spend_df: Dema spend data DataFrame  
        dema_gm2_df: Dema GM2 data DataFrame
        period_week: ISO week string like '2025-42'
        
    Returns:
        Dictionary with all 13 metrics:
        {
            'online_gross_revenue': 1145000,
            'returns': 24000,
            'return_rate_pct': 2.1,
            'online_net_revenue': 1121000,
            'retail_concept_store': 55000,
            'retail_popups_outlets': 0,
            'retail_net_revenue': 55000,
            'wholesale_net_revenue': 0,
            'total_net_revenue': 1176000,
            'returning_customers': 418,
            'new_customers': 189,
            'marketing_spend': 359000,
            'online_cost_of_sale_3': 99000
        }
    """
    
    logger.info(f"Calculating Table 1 metrics for period {period_week}")
    
    # Get date range for filtering
    date_range = get_week_date_range(period_week)
    start_date = pd.to_datetime(date_range['start'])
    end_date = pd.to_datetime(date_range['end'])
    
    # Filter Qlik data to the specific week
    qlik_filtered = qlik_df[
        (pd.to_datetime(qlik_df['Date']) >= start_date) & 
        (pd.to_datetime(qlik_df['Date']) <= end_date)
    ].copy()
    
    logger.debug(f"Filtered Qlik data to {len(qlik_filtered)} records for {period_week}")
    
    # Filter Dema data to the specific week
    dema_spend_filtered = dema_spend_df[
        (pd.to_datetime(dema_spend_df['Days']) >= start_date) & 
        (pd.to_datetime(dema_spend_df['Days']) <= end_date)
    ].copy()
    
    dema_gm2_filtered = dema_gm2_df[
        (pd.to_datetime(dema_gm2_df['Days']) >= start_date) & 
        (pd.to_datetime(dema_gm2_df['Days']) <= end_date)
    ].copy()
    
    logger.debug(f"Filtered Dema spend data to {len(dema_spend_filtered)} records")
    logger.debug(f"Filtered Dema GM2 data to {len(dema_gm2_filtered)} records")
    
    metrics = {}
    
    # 1. Online Gross Revenue = SUM(Gross Revenue WHERE Sales Channel = 'Online')
    online_gross_revenue = qlik_filtered[
        qlik_filtered['Sales Channel'] == 'Online'
    ]['Gross Revenue'].sum()
    metrics['online_gross_revenue'] = float(online_gross_revenue)
    
    # 2. Returns = SUM(Returns)
    returns = qlik_filtered['Returns'].sum()
    metrics['returns'] = float(returns)
    
    # 3. Return Rate % = (Returns / Online Gross Revenue) * 100
    if online_gross_revenue > 0:
        return_rate_pct = (returns / online_gross_revenue) * 100
    else:
        return_rate_pct = 0.0
    metrics['return_rate_pct'] = round(return_rate_pct, 1)
    
    # 4. Online Net Revenue = SUM(Net Revenue WHERE Sales Channel = 'Online')
    online_net_revenue = qlik_filtered[
        qlik_filtered['Sales Channel'] == 'Online'
    ]['Net Revenue'].sum()
    metrics['online_net_revenue'] = float(online_net_revenue)
    
    # 5. Retail Concept Store = SUM(Net Revenue WHERE Sales Channel = 'Retail' AND Country != 'Outlet')
    retail_concept_store = qlik_filtered[
        (qlik_filtered['Sales Channel'] == 'Retail') & 
        (qlik_filtered['Country'] != 'Outlet')
    ]['Net Revenue'].sum()
    metrics['retail_concept_store'] = float(retail_concept_store)
    
    # 6. Retail Pop-ups, Outlets = SUM(Net Revenue WHERE Sales Channel = 'Retail' AND Country = 'Outlet')
    retail_popups_outlets = qlik_filtered[
        (qlik_filtered['Sales Channel'] == 'Retail') & 
        (qlik_filtered['Country'] == 'Outlet')
    ]['Net Revenue'].sum()
    metrics['retail_popups_outlets'] = float(retail_popups_outlets)
    
    # 7. Retail Net Revenue = Retail Concept Store + Retail Pop-ups
    retail_net_revenue = retail_concept_store + retail_popups_outlets
    metrics['retail_net_revenue'] = float(retail_net_revenue)
    
    # 8. Wholesale Net Revenue = SUM(Net Revenue WHERE Sales Channel = 'Wholesale')
    wholesale_net_revenue = qlik_filtered[
        qlik_filtered['Sales Channel'] == 'Wholesale'
    ]['Net Revenue'].sum()
    metrics['wholesale_net_revenue'] = float(wholesale_net_revenue)
    
    # 9. Total Net Revenue = Online Net Revenue + Retail Net Revenue + Wholesale
    total_net_revenue = online_net_revenue + retail_net_revenue + wholesale_net_revenue
    metrics['total_net_revenue'] = float(total_net_revenue)
    
    # 10. Returning Customers = COUNT(DISTINCT Customer E-mail WHERE New/Returning Customer = 'Returning')
    returning_customers = qlik_filtered[
        qlik_filtered['New/Returning Customer'] == 'Returning'
    ]['Customer E-mail'].nunique()
    metrics['returning_customers'] = int(returning_customers)
    
    # 11. New customers = COUNT(DISTINCT Customer E-mail WHERE New/Returning Customer = 'New')
    new_customers = qlik_filtered[
        qlik_filtered['New/Returning Customer'] == 'New'
    ]['Customer E-mail'].nunique()
    metrics['new_customers'] = int(new_customers)
    
    # 12. Marketing Spend = SUM(Marketing spend från dema_spend)
    marketing_spend = dema_spend_filtered['Marketing spend'].sum()
    metrics['marketing_spend'] = float(marketing_spend)
    
    # 13. Online Cost of Sale(3) = (Marketing Spend / Online Gross Revenue) * 100
    if online_gross_revenue > 0:
        online_cost_of_sale_3 = (marketing_spend / online_gross_revenue) * 100
    else:
        online_cost_of_sale_3 = 0.0
    metrics['online_cost_of_sale_3'] = round(online_cost_of_sale_3, 1)
    
    logger.info(f"Calculated {len(metrics)} metrics for {period_week}")
    logger.debug(f"Sample metrics: {dict(list(metrics.items())[:3])}")
    
    return metrics


def load_all_raw_data(data_path: Path) -> Dict[str, pd.DataFrame]:
    """
    Load all raw data files ONCE for efficient reuse across multiple periods.
    Uses in-memory cache to avoid reloading large Excel files.
    
    Args:
        data_path: Path to raw data directory (e.g., data/raw/2025-42)
        
    Returns:
        Dictionary with loaded DataFrames:
        {
            'qlik': DataFrame,
            'dema_spend': DataFrame,
            'dema_gm2': DataFrame
        }
    """
    data_path_str = str(data_path)
    
    # Check cache first
    cached_data = raw_data_cache.get(data_path_str)
    if cached_data:
        return cached_data
    
    logger.info(f"Loading all raw data from {data_path}")
    
    data_sources = {}
    
    # Load Qlik data
    try:
        data_sources['qlik'] = qlik.load_data(data_path)
        logger.info(f"Loaded Qlik data: {data_sources['qlik'].shape}")
    except FileNotFoundError as e:
        logger.error(f"Qlik data not found: {e}")
        raise
    
    # Load Dema spend data
    try:
        data_sources['dema_spend'] = dema.load_data(data_path)
        logger.info(f"Loaded Dema spend data: {data_sources['dema_spend'].shape}")
    except FileNotFoundError as e:
        logger.error(f"Dema spend data not found: {e}")
        raise
    
    # Load Dema GM2 data
    try:
        data_sources['dema_gm2'] = dema_gm2.load_data(data_path)
        logger.info(f"Loaded Dema GM2 data: {data_sources['dema_gm2'].shape}")
    except FileNotFoundError as e:
        logger.error(f"Dema GM2 data not found: {e}")
        raise
    
    # Load Shopify data
    try:
        data_sources['shopify'] = shopify.load_data(data_path)
        logger.info(f"Loaded Shopify data: {data_sources['shopify'].shape}")
    except FileNotFoundError as e:
        logger.warning(f"Shopify data not found: {e}")
        data_sources['shopify'] = pd.DataFrame()
    
    # Cache the loaded data
    raw_data_cache.set(data_path_str, data_sources)
    
    logger.info(f"Successfully loaded and cached all raw data sources")
    return data_sources


def filter_data_for_period(all_data: Dict[str, pd.DataFrame], period_week: str) -> Dict[str, pd.DataFrame]:
    """
    Filter pre-loaded data for specific ISO week.
    
    Args:
        all_data: Dictionary with all raw DataFrames
        period_week: ISO week string like '2025-42'
        
    Returns:
        Dictionary with filtered DataFrames for the period
    """
    logger.info(f"Filtering data for period {period_week}")
    
    filtered_data = {}
    
    # Filter Qlik data by ISO week
    qlik_data = all_data['qlik'].copy()
    if 'Date' in qlik_data.columns:
        qlik_data['Date'] = pd.to_datetime(qlik_data['Date'], errors='coerce')
        qlik_data['ISO_Week'] = qlik_data['Date'].dt.isocalendar().week
        qlik_data['ISO_Year'] = qlik_data['Date'].dt.isocalendar().year
        qlik_data['ISO_Week_Str'] = qlik_data['ISO_Year'].astype(str) + '-' + qlik_data['ISO_Week'].astype(str).str.zfill(2)
        
        period_data = qlik_data[qlik_data['ISO_Week_Str'] == period_week]
        filtered_data['qlik'] = period_data.drop(['ISO_Week', 'ISO_Year', 'ISO_Week_Str'], axis=1)
        logger.info(f"Filtered Qlik data for {period_week}: {filtered_data['qlik'].shape}")
    else:
        logger.error(f"No Date column found in Qlik data for filtering")
        raise ValueError(f"Cannot filter Qlik data for {period_week}")
    
    # Filter Dema spend data by ISO week
    dema_spend_data = all_data['dema_spend'].copy()
    if 'Days' in dema_spend_data.columns:
        dema_spend_data['Days'] = pd.to_datetime(dema_spend_data['Days'], errors='coerce')
        dema_spend_data['ISO_Week'] = dema_spend_data['Days'].dt.isocalendar().week
        dema_spend_data['ISO_Year'] = dema_spend_data['Days'].dt.isocalendar().year
        dema_spend_data['ISO_Week_Str'] = dema_spend_data['ISO_Year'].astype(str) + '-' + dema_spend_data['ISO_Week'].astype(str).str.zfill(2)
        
        period_data = dema_spend_data[dema_spend_data['ISO_Week_Str'] == period_week]
        filtered_data['dema_spend'] = period_data.drop(['ISO_Week', 'ISO_Year', 'ISO_Week_Str'], axis=1)
        logger.info(f"Filtered Dema spend data for {period_week}: {filtered_data['dema_spend'].shape}")
    else:
        logger.error(f"No Days column found in Dema spend data for filtering")
        raise ValueError(f"Cannot filter Dema spend data for {period_week}")
    
    # Filter Dema GM2 data by ISO week
    dema_gm2_data = all_data['dema_gm2'].copy()
    if 'Days' in dema_gm2_data.columns:
        dema_gm2_data['Days'] = pd.to_datetime(dema_gm2_data['Days'], errors='coerce')
        dema_gm2_data['ISO_Week'] = dema_gm2_data['Days'].dt.isocalendar().week
        dema_gm2_data['ISO_Year'] = dema_gm2_data['Days'].dt.isocalendar().year
        dema_gm2_data['ISO_Week_Str'] = dema_gm2_data['ISO_Year'].astype(str) + '-' + dema_gm2_data['ISO_Week'].astype(str).str.zfill(2)
        
        period_data = dema_gm2_data[dema_gm2_data['ISO_Week_Str'] == period_week]
        filtered_data['dema_gm2'] = period_data.drop(['ISO_Week', 'ISO_Year', 'ISO_Week_Str'], axis=1)
        logger.info(f"Filtered Dema GM2 data for {period_week}: {filtered_data['dema_gm2'].shape}")
    else:
        logger.error(f"No Days column found in Dema GM2 data for filtering")
        raise ValueError(f"Cannot filter Dema GM2 data for {period_week}")
    
    logger.info(f"Successfully filtered all data for {period_week}")
    return filtered_data


def filter_data_for_date_range(all_data: Dict[str, pd.DataFrame], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
    """
    Filter pre-loaded data for specific date range (for YTD calculations).
    
    Args:
        all_data: Dictionary with all raw DataFrames
        start_date: Start date string like '2025-04-01'
        end_date: End date string like '2025-10-19'
        
    Returns:
        Dictionary with filtered DataFrames for the date range
    """
    logger.info(f"Filtering data for date range {start_date} to {end_date}")
    
    filtered_data = {}
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    
    # Filter Qlik data by date range
    qlik_data = all_data['qlik'].copy()
    if 'Date' in qlik_data.columns:
        qlik_data['Date'] = pd.to_datetime(qlik_data['Date'], errors='coerce')
        period_data = qlik_data[
            (qlik_data['Date'] >= start_dt) & 
            (qlik_data['Date'] <= end_dt)
        ]
        filtered_data['qlik'] = period_data
        logger.info(f"Filtered Qlik data for date range: {filtered_data['qlik'].shape}")
    else:
        logger.error(f"No Date column found in Qlik data for filtering")
        raise ValueError(f"Cannot filter Qlik data for date range {start_date} to {end_date}")
    
    # Filter Dema spend data by date range
    dema_spend_data = all_data['dema_spend'].copy()
    if 'Days' in dema_spend_data.columns:
        dema_spend_data['Days'] = pd.to_datetime(dema_spend_data['Days'], errors='coerce')
        period_data = dema_spend_data[
            (dema_spend_data['Days'] >= start_dt) & 
            (dema_spend_data['Days'] <= end_dt)
        ]
        filtered_data['dema_spend'] = period_data
        logger.info(f"Filtered Dema spend data for date range: {filtered_data['dema_spend'].shape}")
    else:
        logger.error(f"No Days column found in Dema spend data for filtering")
        raise ValueError(f"Cannot filter Dema spend data for date range {start_date} to {end_date}")
    
    # Filter Dema GM2 data by date range
    dema_gm2_data = all_data['dema_gm2'].copy()
    if 'Days' in dema_gm2_data.columns:
        dema_gm2_data['Days'] = pd.to_datetime(dema_gm2_data['Days'], errors='coerce')
        period_data = dema_gm2_data[
            (dema_gm2_data['Days'] >= start_dt) & 
            (dema_gm2_data['Days'] <= end_dt)
        ]
        filtered_data['dema_gm2'] = period_data
        logger.info(f"Filtered Dema GM2 data for date range: {filtered_data['dema_gm2'].shape}")
    else:
        logger.error(f"No Days column found in Dema GM2 data for filtering")
        raise ValueError(f"Cannot filter Dema GM2 data for date range {start_date} to {end_date}")
    
    logger.info(f"Successfully filtered all data for date range {start_date} to {end_date}")
    return filtered_data


def calculate_table1_metrics_for_date_range(
    qlik_df: pd.DataFrame, 
    dema_spend_df: pd.DataFrame, 
    dema_gm2_df: pd.DataFrame, 
    start_date: str,
    end_date: str
) -> Dict[str, Any]:
    """
    Calculate all 13 metrics for Table 1 from Qlik and Dema data for a date range.
    
    Args:
        qlik_df: Qlik data DataFrame
        dema_spend_df: Dema spend data DataFrame  
        dema_gm2_df: Dema GM2 data DataFrame
        start_date: Start date string like '2025-04-01'
        end_date: End date string like '2025-10-19'
        
    Returns:
        Dictionary with all 13 metrics
    """
    
    logger.info(f"Calculating Table 1 metrics for date range {start_date} to {end_date}")
    
    metrics = {}
    
    # 1. Online Gross Revenue = SUM(Gross Revenue WHERE Sales Channel = 'Online')
    online_gross_revenue = qlik_df[
        qlik_df['Sales Channel'] == 'Online'
    ]['Gross Revenue'].sum()
    metrics['online_gross_revenue'] = float(online_gross_revenue)
    
    # 2. Returns = SUM(Returns)
    returns = qlik_df['Returns'].sum()
    metrics['returns'] = float(returns)
    
    # 3. Return Rate % = (Returns / Online Gross Revenue) * 100
    if online_gross_revenue > 0:
        return_rate_pct = (returns / online_gross_revenue) * 100
    else:
        return_rate_pct = 0.0
    metrics['return_rate_pct'] = round(return_rate_pct, 1)
    
    # 4. Online Net Revenue = SUM(Net Revenue WHERE Sales Channel = 'Online')
    online_net_revenue = qlik_df[
        qlik_df['Sales Channel'] == 'Online'
    ]['Net Revenue'].sum()
    metrics['online_net_revenue'] = float(online_net_revenue)
    
    # 5. Retail Concept Store = SUM(Net Revenue WHERE Sales Channel = 'Retail' AND Country != 'Outlet')
    retail_concept_store = qlik_df[
        (qlik_df['Sales Channel'] == 'Retail') & 
        (qlik_df['Country'] != 'Outlet')
    ]['Net Revenue'].sum()
    metrics['retail_concept_store'] = float(retail_concept_store)
    
    # 6. Retail Pop-ups, Outlets = SUM(Net Revenue WHERE Sales Channel = 'Retail' AND Country = 'Outlet')
    retail_popups_outlets = qlik_df[
        (qlik_df['Sales Channel'] == 'Retail') & 
        (qlik_df['Country'] == 'Outlet')
    ]['Net Revenue'].sum()
    metrics['retail_popups_outlets'] = float(retail_popups_outlets)
    
    # 7. Retail Net Revenue = Retail Concept Store + Retail Pop-ups
    retail_net_revenue = retail_concept_store + retail_popups_outlets
    metrics['retail_net_revenue'] = float(retail_net_revenue)
    
    # 8. Wholesale Net Revenue = SUM(Net Revenue WHERE Sales Channel = 'Wholesale')
    wholesale_net_revenue = qlik_df[
        qlik_df['Sales Channel'] == 'Wholesale'
    ]['Net Revenue'].sum()
    metrics['wholesale_net_revenue'] = float(wholesale_net_revenue)
    
    # 9. Total Net Revenue = Online Net Revenue + Retail Net Revenue + Wholesale
    total_net_revenue = online_net_revenue + retail_net_revenue + wholesale_net_revenue
    metrics['total_net_revenue'] = float(total_net_revenue)
    
    # 10. Returning Customers = COUNT(DISTINCT Customer E-mail WHERE New/Returning Customer = 'Returning')
    returning_customers = qlik_df[
        qlik_df['New/Returning Customer'] == 'Returning'
    ]['Customer E-mail'].nunique()
    metrics['returning_customers'] = int(returning_customers)
    
    # 11. New customers = COUNT(DISTINCT Customer E-mail WHERE New/Returning Customer = 'New')
    new_customers = qlik_df[
        qlik_df['New/Returning Customer'] == 'New'
    ]['Customer E-mail'].nunique()
    metrics['new_customers'] = int(new_customers)
    
    # 12. Marketing Spend = SUM(Marketing spend från dema_spend)
    marketing_spend = dema_spend_df['Marketing spend'].sum()
    metrics['marketing_spend'] = float(marketing_spend)
    
    # 13. Online Cost of Sale(3) = (Marketing Spend / Online Gross Revenue) * 100
    if online_gross_revenue > 0:
        online_cost_of_sale_3 = (marketing_spend / online_gross_revenue) * 100
    else:
        online_cost_of_sale_3 = 0.0
    metrics['online_cost_of_sale_3'] = round(online_cost_of_sale_3, 1)
    
    logger.info(f"Calculated {len(metrics)} metrics for date range {start_date} to {end_date}")
    logger.debug(f"Sample metrics: {dict(list(metrics.items())[:3])}")
    
    return metrics


def calculate_table1_for_periods_with_ytd(periods: Dict[str, str], data_root: Path) -> Dict[str, Dict[str, Any]]:
    """
    Calculate Table 1 metrics for multiple periods INCLUDING YTD columns.
    
    Args:
        periods: Dictionary with period mappings (from get_periods_for_week)
        data_root: Root data directory
        
    Returns:
        Dictionary with metrics for each period including YTD:
        {
            'actual': {metrics...},
            'last_week': {metrics...},
            'last_year': {metrics...},
            'year_2023': {metrics...},
            'ytd_actual': {metrics...},
            'ytd_last_year': {metrics...},
            'ytd_2023': {metrics...}
        }
    """
    
    logger.info(f"Calculating Table 1 metrics for {len(periods)} periods + YTD")
    
    # Get base week from periods
    base_week = periods['actual']
    
    # Load all raw data ONCE
    latest_data_path = data_root / "raw" / "2025-42"
    
    try:
        logger.info("Loading all raw data sources ONCE...")
        all_raw_data = load_all_raw_data(latest_data_path)
        logger.info("Successfully loaded all raw data")
    except Exception as e:
        logger.error(f"Failed to load raw data: {e}")
        raise
    
    results = {}
    
    # Calculate regular periods
    for period_name, period_week in periods.items():
        logger.info(f"Processing {period_name}: {period_week}")
        
        try:
            filtered_data = filter_data_for_period(all_raw_data, period_week)
            metrics = calculate_table1_metrics(
                filtered_data['qlik'],
                filtered_data['dema_spend'], 
                filtered_data['dema_gm2'],
                period_week
            )
            results[period_name] = metrics
        except Exception as e:
            logger.warning(f"Failed to process {period_name} ({period_week}): {e}")
            results[period_name] = _get_zero_metrics()
    
    # Calculate YTD periods
    try:
        ytd_periods = get_ytd_periods_for_week(base_week)
        
        for ytd_name, date_range in ytd_periods.items():
            logger.info(f"Processing {ytd_name}: {date_range['start']} to {date_range['end']}")
            
            try:
                filtered_data = filter_data_for_date_range(
                    all_raw_data,
                    date_range['start'],
                    date_range['end']
                )
                
                metrics = calculate_table1_metrics_for_date_range(
                    filtered_data['qlik'],
                    filtered_data['dema_spend'],
                    filtered_data['dema_gm2'],
                    date_range['start'],
                    date_range['end']
                )
                
                results[ytd_name] = metrics
            except Exception as e:
                logger.warning(f"Failed to process {ytd_name}: {e}")
                results[ytd_name] = _get_zero_metrics()
    except Exception as e:
        logger.error(f"Failed to calculate YTD periods: {e}")
    
    logger.info(f"Completed metrics calculation for {len(results)} periods")
    return results


def _get_zero_metrics() -> Dict[str, Any]:
    """Return a dictionary with all metrics set to zero."""
    return {
        'online_gross_revenue': 0.0,
        'returns': 0.0,
        'return_rate_pct': 0.0,
        'online_net_revenue': 0.0,
        'retail_concept_store': 0.0,
        'retail_popups_outlets': 0.0,
        'retail_net_revenue': 0.0,
        'wholesale_net_revenue': 0.0,
        'total_net_revenue': 0.0,
        'returning_customers': 0,
        'new_customers': 0,
        'marketing_spend': 0.0,
        'online_cost_of_sale_3': 0.0
    }


def load_data_for_period(period_week: str, data_root: Path) -> Dict[str, pd.DataFrame]:
    """
    Load all required data for a specific period.
    
    Args:
        period_week: ISO week string like '2025-42'
        data_root: Root data directory
        
    Returns:
        Dictionary with loaded DataFrames:
        {
            'qlik': DataFrame,
            'dema_spend': DataFrame,
            'dema_gm2': DataFrame
        }
    """
    
    raw_data_path = data_root / "raw" / period_week
    
    logger.info(f"Loading data for period {period_week} from {raw_data_path}")
    
    data_sources = {}
    
    try:
        # Load Qlik data
        data_sources['qlik'] = qlik.load_data(raw_data_path)
        logger.info(f"Loaded Qlik data: {data_sources['qlik'].shape}")
    except FileNotFoundError as e:
        logger.warning(f"Qlik data not found for {period_week}: {e}")
        # Try to load from the latest available data and filter by date
        try:
            latest_data_path = data_root / "raw" / "2025-42"  # Use latest available data
            all_qlik_data = qlik.load_data(latest_data_path)
            logger.info(f"Loading from latest data and filtering for {period_week}")
            
            # Filter data by ISO week
            if 'Date' in all_qlik_data.columns:
                # Convert Date column to datetime and filter by ISO week
                all_qlik_data['Date'] = pd.to_datetime(all_qlik_data['Date'], errors='coerce')
                
                # Get ISO week from date
                all_qlik_data['ISO_Week'] = all_qlik_data['Date'].dt.isocalendar().week
                all_qlik_data['ISO_Year'] = all_qlik_data['Date'].dt.isocalendar().year
                all_qlik_data['ISO_Week_Str'] = all_qlik_data['ISO_Year'].astype(str) + '-' + all_qlik_data['ISO_Week'].astype(str).str.zfill(2)
                
                # Filter for the specific period
                period_data = all_qlik_data[all_qlik_data['ISO_Week_Str'] == period_week]
                data_sources['qlik'] = period_data.drop(['ISO_Week', 'ISO_Year', 'ISO_Week_Str'], axis=1)
                logger.info(f"Filtered Qlik data for {period_week}: {data_sources['qlik'].shape}")
            else:
                logger.error(f"No Date column found in Qlik data for filtering")
                raise FileNotFoundError(f"No data available for {period_week}")
        except Exception as filter_error:
            logger.error(f"Failed to filter data for {period_week}: {filter_error}")
            raise FileNotFoundError(f"No data available for {period_week}")
    
    try:
        # Load Dema spend data
        data_sources['dema_spend'] = dema.load_data(raw_data_path)
        logger.info(f"Loaded Dema spend data: {data_sources['dema_spend'].shape}")
    except FileNotFoundError as e:
        logger.warning(f"Dema spend data not found for {period_week}: {e}")
        # Try to load from latest and filter
        try:
            latest_data_path = data_root / "raw" / "2025-42"
            all_dema_data = dema.load_data(latest_data_path)
            
            if 'Days' in all_dema_data.columns:
                all_dema_data['Days'] = pd.to_datetime(all_dema_data['Days'], errors='coerce')
                all_dema_data['ISO_Week'] = all_dema_data['Days'].dt.isocalendar().week
                all_dema_data['ISO_Year'] = all_dema_data['Days'].dt.isocalendar().year
                all_dema_data['ISO_Week_Str'] = all_dema_data['ISO_Year'].astype(str) + '-' + all_dema_data['ISO_Week'].astype(str).str.zfill(2)
                
                period_data = all_dema_data[all_dema_data['ISO_Week_Str'] == period_week]
                data_sources['dema_spend'] = period_data.drop(['ISO_Week', 'ISO_Year', 'ISO_Week_Str'], axis=1)
                logger.info(f"Filtered Dema spend data for {period_week}: {data_sources['dema_spend'].shape}")
            else:
                logger.error(f"No Days column found in Dema data for filtering")
                raise FileNotFoundError(f"No data available for {period_week}")
        except Exception as filter_error:
            logger.error(f"Failed to filter Dema data for {period_week}: {filter_error}")
            raise FileNotFoundError(f"No data available for {period_week}")
    
    try:
        # Load Dema GM2 data
        data_sources['dema_gm2'] = dema_gm2.load_data(raw_data_path)
        logger.info(f"Loaded Dema GM2 data: {data_sources['dema_gm2'].shape}")
    except FileNotFoundError as e:
        logger.warning(f"Dema GM2 data not found for {period_week}: {e}")
        # Try to load from latest and filter
        try:
            latest_data_path = data_root / "raw" / "2025-42"
            all_dema_gm2_data = dema_gm2.load_data(latest_data_path)
            
            if 'Days' in all_dema_gm2_data.columns:
                all_dema_gm2_data['Days'] = pd.to_datetime(all_dema_gm2_data['Days'], errors='coerce')
                all_dema_gm2_data['ISO_Week'] = all_dema_gm2_data['Days'].dt.isocalendar().week
                all_dema_gm2_data['ISO_Year'] = all_dema_gm2_data['Days'].dt.isocalendar().year
                all_dema_gm2_data['ISO_Week_Str'] = all_dema_gm2_data['ISO_Year'].astype(str) + '-' + all_dema_gm2_data['ISO_Week'].astype(str).str.zfill(2)
                
                period_data = all_dema_gm2_data[all_dema_gm2_data['ISO_Week_Str'] == period_week]
                data_sources['dema_gm2'] = period_data.drop(['ISO_Week', 'ISO_Year', 'ISO_Week_Str'], axis=1)
                logger.info(f"Filtered Dema GM2 data for {period_week}: {data_sources['dema_gm2'].shape}")
            else:
                logger.error(f"No Days column found in Dema GM2 data for filtering")
                raise FileNotFoundError(f"No data available for {period_week}")
        except Exception as filter_error:
            logger.error(f"Failed to filter Dema GM2 data for {period_week}: {filter_error}")
            raise FileNotFoundError(f"No data available for {period_week}")
    
    return data_sources


def calculate_table1_for_periods(
    periods: Dict[str, str], 
    data_root: Path
) -> Dict[str, Dict[str, Any]]:
    """
    Calculate Table 1 metrics for multiple periods (OPTIMIZED VERSION).
    
    Loads raw data ONCE and filters for each period, instead of loading 4 times.
    
    Args:
        periods: Dictionary with period mappings (from get_periods_for_week)
        data_root: Root data directory
        
    Returns:
        Dictionary with metrics for each period:
        {
            'actual': {metrics...},
            'last_week': {metrics...},
            'last_year': {metrics...},
            'year_2023': {metrics...}
        }
    """
    
    logger.info(f"Calculating Table 1 metrics for {len(periods)} periods")
    
    # OPTIMIZATION: Load all raw data ONCE
    # Use the latest available data directory (2025-42) which contains multi-year data
    latest_data_path = data_root / "raw" / "2025-42"
    
    try:
        logger.info("Loading all raw data sources ONCE for efficient reuse...")
        all_raw_data = load_all_raw_data(latest_data_path)
        logger.info("Successfully loaded all raw data - now filtering for each period")
    except Exception as e:
        logger.error(f"Failed to load raw data: {e}")
        raise
    
    results = {}
    
    for period_name, period_week in periods.items():
        logger.info(f"Processing {period_name}: {period_week}")
        
        try:
            # OPTIMIZATION: Filter pre-loaded data instead of loading again
            filtered_data = filter_data_for_period(all_raw_data, period_week)
            
            # Calculate metrics using filtered data
            metrics = calculate_table1_metrics(
                filtered_data['qlik'],
                filtered_data['dema_spend'], 
                filtered_data['dema_gm2'],
                period_week
            )
            
            results[period_name] = metrics
            
        except Exception as e:
            logger.warning(f"Failed to process {period_name} ({period_week}): {e}")
            # Return zeros for missing data
            results[period_name] = {
                'online_gross_revenue': 0.0,
                'returns': 0.0,
                'return_rate_pct': 0.0,
                'online_net_revenue': 0.0,
                'retail_concept_store': 0.0,
                'retail_popups_outlets': 0.0,
                'retail_net_revenue': 0.0,
                'wholesale_net_revenue': 0.0,
                'total_net_revenue': 0.0,
                'returning_customers': 0,
                'new_customers': 0,
                'marketing_spend': 0.0,
                'online_cost_of_sale_3': 0.0
            }
    
    logger.info(f"Completed metrics calculation for {len(results)} periods")
    return results
