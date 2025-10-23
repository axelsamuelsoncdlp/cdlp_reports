"""Men category sales metrics calculation."""
from typing import Dict, Any, List
import pandas as pd
from loguru import logger
from pathlib import Path

from weekly_report.src.metrics.table1 import load_all_raw_data


def calculate_men_category_sales_for_week(qlik_df: pd.DataFrame, week_str: str) -> Dict[str, Any]:
    """Calculate gross sales by product category for Men."""
    
    # Filter for online Men sales only
    men_df = qlik_df[(qlik_df['Sales Channel'] == 'Online') & (qlik_df['Gender'].str.upper() == 'MEN')]
    
    # Group by Product Category
    category_sales = men_df.groupby('Product Category').agg({
        'Gross Revenue': 'sum'
    }).reset_index()
    
    # Create result dict
    result = {
        'week': week_str,
        'categories': {}
    }
    
    # Add each category's sales
    for _, row in category_sales.iterrows():
        category = row['Product Category']
        if pd.notna(category) and category != '-':
            result['categories'][category] = float(row['Gross Revenue'])
    
    return result


def calculate_men_category_sales_for_weeks(base_week: str, num_weeks: int, data_root: Path) -> List[Dict[str, Any]]:
    """Calculate men category sales for multiple weeks."""
    
    results = []
    
    # Load all raw data once from base week directory
    logger.info(f"Loading raw data from {data_root}")
    raw_data = load_all_raw_data(data_root)
    qlik_df = raw_data.get('qlik', pd.DataFrame())
    
    if qlik_df.empty:
        logger.warning(f"No Qlik data found in {data_root}")
        return []
    
    # Add iso_week column if not present
    if 'iso_week' not in qlik_df.columns and 'Date' in qlik_df.columns:
        qlik_df['iso_week'] = qlik_df['Date'].apply(lambda x: pd.to_datetime(x).strftime('%Y-%W') if pd.notna(x) else None)
    
    # Parse base week
    year, week_num = base_week.split('-')
    year = int(year)
    week_num = int(week_num)
    
    for i in range(num_weeks):
        # Calculate target week
        target_week_num = week_num - num_weeks + 1 + i
        target_year = year
        
        # Handle year rollover
        if target_week_num <= 0:
            target_year -= 1
            target_week_num += 52
        
        week_str = f"{target_year}-{target_week_num:02d}"
        
        try:
            # Filter data for this week
            week_df = qlik_df[qlik_df['iso_week'] == week_str].copy()
            
            if week_df.empty:
                logger.warning(f"No data for week {week_str}")
                continue
            
            # Calculate category sales
            week_data = calculate_men_category_sales_for_week(week_df, week_str)
            
            # Get last year data
            last_year = target_year - 1
            last_year_week_str = f"{last_year}-{target_week_num:02d}"
            
            try:
                last_year_df = qlik_df[qlik_df['iso_week'] == last_year_week_str].copy()
                
                if not last_year_df.empty:
                    last_year_data = calculate_men_category_sales_for_week(last_year_df, last_year_week_str)
                    week_data['last_year'] = last_year_data
                else:
                    week_data['last_year'] = None
            except Exception as e:
                logger.warning(f"Could not load last year data for {last_year_week_str}: {e}")
                week_data['last_year'] = None
            
            results.append(week_data)
            
        except Exception as e:
            logger.error(f"Error processing week {week_str}: {e}")
            continue
    
    return results

