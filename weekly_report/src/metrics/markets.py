"""Markets calculation module for top markets analysis."""

import pandas as pd
from typing import Dict, List, Any
from pathlib import Path
from loguru import logger

from weekly_report.src.adapters import qlik
from weekly_report.src.periods.calculator import get_week_date_range
from weekly_report.src.metrics.table1 import load_all_raw_data, filter_data_for_period


def calculate_top_markets_for_weeks(base_week: str, num_weeks: int, data_root: Path) -> Dict[str, Any]:
    """
    Calculate top markets based on average Online Gross Revenue over last N weeks.
    
    Args:
        base_week: ISO week format like '2025-42'
        num_weeks: Number of weeks to look back (default 8)
        data_root: Root data directory
        
    Returns:
        Dictionary with markets data and period info
    """
    
    logger.info(f"Calculating top markets for {num_weeks} weeks ending at {base_week}")
    
    # Parse base week
    match = base_week.split('-')
    year = int(match[0])
    week = int(match[1])
    
    # Generate list of weeks to analyze (current year)
    weeks_to_analyze = []
    for i in range(num_weeks):
        week_num = week - i
        if week_num < 1:
            # Need to go back to previous year
            prev_year = year - 1
            # Check if previous year had 53 weeks
            if _has_53_weeks(prev_year):
                week_num = 53 + week_num
            else:
                week_num = 52 + week_num
            weeks_to_analyze.append(f"{prev_year}-{week_num:02d}")
        else:
            weeks_to_analyze.append(f"{year}-{week_num:02d}")
    
    # Generate list of last year weeks (same week numbers, previous year)
    last_year_weeks = []
    for week_str in weeks_to_analyze:
        week_year, week_num = week_str.split('-')
        last_year_weeks.append(f"{int(week_year) - 1}-{week_num}")
    
    # Reverse to match order
    weeks_to_analyze = weeks_to_analyze[::-1]
    last_year_weeks = last_year_weeks[::-1]
    
    logger.info(f"Analyzing weeks: {weeks_to_analyze}")
    logger.info(f"Last year weeks: {last_year_weeks}")
    
    # Load all raw data for the base week
    base_week = weeks_to_analyze[0] if weeks_to_analyze else '2025-42'
    latest_data_path = data_root / "raw" / base_week
    
    try:
        logger.info(f"Loading raw data from {latest_data_path} for base week {base_week}")
        all_raw_data = load_all_raw_data(latest_data_path)
    except Exception as e:
        logger.error(f"Failed to load raw data: {e}")
        raise
    
    # Calculate revenue per country per week (both current and last year)
    country_weeks_data = {}
    
    all_weeks = list(set(weeks_to_analyze + last_year_weeks))
    logger.info(f"Processing {len(all_weeks)} weeks total: {all_weeks}")
    
    for week_str in all_weeks:
        try:
            # Filter data for this week
            filtered_data = filter_data_for_period(all_raw_data, week_str)
            qlik_df = filtered_data['qlik']
            
            # Group by Country and sum Online Gross Revenue
            if 'Country' in qlik_df.columns and 'Gross Revenue' in qlik_df.columns:
                country_revenue = qlik_df[
                    qlik_df['Sales Channel'] == 'Online'
                ].groupby('Country')['Gross Revenue'].sum()
                
                for country, revenue in country_revenue.items():
                    if country not in country_weeks_data:
                        country_weeks_data[country] = {}
                    country_weeks_data[country][week_str] = float(revenue)
                    
        except Exception as e:
            logger.warning(f"Failed to process week {week_str}: {e}")
            # Continue with other weeks
    
    # Calculate averages and sort (only for current year weeks)
    markets_list = []
    for country, weeks_data in country_weeks_data.items():
        # Calculate average only for current year weeks, including 0 for weeks without data
        current_year_values = [weeks_data.get(week, 0) for week in weeks_to_analyze]
        avg_revenue = sum(current_year_values) / len(weeks_to_analyze) if weeks_to_analyze else 0
        
        # Build weeks dict with both current and last year data
        combined_weeks = {}
        # Add current year weeks
        for week in weeks_to_analyze:
            combined_weeks[week] = weeks_data.get(week, 0)
        # Add last year weeks
        for week in last_year_weeks:
            combined_weeks[week] = weeks_data.get(week, 0)
        
        markets_list.append({
            'country': country,
            'weeks': combined_weeks,
            'average': avg_revenue
        })
    
    # Sort by average descending
    markets_list.sort(key=lambda x: x['average'], reverse=True)
    
    # Get top 13
    top_13 = markets_list[:13]
    
    # Calculate ROW (Rest of World) - sum of all others
    remaining_countries = markets_list[13:]
    row_weeks = {}
    row_total = 0
    
    # Include both current year and last year weeks for ROW
    for week_str in all_weeks:
        row_week_total = sum(c['weeks'].get(week_str, 0) for c in remaining_countries)
        row_weeks[week_str] = row_week_total
        if week_str in weeks_to_analyze:
            row_total += row_week_total
    
    row_average = row_total / len(weeks_to_analyze) if weeks_to_analyze else 0
    
    # Add ROW to markets list
    if row_average > 0:
        top_13.append({
            'country': 'ROW',
            'weeks': row_weeks,
            'average': row_average
        })
    
    # Calculate Total (sum of all countries including top 13 and ROW)
    total_weeks = {}
    total_sum = 0
    
    # Sum all countries for each week (use original markets_list to avoid double counting ROW)
    for week_str in all_weeks:
        week_total = sum(c['weeks'].get(week_str, 0) for c in markets_list)
        total_weeks[week_str] = week_total
        if week_str in weeks_to_analyze:
            total_sum += week_total
    
    # Calculate total average as average of the 8 weeks
    total_average = total_sum / len(weeks_to_analyze) if weeks_to_analyze else 0
    
    # Add Total to markets list
    top_13.append({
        'country': 'Total',
        'weeks': total_weeks,
        'average': total_average
    })
    
    # Get latest week date range for display
    latest_week = weeks_to_analyze[-1]  # Use last week instead of first
    date_range = get_week_date_range(latest_week)
    
    result = {
        'markets': top_13,
        'period_info': {
            'latest_week': latest_week,
            'latest_dates': date_range['display']
        }
    }
    
    logger.info(f"Calculated top markets: {len(top_13)} entries")
    return result


def _has_53_weeks(year: int) -> bool:
    """Check if a year has 53 ISO weeks."""
    from datetime import datetime
    
    jan_4 = datetime(year, 1, 4)
    return jan_4.weekday() >= 3

