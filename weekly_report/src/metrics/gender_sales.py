"""Gender sales metrics calculation."""
from typing import Dict, Any, List
import pandas as pd
from loguru import logger

from weekly_report.src.adapters.qlik import load_data
from weekly_report.src.config import load_config


def calculate_gender_sales_for_week(qlik_df: pd.DataFrame, week_str: str) -> Dict[str, Any]:
    """Calculate gross sales by gender for a single week."""
    
    # Filter for online sales only
    online_df = qlik_df[qlik_df['Sales Channel'] == 'Online']
    
    # Group by Gender
    gender_sales = online_df.groupby('Gender').agg({
        'Gross Revenue': 'sum'
    }).reset_index()
    
    # Calculate totals
    total_sales = online_df['Gross Revenue'].sum()
    
    # Get individual category sales (case-insensitive matching)
    men_sales = gender_sales[gender_sales['Gender'].str.upper() == 'MEN']['Gross Revenue'].sum() if 'MEN' in gender_sales['Gender'].str.upper().values else 0
    women_sales = gender_sales[gender_sales['Gender'].str.upper() == 'WOMEN']['Gross Revenue'].sum() if 'WOMEN' in gender_sales['Gender'].str.upper().values else 0
    unisex_sales = gender_sales[gender_sales['Gender'].str.upper() == 'UNISEX']['Gross Revenue'].sum() if 'UNISEX' in gender_sales['Gender'].str.upper().values else 0
    
    # Calculate Men + Unisex combined
    men_unisex_sales = men_sales + unisex_sales
    
    return {
        'week': week_str,
        'men_unisex_sales': float(men_unisex_sales),
        'women_sales': float(women_sales),
        'total_sales': float(total_sales)
    }


def calculate_gender_sales_for_weeks(base_week: str, num_weeks: int = 8) -> List[Dict[str, Any]]:
    """Calculate gender sales for multiple weeks."""
    
    results = []
    
    # Parse base week
    year, week_num = base_week.split('-')
    year = int(year)
    week_num = int(week_num)
    
    for i in range(num_weeks):
        # Calculate target week
        target_week_num = week_num - i
        target_year = year
        
        # Handle year rollover
        if target_week_num <= 0:
            target_year -= 1
            target_week_num += 52
        
        week_str = f"{target_year}-{target_week_num:02d}"
        
        try:
            # Load Qlik data for this week
            config = load_config(week=week_str)
            qlik_df = load_data(config.raw_data_path)
            
            if qlik_df.empty:
                logger.warning(f"No Qlik data for week {week_str}")
                continue
            
            # Calculate gender sales
            week_data = calculate_gender_sales_for_week(qlik_df, week_str)
            
            # Get last year data
            last_year = target_year - 1
            last_year_week_str = f"{last_year}-{target_week_num:02d}"
            
            try:
                last_year_config = load_config(week=last_year_week_str)
                last_year_df = load_data(last_year_config.raw_data_path)
                
                if not last_year_df.empty:
                    last_year_data = calculate_gender_sales_for_week(last_year_df, last_year_week_str)
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
    
    # Reverse to get chronological order (oldest to newest)
    results.reverse()
    
    return results

