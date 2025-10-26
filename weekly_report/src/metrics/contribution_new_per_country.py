"""Contribution per New Customer per country metrics calculation."""
from typing import Dict, Any, List
import pandas as pd
from loguru import logger
from pathlib import Path

from weekly_report.src.metrics.table1 import load_all_raw_data


def calculate_contribution_new_per_country_for_week(
    qlik_df: pd.DataFrame,
    dema_df: pd.DataFrame,
    dema_gm2_df: pd.DataFrame,
    week_str: str
) -> Dict[str, Any]:
    """Calculate contribution per new customer per country for a single week."""
    
    if qlik_df.empty or dema_gm2_df.empty or dema_df.empty:
        logger.warning(f"Missing data for week {week_str}")
        return {
            'week': week_str,
            'countries': {}
        }
    
    # Filter for online sales and new customers only
    online_df = qlik_df[qlik_df['Sales Channel'] == 'Online']
    new_customers_df = online_df[online_df['New/Returning Customer'] == 'New']
    
    if new_customers_df.empty:
        logger.warning(f"No new customers found for week {week_str}")
        return {
            'week': week_str,
            'countries': {}
        }
    
    # Get marketing spend per country
    country_spend = dema_df.groupby('Country').agg({
        'Marketing spend': 'sum'
    }).reset_index()
    country_spend['New customer spend'] = country_spend['Marketing spend'] * 0.70
    
    # Get GM2 per country for new customers
    if 'Country' in dema_gm2_df.columns and 'New vs Returning Customer' in dema_gm2_df.columns:
        new_gm2_df = dema_gm2_df[dema_gm2_df['New vs Returning Customer'] == 'New']
        
        # Calculate GM2 percentage per country
        country_gm2 = new_gm2_df.groupby('Country').agg({
            'Gross margin 2 - Dema MTA': 'mean'
        }).reset_index()
        country_gm2.columns = ['Country', 'gm2_pct']
    else:
        logger.warning(f"Country or customer type not found in GM2 data for week {week_str}")
        return {
            'week': week_str,
            'countries': {}
        }
    
    # Get gross revenue per country for new customers
    country_revenue = new_customers_df.groupby('Country').agg({
        'Gross Revenue': 'sum'
    }).reset_index()
    country_revenue.columns = ['Country', 'gross_revenue']
    
    # Count new customers per country
    country_customers = new_customers_df.groupby('Country').agg(
        new_customers=('Customer E-mail', 'nunique')
    ).reset_index()
    
    # Merge all data
    merged_df = pd.merge(
        pd.merge(country_revenue, country_gm2, on='Country', how='outer'),
        pd.merge(country_spend, country_customers, on='Country', how='outer'),
        on='Country',
        how='outer'
    ).fillna(0)
    
    # Calculate GM2 in SEK per country = Gross Revenue * GM2 percentage
    merged_df['gm2_sek'] = merged_df['gross_revenue'] * merged_df['gm2_pct']
    
    # Calculate Contribution = GM2 - Marketing spend (for new customers)
    merged_df['contribution'] = merged_df['gm2_sek'] - merged_df['New customer spend']
    
    # Calculate Contribution per New Customer = Contribution / New Customers
    merged_df['contribution_per_customer'] = merged_df.apply(
        lambda row: row['contribution'] / row['new_customers'] if row['new_customers'] > 0 else 0,
        axis=1
    )
    
    # Create result dict
    result = {
        'week': week_str,
        'countries': {}
    }
    
    # Add each country's contribution per new customer
    for _, row in merged_df.iterrows():
        country = row['Country']
        if pd.notna(country) and country != '-':
            result['countries'][country] = float(row['contribution_per_customer'])
    
    return result


def calculate_contribution_new_per_country_for_weeks(base_week: str, num_weeks: int, data_root: Path) -> List[Dict[str, Any]]:
    """Calculate contribution per new customer per country for multiple weeks."""
    
    results = []
    
    # Load data
    logger.info(f"Loading data from {data_root}")
    raw_data = load_all_raw_data(data_root)
    qlik_df = raw_data.get('qlik', pd.DataFrame())
    dema_df = raw_data.get('dema_spend', pd.DataFrame())
    dema_gm2_df = raw_data.get('dema_gm2', pd.DataFrame())
    
    if qlik_df.empty or dema_df.empty or dema_gm2_df.empty:
        logger.warning(f"Missing required data in {data_root}")
        return []
    
    # Add iso_week columns if not present
    if 'iso_week' not in qlik_df.columns and 'Date' in qlik_df.columns:
        iso_cal = pd.to_datetime(qlik_df['Date']).dt.isocalendar()
        qlik_df['iso_week'] = iso_cal['year'].astype(str) + '-' + iso_cal['week'].astype(str).str.zfill(2)
    
    if 'iso_week' not in dema_df.columns and 'Days' in dema_df.columns:
        iso_cal = pd.to_datetime(dema_df['Days']).dt.isocalendar()
        dema_df['iso_week'] = iso_cal['year'].astype(str) + '-' + iso_cal['week'].astype(str).str.zfill(2)
    
    if 'iso_week' not in dema_gm2_df.columns and 'Days' in dema_gm2_df.columns:
        iso_cal = pd.to_datetime(dema_gm2_df['Days']).dt.isocalendar()
        dema_gm2_df['iso_week'] = iso_cal['year'].astype(str) + '-' + iso_cal['week'].astype(str).str.zfill(2)
    
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
            week_qlik_df = qlik_df[qlik_df['iso_week'] == week_str].copy()
            week_dema_df = dema_df[dema_df['iso_week'] == week_str].copy()
            week_dema_gm2_df = dema_gm2_df[dema_gm2_df['iso_week'] == week_str].copy()
            
            if week_qlik_df.empty or week_dema_df.empty or week_dema_gm2_df.empty:
                logger.warning(f"Missing data for week {week_str}")
                continue
            
            # Calculate contribution per new customer per country
            week_data = calculate_contribution_new_per_country_for_week(
                week_qlik_df,
                week_dema_df,
                week_dema_gm2_df,
                week_str
            )
            
            # Get last year data
            last_year = target_year - 1
            last_year_week_str = f"{last_year}-{target_week_num:02d}"
            
            try:
                last_year_qlik_df = qlik_df[qlik_df['iso_week'] == last_year_week_str].copy()
                last_year_dema_df = dema_df[dema_df['iso_week'] == last_year_week_str].copy()
                last_year_dema_gm2_df = dema_gm2_df[dema_gm2_df['iso_week'] == last_year_week_str].copy()
                
                if not last_year_qlik_df.empty and not last_year_dema_df.empty and not last_year_dema_gm2_df.empty:
                    last_year_data = calculate_contribution_new_per_country_for_week(
                        last_year_qlik_df,
                        last_year_dema_df,
                        last_year_dema_gm2_df,
                        last_year_week_str
                    )
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

