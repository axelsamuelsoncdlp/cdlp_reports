"""Period calculation module for ISO week handling."""

from datetime import datetime, timedelta
from typing import Dict
import re
from loguru import logger


def get_periods_for_week(iso_week: str) -> Dict[str, str]:
    """
    Calculate all periods for a given ISO week.
    
    Args:
        iso_week: ISO week format like '2025-42'
        
    Returns:
        Dictionary with period mappings:
        {
            'actual': '2025-42',
            'last_week': '2025-41', 
            'last_year': '2024-42',
            'year_2023': '2023-42'
        }
    """
    
    # Parse ISO week
    match = re.match(r'(\d{4})-(\d{1,2})', iso_week)
    if not match:
        raise ValueError(f"Invalid ISO week format: {iso_week}. Expected format: YYYY-WW")
    
    year = int(match.group(1))
    week = int(match.group(2))
    
    # Validate week number
    if week < 1 or week > 53:
        raise ValueError(f"Week number {week} is invalid. Must be between 1-53.")
    
    periods = {
        'actual': iso_week,
        'last_week': _get_previous_week(year, week),
        'last_year': f"{year-1}-{week:02d}",
        'year_2023': f"2023-{week:02d}"
    }
    
    logger.debug(f"Calculated periods for {iso_week}: {periods}")
    return periods


def _get_previous_week(year: int, week: int) -> str:
    """Get the previous ISO week."""
    
    if week > 1:
        return f"{year}-{week-1:02d}"
    else:
        # Week 1 -> previous year's last week
        # Check if previous year had 53 weeks
        prev_year = year - 1
        if _has_53_weeks(prev_year):
            return f"{prev_year}-53"
        else:
            return f"{prev_year}-52"


def _has_53_weeks(year: int) -> bool:
    """
    Check if a year has 53 ISO weeks.
    A year has 53 weeks if January 4th falls on a Thursday or later.
    """
    
    jan_4 = datetime(year, 1, 4)
    # Monday = 0, Tuesday = 1, ..., Thursday = 3, Friday = 4, Saturday = 5, Sunday = 6
    return jan_4.weekday() >= 3


def get_current_iso_week() -> str:
    """Get the current ISO week."""
    
    now = datetime.now()
    year, week, _ = now.isocalendar()
    return f"{year}-{week:02d}"


def get_week_date_range(iso_week: str) -> Dict[str, str]:
    """
    Get the date range (Monday-Sunday) for an ISO week.
    
    Args:
        iso_week: ISO week format like '2025-42'
        
    Returns:
        Dictionary with start and end dates:
        {
            'start': '2025-10-13',
            'end': '2025-10-19',
            'display': 'Oct 13th - Oct 19th'
        }
    """
    
    match = re.match(r'(\d{4})-(\d{1,2})', iso_week)
    if not match:
        raise ValueError(f"Invalid ISO week format: {iso_week}")
    
    year = int(match.group(1))
    week = int(match.group(2))
    
    # Get the Monday of the ISO week
    jan_4 = datetime(year, 1, 4)
    jan_4_weekday = jan_4.weekday()  # Monday = 0
    
    # Calculate the first Monday of the year
    first_monday = jan_4 - timedelta(days=jan_4_weekday)
    
    # Calculate the Monday of the target week
    target_monday = first_monday + timedelta(weeks=week-1)
    
    # Calculate the Sunday of the target week
    target_sunday = target_monday + timedelta(days=6)
    
    # Format dates
    start_date = target_monday.strftime('%Y-%m-%d')
    end_date = target_sunday.strftime('%Y-%m-%d')
    
    # Create display format
    start_display = target_monday.strftime('%b %d')
    end_display = target_sunday.strftime('%b %d')
    display = f"{start_display} - {end_display}"
    
    return {
        'start': start_date,
        'end': end_date,
        'display': display
    }


def validate_iso_week(iso_week: str) -> bool:
    """Validate if an ISO week string is valid."""
    
    try:
        match = re.match(r'(\d{4})-(\d{1,2})', iso_week)
        if not match:
            return False
        
        year = int(match.group(1))
        week = int(match.group(2))
        
        # Basic validation
        if year < 2000 or year > 2100:
            return False
        
        if week < 1 or week > 53:
            return False
        
        # Check if week 53 exists for this year
        if week == 53 and not _has_53_weeks(year):
            return False
        
        return True
        
    except (ValueError, AttributeError):
        return False


def get_ytd_periods_for_week(iso_week: str) -> Dict[str, Dict[str, str]]:
    """
    Calculate YTD periods from April 1st (Fiscal Year start) for a given ISO week.
    
    Args:
        iso_week: ISO week format like '2025-42'
        
    Returns:
        Dictionary with YTD period mappings:
        {
            'ytd_actual': {'start': '2025-04-01', 'end': '2025-10-19'},
            'ytd_last_year': {'start': '2024-04-01', 'end': '2024-10-19'},
            'ytd_2023': {'start': '2023-04-01', 'end': '2023-10-19'}
        }
    """
    
    match = re.match(r'(\d{4})-(\d{1,2})', iso_week)
    if not match:
        raise ValueError(f"Invalid ISO week format: {iso_week}")
    
    year = int(match.group(1))
    week = int(match.group(2))
    
    # Get the end date of the current week
    week_end = get_week_date_range(iso_week)['end']
    
    # Calculate YTD for current year (from April 1st)
    fy_start_current = f"{year}-04-01"
    
    # Calculate YTD for last year (same week in previous year)
    last_year_iso_week = f"{year-1}-{week:02d}"
    week_end_last_year = get_week_date_range(last_year_iso_week)['end']
    fy_start_last_year = f"{year-1}-04-01"
    
    # Calculate YTD for 2023 (same week in 2023)
    iso_week_2023 = f"2023-{week:02d}"
    week_end_2023 = get_week_date_range(iso_week_2023)['end']
    fy_start_2023 = "2023-04-01"
    
    periods = {
        'ytd_actual': {
            'start': fy_start_current,
            'end': week_end
        },
        'ytd_last_year': {
            'start': fy_start_last_year,
            'end': week_end_last_year
        },
        'ytd_2023': {
            'start': fy_start_2023,
            'end': week_end_2023
        }
    }
    
    logger.debug(f"Calculated YTD periods for {iso_week}: {periods}")
    return periods
