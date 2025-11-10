"""Weekly Reports combined PDF builder using ReportLab.

Generates a single PDF that aggregates key Weekly Reports sections with actual tables.
"""

from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.lib.colors import HexColor

from weekly_report.src.config import Config
from weekly_report.src.periods.calculator import get_week_date_range
from loguru import logger


def format_number(value: Any, metric_key: str = None, decimals: int = 0) -> str:
    """Format number matching frontend format (thousands for most metrics, integers for customers)."""
    if value is None or (isinstance(value, float) and (value != value)):  # NaN check
        return '-'
    try:
        num = float(value)
        
        # Customer counts should NOT be formatted in thousands
        if metric_key in ['returning_customers', 'new_customers']:
            return f"{int(round(num)):,}".replace(',', ' ')
        
        # Percentage metrics
        if metric_key in ['return_rate_pct', 'online_cost_of_sale_3']:
            return f"{num:.1f}%"
        
        if num == 0:
            return '0'
        
        # Convert to thousands and round to nearest integer (matching frontend)
        thousands_value = num / 1000
        rounded_thousands = int(round(thousands_value))
        
        # Format with Swedish locale (space as thousand separator)
        return f"{rounded_thousands:,}".replace(',', ' ')
    except (ValueError, TypeError):
        return str(value)


def format_percentage(value: Any) -> str:
    """Format percentage with 1 decimal."""
    if value is None or (isinstance(value, float) and (value != value)):
        return '-'
    try:
        return f"{float(value):.1f}%"
    except (ValueError, TypeError):
        return str(value)


def format_growth_percentage(current: float, previous: float) -> str:
    """Format growth percentage matching frontend format (negative in parentheses)."""
    if previous == 0 or current is None or previous is None:
        return '-'
    try:
        growth = ((current - previous) / previous) * 100
        abs_value = abs(growth)
        formatted = f"{abs_value:.1f}"
        
        if growth < 0:
            return f"({formatted}%)"
        else:
            return f"{formatted}%"
    except (ValueError, TypeError, ZeroDivisionError):
        return '-'


def create_table_style() -> TableStyle:
    """Create standard table style for Weekly Reports."""
    return TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#FFF9E6')),  # Light yellow
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#1f2937')),  # Dark gray
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        
        # Data row styling
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#FFFFFF')),
        ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#1f2937')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # First column left
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),  # Numbers right
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        
        # Borders
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
        ('LINEBELOW', (0, 0), (-1, 0), 1, HexColor('#999999')),
        
        # Row striping
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#F5F5F5'), HexColor('#FFFFFF')]),
    ])


def build_summary_table(metrics: Dict[str, Dict[str, Any]], periods: Dict[str, Any] = None) -> Table:
    """Build Summary (Table 1) table matching frontend MetricsPreview exactly."""
    if not metrics or not isinstance(metrics, dict):
        logger.warning(f"Invalid metrics structure for summary table: {type(metrics)}")
        return None
    
    metric_labels = [
        'Online Gross Revenue', 'Returns', 'Return Rate %', 'Online Net Revenue',
        'Retail Concept Store', 'Retail Pop-ups, Outlets', 'Retail Net Revenue',
        'Wholesale Net Revenue', 'Total Net Revenue', 'Returning Customers',
        'New customers', 'Marketing Spend', 'Online Cost of Sale(3)'
    ]
    metric_keys = [
        'online_gross_revenue', 'returns', 'return_rate_pct', 'online_net_revenue',
        'retail_concept_store', 'retail_popups_outlets', 'retail_net_revenue',
        'wholesale_net_revenue', 'total_net_revenue', 'returning_customers',
        'new_customers', 'marketing_spend', 'online_cost_of_sale_3'
    ]
    
    # Get date range for latest week
    latest_week_display = 'N/A'
    if periods and isinstance(periods, dict):
        date_ranges = periods.get('date_ranges', {})
        actual_range = date_ranges.get('actual', {})
        latest_week_display = actual_range.get('display', 'N/A')
    
    # Build multi-row header matching frontend exactly
    # Row 1: Main header
    header_row1 = ['(SEK \'000)']
    header_row1.extend([''] * 6)  # Placeholder for Latest Week section (7 cols total)
    header_row1.extend([''] * 5)   # Placeholder for Year-to-date section (5 cols)
    
    # Row 2: Section headers
    header_row2 = ['']  # Empty first cell
    header_row2.append('Latest Week: ' + latest_week_display)  # Spans 7 columns
    header_row2.extend([''] * 5)  # Rest of Latest Week section
    header_row2.append('Year-to-date')  # Spans 5 columns
    header_row2.extend([''] * 3)  # Rest of YTD section
    
    # Row 3: Column headers
    header_row3 = ['Metric', 'Actual', 'Last Week', 'Last Year', '2023',
                   'vs Last Week', 'vs Last Year', 'vs 2023',
                   'YTD Actual', 'YTD Last Year', 'YTD 2023',
                   'YTD vs Last Year', 'YTD vs 2023']
    
    table_data = [header_row1, header_row2, header_row3]
    
    # Build data rows
    for label, key in zip(metric_labels, metric_keys):
        row = [label]
        
        # Latest Week columns
        actual_value = metrics.get('actual', {}).get(key, 0) if isinstance(metrics.get('actual'), dict) else 0
        last_week_value = metrics.get('last_week', {}).get(key, 0) if isinstance(metrics.get('last_week'), dict) else 0
        last_year_value = metrics.get('last_year', {}).get(key, 0) if isinstance(metrics.get('last_year'), dict) else 0
        year_2023_value = metrics.get('year_2023', {}).get(key, 0) if isinstance(metrics.get('year_2023'), dict) else 0
        
        row.append(format_number(actual_value, key))  # Actual
        row.append(format_number(last_week_value, key))  # Last Week
        row.append(format_number(last_year_value, key))  # Last Year
        row.append(format_number(year_2023_value, key))  # 2023
        row.append(format_growth_percentage(actual_value, last_week_value))  # vs Last Week
        row.append(format_growth_percentage(actual_value, last_year_value))  # vs Last Year
        row.append(format_growth_percentage(actual_value, year_2023_value))  # vs 2023
        
        # YTD columns
        ytd_actual_value = metrics.get('ytd_actual', {}).get(key, 0) if isinstance(metrics.get('ytd_actual'), dict) else 0
        ytd_last_year_value = metrics.get('ytd_last_year', {}).get(key, 0) if isinstance(metrics.get('ytd_last_year'), dict) else 0
        ytd_2023_value = metrics.get('ytd_2023', {}).get(key, 0) if isinstance(metrics.get('ytd_2023'), dict) else 0
        
        row.append(format_number(ytd_actual_value, key))  # YTD Actual
        row.append(format_number(ytd_last_year_value, key))  # YTD Last Year
        row.append(format_number(ytd_2023_value, key))  # YTD 2023
        row.append(format_growth_percentage(ytd_actual_value, ytd_last_year_value))  # YTD vs Last Year
        row.append(format_growth_percentage(ytd_actual_value, ytd_2023_value))  # YTD vs 2023
        
        table_data.append(row)
    
    if len(table_data) <= 3:  # Only headers
        return None
    
    # Calculate column widths (landscape A4: ~280mm width, minus margins)
    available_width = 240 * mm  # Approximate width after margins
    col_widths = [
        50 * mm,  # Metric
        18 * mm,  # Actual
        18 * mm,  # Last Week
        18 * mm,  # Last Year
        18 * mm,  # 2023
        18 * mm,  # vs Last Week
        18 * mm,  # vs Last Year
        18 * mm,  # vs 2023
        18 * mm,  # YTD Actual
        18 * mm,  # YTD Last Year
        18 * mm,  # YTD 2023
        18 * mm,  # YTD vs Last Year
        18 * mm,  # YTD vs 2023
    ]
    
    table = Table(table_data, colWidths=col_widths)
    
    # Create table style matching frontend exactly
    style = TableStyle([
        # Row 1 header (spans all columns)
        ('SPAN', (0, 0), (0, 2)),  # (SEK '000) spans 3 rows
        ('SPAN', (1, 0), (7, 0)),  # "Latest Week:" spans 7 columns
        ('SPAN', (8, 0), (12, 0)),  # "Year-to-date" spans 5 columns
        ('BACKGROUND', (1, 0), (7, 0), HexColor('#F3F4F6')),  # Gray background for Latest Week
        ('BACKGROUND', (8, 0), (12, 0), HexColor('#DBEAFE')),  # Blue background for YTD
        ('ALIGN', (1, 0), (7, 0), 'CENTER'),
        ('ALIGN', (8, 0), (12, 0), 'CENTER'),
        ('FONTNAME', (1, 0), (12, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (1, 0), (12, 0), 9),
        
        # Row 2 section headers
        ('BACKGROUND', (1, 1), (7, 1), HexColor('#F3F4F6')),  # Gray
        ('BACKGROUND', (8, 1), (12, 1), HexColor('#DBEAFE')),  # Blue
        ('ALIGN', (1, 1), (12, 1), 'CENTER'),
        ('FONTNAME', (1, 1), (12, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (1, 1), (12, 1), 9),
        
        # Row 3 column headers
        ('BACKGROUND', (0, 2), (-1, 2), HexColor('#E5E7EB')),  # Gray background
        ('TEXTCOLOR', (0, 2), (-1, 2), HexColor('#1f2937')),  # Dark gray text
        ('ALIGN', (0, 2), (0, 2), 'LEFT'),  # Metric column left
        ('ALIGN', (1, 2), (-1, 2), 'RIGHT'),  # All other columns right
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 2), (-1, 2), 8),
        ('BOTTOMPADDING', (0, 2), (-1, 2), 4),
        ('TOPPADDING', (0, 2), (-1, 2), 4),
        
        # Actual column (col 1) - gray background, bold
        ('BACKGROUND', (1, 2), (1, -1), HexColor('#E5E7EB')),
        ('FONTNAME', (1, 3), (1, -1), 'Helvetica-Bold'),
        
        # YTD Actual column (col 8) - blue background, bold
        ('BACKGROUND', (8, 2), (8, -1), HexColor('#DBEAFE')),
        ('FONTNAME', (8, 3), (8, -1), 'Helvetica-Bold'),
        
        # YTD other columns (cols 9-12) - light blue background
        ('BACKGROUND', (9, 2), (12, -1), HexColor('#EFF6FF')),
        
        # Data rows
        ('TEXTCOLOR', (0, 3), (-1, -1), HexColor('#1f2937')),
        ('FONTNAME', (0, 3), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 3), (-1, -1), 8),
        ('ALIGN', (0, 3), (0, -1), 'LEFT'),  # Metric column left
        ('ALIGN', (1, 3), (-1, -1), 'RIGHT'),  # All other columns right
        ('BOTTOMPADDING', (0, 3), (-1, -1), 3),
        ('TOPPADDING', (0, 3), (-1, -1), 3),
        
        # Borders
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#E5E7EB')),
        ('LINEBELOW', (0, 2), (-1, 2), 1, HexColor('#9CA3AF')),  # Border below header
        
        # Row striping (alternating)
        ('ROWBACKGROUNDS', (0, 3), (-1, -1), [HexColor('#FFFFFF'), HexColor('#F9FAFB')]),
    ])
    
    table.setStyle(style)
    return table


def build_markets_table(markets_data: Dict[str, Any], period_info: Dict[str, Any] = None) -> Table:
    """Build Top Markets table matching frontend TopMarketsTable exactly."""
    if 'markets' not in markets_data or not markets_data['markets']:
        return None
    
    markets_list = markets_data['markets']
    if not markets_list or len(markets_list) == 0:
        return None
    
    # Get week keys from first market (should have weeks dict)
    if 'weeks' not in markets_list[0]:
        return None
    
    all_week_keys = sorted(markets_list[0]['weeks'].keys())
    # Filter to only show 2025 weeks (current year) - matching frontend
    week_keys = [w for w in all_week_keys if w.startswith('2025')]
    
    if not week_keys:
        return None
    
    # Calculate last year weeks (same week numbers, previous year)
    last_year_weeks = []
    for week in week_keys:
        year, week_num = week.split('-')
        last_year_weeks.append(f"{int(year) - 1}-{week_num}")
    
    # Get latest dates from period_info
    latest_dates = 'N/A'
    if period_info and isinstance(period_info, dict):
        latest_dates = period_info.get('latest_dates', 'N/A')
    
    # Helper to get week number (e.g., "2025-44" -> "44")
    def get_week_number(week_str: str) -> str:
        parts = week_str.split('-')
        return parts[1] if len(parts) > 1 else week_str
    
    # Helper to format value (thousands)
    def format_value(val: float) -> str:
        if val == 0:
            return '0'
        thousands = val / 1000
        rounded = int(round(thousands))
        return f"{rounded:,}".replace(',', ' ')
    
    # Helper to calculate YoY
    def calculate_yoy(current: float, previous: float) -> float:
        if previous == 0:
            return None
        return ((current - previous) / previous) * 100
    
    # Helper to format YoY
    def format_yoy(value: float) -> str:
        if value is None:
            return '-'
        abs_val = abs(value)
        rounded = int(round(abs_val))
        if value < 0:
            return f"({rounded}%)"
        return f"{rounded}%"
    
    # Helper to calculate SoB (Share of Business)
    def calculate_sob(market_val: float, total_val: float) -> float:
        if total_val == 0:
            return None
        return (market_val / total_val) * 100
    
    # Helper to format SoB
    def format_sob(value: float) -> str:
        if value is None:
            return '-'
        return f"{int(round(value))}%"
    
    # Find Total row for SoB calculations
    total_row = next((m for m in markets_list if m.get('country') == 'Total'), None)
    total_weeks = total_row.get('weeks', {}) if total_row else {}
    
    # Build multi-row header matching frontend exactly
    # Row 1: Main header with section spans
    header_row1 = ['Country']  # Country spans 3 rows
    header_row1.append('Latest Week: ' + str(latest_dates))  # Spans all weeks in Latest Week section
    header_row1.extend([''] * (len(week_keys) - 1))  # Rest of Latest Week section (weeks)
    header_row1.append('')  # Avg column (spans 2 rows)
    header_row1.append('Y/Y GROWTH%')  # Spans all weeks in Y/Y GROWTH% section
    header_row1.extend([''] * (len(week_keys) - 1))  # Rest of Y/Y GROWTH% section (weeks)
    header_row1.append('')  # Avg column (spans 2 rows)
    header_row1.append('SoB')  # Spans all weeks in SoB section
    header_row1.extend([''] * (len(week_keys) - 1))  # Rest of SoB section (weeks)
    header_row1.append('')  # Avg column (spans 2 rows)
    
    # Row 2: Section headers (empty for Country, section names for spans)
    header_row2 = ['']  # Country cell (spans 3 rows total)
    # Latest Week section - all empty except first cell already has text
    header_row2.extend([''] * len(week_keys))  # Week columns
    header_row2.append('')  # Avg column
    # Y/Y GROWTH% section - all empty except first cell already has text
    header_row2.extend([''] * len(week_keys))  # Week columns
    header_row2.append('')  # Avg column
    # SoB section - all empty except first cell already has text
    header_row2.extend([''] * len(week_keys))  # Week columns
    header_row2.append('')  # Avg column
    
    # Row 3: Column headers
    header_row3 = ['Country']
    # Latest Week columns
    for week in week_keys:
        header_row3.append(get_week_number(week))
    header_row3.append('Avg')
    # Y/Y GROWTH% columns
    for week in week_keys:
        header_row3.append(get_week_number(week))
    header_row3.append('Avg')
    # SoB columns
    for week in week_keys:
        header_row3.append(get_week_number(week))
    header_row3.append('Avg')
    
    table_data = [header_row1, header_row2, header_row3]
    
    # Build data rows
    for market in markets_list:
        country = market.get('country', '')
        weeks_dict = market.get('weeks', {})
        avg = market.get('average', 0)
        
        is_row = country == 'ROW'
        is_total = country == 'Total'
        
        row = [country]
        
        # Latest Week columns
        for week in week_keys:
            week_val = weeks_dict.get(week, 0)
            row.append(format_value(week_val))
        row.append(format_value(avg))
        
        # Y/Y GROWTH% columns
        for week, last_year_week in zip(week_keys, last_year_weeks):
            current_val = weeks_dict.get(week, 0)
            last_year_val = weeks_dict.get(last_year_week, 0)
            yoy = calculate_yoy(current_val, last_year_val)
            row.append(format_yoy(yoy))
        
        # Average YoY
        total_yoy = 0
        valid_weeks = 0
        for week, last_year_week in zip(week_keys, last_year_weeks):
            current_val = weeks_dict.get(week, 0)
            last_year_val = weeks_dict.get(last_year_week, 0)
            yoy = calculate_yoy(current_val, last_year_val)
            if yoy is not None:
                total_yoy += yoy
                valid_weeks += 1
        avg_yoy = total_yoy / valid_weeks if valid_weeks > 0 else None
        row.append(format_yoy(avg_yoy))
        
        # SoB columns
        for week in week_keys:
            market_val = weeks_dict.get(week, 0)
            total_val = total_weeks.get(week, 0) if total_weeks else 0
            if is_total:
                sob = 100
            else:
                sob = calculate_sob(market_val, total_val)
            row.append(format_sob(sob))
        
        # Average SoB
        if is_total:
            avg_sob = 100
        else:
            total_market_val = sum(weeks_dict.get(week, 0) for week in week_keys)
            total_total_val = sum(total_weeks.get(week, 0) for week in week_keys) if total_weeks else 0
            avg_sob = calculate_sob(total_market_val, total_total_val) if total_total_val > 0 else None
        row.append(format_sob(avg_sob))
        
        table_data.append(row)
    
    if len(table_data) <= 3:  # Only headers
        return None
    
    # Calculate column widths (landscape A4: ~280mm width, minus margins)
    num_weeks = len(week_keys)
    available_width = 240 * mm  # Approximate width after margins
    week_col_width = 12 * mm  # Each week column
    country_col_width = 40 * mm  # Country column
    avg_col_width = 15 * mm  # Avg column
    
    col_widths = [country_col_width]
    # Latest Week columns
    for _ in week_keys:
        col_widths.append(week_col_width)
    col_widths.append(avg_col_width)
    # Y/Y GROWTH% columns
    for _ in week_keys:
        col_widths.append(week_col_width)
    col_widths.append(avg_col_width)
    # SoB columns
    for _ in week_keys:
        col_widths.append(week_col_width)
    col_widths.append(avg_col_width)
    
    table = Table(table_data, colWidths=col_widths)
    
    # Create table style matching frontend exactly
    style = TableStyle([
        # Row 1 header (spans all columns)
        ('SPAN', (0, 0), (0, 2)),  # Country spans 3 rows
        ('SPAN', (1, 0), (num_weeks, 0)),  # "Latest Week:" spans all week columns
        ('SPAN', (num_weeks + 1, 0), (num_weeks + 1, 1)),  # Avg column spans 2 rows
        ('SPAN', (num_weeks + 2, 0), (num_weeks * 2 + 1, 0)),  # "Y/Y GROWTH%" spans all week columns
        ('SPAN', (num_weeks * 2 + 2, 0), (num_weeks * 2 + 2, 1)),  # Avg column spans 2 rows
        ('SPAN', (num_weeks * 2 + 3, 0), (num_weeks * 3 + 2, 0)),  # "SoB" spans all week columns
        ('SPAN', (num_weeks * 3 + 3, 0), (num_weeks * 3 + 3, 1)),  # Avg column spans 2 rows
        
        ('BACKGROUND', (1, 0), (num_weeks, 0), HexColor('#F3F4F6')),  # Gray for Latest Week
        ('BACKGROUND', (num_weeks + 1, 0), (num_weeks + 1, 1), HexColor('#DBEAFE')),  # Blue for Avg
        ('BACKGROUND', (num_weeks + 2, 0), (num_weeks * 2 + 1, 0), HexColor('#FEF3C7')),  # Yellow for Y/Y GROWTH%
        ('BACKGROUND', (num_weeks * 2 + 2, 0), (num_weeks * 2 + 2, 1), HexColor('#FEF3C7')),  # Yellow for Avg
        ('BACKGROUND', (num_weeks * 2 + 3, 0), (num_weeks * 3 + 2, 0), HexColor('#D1FAE5')),  # Green for SoB
        ('BACKGROUND', (num_weeks * 3 + 3, 0), (num_weeks * 3 + 3, 1), HexColor('#D1FAE5')),  # Green for Avg
        
        ('ALIGN', (1, 0), (num_weeks, 0), 'CENTER'),  # Latest Week header
        ('ALIGN', (num_weeks + 2, 0), (num_weeks * 2 + 1, 0), 'CENTER'),  # Y/Y GROWTH% header
        ('ALIGN', (num_weeks * 2 + 3, 0), (num_weeks * 3 + 2, 0), 'CENTER'),  # SoB header
        ('FONTNAME', (1, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (1, 0), (-1, 0), 9),
        
        # Row 2 section headers (empty cells, already styled)
        ('BACKGROUND', (1, 1), (num_weeks, 1), HexColor('#F3F4F6')),  # Gray
        ('BACKGROUND', (num_weeks + 1, 1), (num_weeks + 1, 1), HexColor('#DBEAFE')),  # Blue for Avg
        ('BACKGROUND', (num_weeks + 2, 1), (num_weeks * 2 + 1, 1), HexColor('#FEF3C7')),  # Yellow
        ('BACKGROUND', (num_weeks * 2 + 2, 1), (num_weeks * 2 + 2, 1), HexColor('#FEF3C7')),  # Yellow for Avg
        ('BACKGROUND', (num_weeks * 2 + 3, 1), (num_weeks * 3 + 2, 1), HexColor('#D1FAE5')),  # Green
        ('BACKGROUND', (num_weeks * 3 + 3, 1), (num_weeks * 3 + 3, 1), HexColor('#D1FAE5')),  # Green for Avg
        
        # Row 3 column headers
        
        ('BACKGROUND', (0, 2), (-1, 2), HexColor('#E5E7EB')),  # Gray background
        ('TEXTCOLOR', (0, 2), (-1, 2), HexColor('#1f2937')),  # Dark gray text
        ('ALIGN', (0, 2), (0, 2), 'LEFT'),  # Country column left
        ('ALIGN', (1, 2), (-1, 2), 'RIGHT'),  # All other columns right
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 2), (-1, 2), 8),
        ('BOTTOMPADDING', (0, 2), (-1, 2), 4),
        ('TOPPADDING', (0, 2), (-1, 2), 4),
        
        # Latest Week Avg column - blue background
        ('BACKGROUND', (num_weeks + 1, 2), (num_weeks + 1, -1), HexColor('#DBEAFE')),
        ('FONTNAME', (num_weeks + 1, 3), (num_weeks + 1, -1), 'Helvetica-Bold'),
        
        # Y/Y GROWTH% columns - yellow background
        ('BACKGROUND', (num_weeks + 2, 2), (num_weeks * 2 + 1, -1), HexColor('#FEF3C7')),
        ('BACKGROUND', (num_weeks * 2 + 2, 2), (num_weeks * 2 + 2, -1), HexColor('#FEF3C7')),
        ('FONTNAME', (num_weeks * 2 + 2, 3), (num_weeks * 2 + 2, -1), 'Helvetica-Bold'),
        
        # SoB columns - green background
        ('BACKGROUND', (num_weeks * 2 + 3, 2), (num_weeks * 3 + 2, -1), HexColor('#D1FAE5')),
        ('BACKGROUND', (num_weeks * 3 + 3, 2), (num_weeks * 3 + 3, -1), HexColor('#D1FAE5')),
        ('FONTNAME', (num_weeks * 3 + 3, 3), (num_weeks * 3 + 3, -1), 'Helvetica-Bold'),
        
        # ROW and Total row styling
        # ROW rows - gray background
        # Total rows - gray background, bold
        
        # Data rows
        ('TEXTCOLOR', (0, 3), (-1, -1), HexColor('#1f2937')),
        ('FONTNAME', (0, 3), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 3), (-1, -1), 8),
        ('ALIGN', (0, 3), (0, -1), 'LEFT'),  # Country column left
        ('ALIGN', (1, 3), (-1, -1), 'RIGHT'),  # All other columns right
        ('BOTTOMPADDING', (0, 3), (-1, -1), 3),
        ('TOPPADDING', (0, 3), (-1, -1), 3),
        
        # Borders
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#E5E7EB')),
        ('LINEBELOW', (0, 2), (-1, 2), 1, HexColor('#9CA3AF')),  # Border below header
        
        # Row striping (alternating)
        ('ROWBACKGROUNDS', (0, 3), (-1, -1), [HexColor('#FFFFFF'), HexColor('#F9FAFB')]),
    ])
    
    # Apply ROW and Total row styling
    for row_idx in range(3, len(table_data)):
        country = table_data[row_idx][0]
        if country == 'ROW':
            # Gray background for ROW
            style.add('BACKGROUND', (0, row_idx), (-1, row_idx), HexColor('#F3F4F6'))
        elif country == 'Total':
            # Darker gray background and bold for Total
            style.add('BACKGROUND', (0, row_idx), (-1, row_idx), HexColor('#E5E7EB'))
            style.add('FONTNAME', (0, row_idx), (-1, row_idx), 'Helvetica-Bold')
            style.add('FONTNAME', (0, row_idx), (0, row_idx), 'Helvetica-Bold')  # Country column bold
    
    table.setStyle(style)
    return table


def build_kpis_table(kpis_data: Dict[str, Any]) -> Table:
    """Build Online KPIs table."""
    # Handle both formats: direct list or dict with 'kpis' key
    if isinstance(kpis_data, list):
        kpis_list = kpis_data
    elif 'kpis' in kpis_data and kpis_data['kpis']:
        kpis_list = kpis_data['kpis']
    else:
        return None
    
    if not kpis_list or len(kpis_list) == 0:
        return None
    
    # Use the latest week (last in list)
    latest_kpis = kpis_list[-1] if kpis_list else {}
    
    header = ['Metric', 'Value']
    table_data = [header]
    
    kpi_fields = {
        'AOV New Customer': 'aov_new_customer',
        'AOV Returning Customer': 'aov_returning_customer',
        'COS (%)': 'cos',
        'Marketing Spend': 'marketing_spend',
        'Conversion Rate (%)': 'conversion_rate',
        'New Customers': 'new_customers',
        'Returning Customers': 'returning_customers',
        'Sessions': 'sessions',
        'New Customer CAC': 'new_customer_cac',
        'Total Orders': 'total_orders'
    }
    
    for label, key in kpi_fields.items():
        value = latest_kpis.get(key, 0)
        if 'rate' in key.lower() or 'cos' in key.lower():
            formatted = format_percentage(value)
        else:
            formatted = format_number(value)
        table_data.append([label, formatted])
    
    table = Table(table_data, colWidths=[120*mm, 60*mm])
    table.setStyle(create_table_style())
    return table


def build_weekly_reports_pdf(
    batch_metrics: Dict[str, Any],
    config: Config,
) -> Path:
    """Build a combined Weekly Reports PDF from batch metrics.

    Args:
        batch_metrics: The BatchMetricsResponse-like dict (periods, markets, kpis, etc.)
        config: Loaded Config for the base week

    Returns:
        Path to the generated PDF file
    """
    logger.info(f"Building Weekly Reports PDF for week {config.week}")

    output_path = config.reports_path / f"weekly_reports_{config.week}.pdf"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Landscape A4
    page_width, page_height = A4
    page_width, page_height = page_height, page_width

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=(page_width, page_height),
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        alignment=TA_CENTER,
        fontSize=22,
        textColor=HexColor("#1f2937"),
        spaceAfter=20,
        fontName='Helvetica-Bold'
    )
    h2_style = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        alignment=TA_LEFT,
        fontSize=16,
        textColor=HexColor("#111827"),
        spaceAfter=12,
        spaceBefore=15,
        fontName='Helvetica-Bold'
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=9,
        textColor=HexColor("#374151"),
        spaceAfter=8,
    )

    story = []
    
    # Cover page
    story.append(Paragraph(f"Weekly Reports", title_style))
    story.append(Spacer(1, 20))
    
    try:
        date_range = get_week_date_range(config.week)
        period_display = date_range.get('display', config.week)
    except Exception:
        period_display = config.week
    
    story.append(Paragraph(f"Week {config.week}", body_style))
    story.append(Paragraph(f"{period_display}", body_style))
    story.append(PageBreak())

    # Get periods from batch_metrics for date ranges
    periods_data = batch_metrics.get("periods", {})
    
    # 1. Summary (Table 1)
    if "metrics" in batch_metrics and batch_metrics["metrics"]:
        try:
            story.append(Paragraph("Summary (Table 1)", h2_style))
            metrics_data = batch_metrics["metrics"]
            # Ensure metrics_data is a dict with period keys
            if not isinstance(metrics_data, dict):
                logger.warning(f"metrics_data is not a dict: {type(metrics_data)}")
                metrics_data = {}
            # Validate that we have at least one period
            if not any(key in metrics_data for key in ['actual', 'last_week', 'last_year', 'year_2023']):
                logger.warning(f"metrics_data missing period keys, available keys: {list(metrics_data.keys())}")
            summary_table = build_summary_table(metrics_data, periods_data)
            if summary_table:
                story.append(summary_table)
                story.append(Spacer(1, 15))
            else:
                logger.warning("build_summary_table returned None")
                story.append(Paragraph("Summary data not available", body_style))
        except Exception as e:
            logger.error(f"Error building summary table: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            story.append(Paragraph(f"Error building summary table: {str(e)}", body_style))

    # 2. Top Markets
    if "markets" in batch_metrics and batch_metrics["markets"]:
        try:
            story.append(Paragraph("Top Markets", h2_style))
            markets_data = batch_metrics["markets"]
            # Extract period_info if markets_data is a dict with period_info
            period_info = None
            if isinstance(markets_data, dict) and 'period_info' in markets_data:
                period_info = markets_data.get('period_info')
            
            markets_table = build_markets_table(markets_data, period_info)
            if markets_table:
                story.append(markets_table)
                story.append(Spacer(1, 15))
            else:
                logger.warning("build_markets_table returned None")
                story.append(Paragraph("Markets data not available", body_style))
        except Exception as e:
            logger.error(f"Error building markets table: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            story.append(Paragraph(f"Error building markets table: {str(e)}", body_style))

    # 3. Online KPIs
    if "kpis" in batch_metrics and batch_metrics["kpis"]:
        try:
            story.append(Paragraph("Online KPIs", h2_style))
            kpis_table = build_kpis_table(batch_metrics["kpis"])
            if kpis_table:
                story.append(kpis_table)
                story.append(Spacer(1, 15))
        except Exception as e:
            logger.error(f"Error building KPIs table: {e}")
            story.append(Paragraph(f"Error building KPIs table: {str(e)}", body_style))

    # 4. Contribution (simplified - show latest week if available)
    if "contribution" in batch_metrics and batch_metrics["contribution"]:
        story.append(Paragraph("Contribution", h2_style))
        contribution = batch_metrics["contribution"]
        if isinstance(contribution, list) and len(contribution) > 0:
            latest = contribution[-1]
            story.append(Paragraph(f"Week: {latest.get('week', 'N/A')}", body_style))
            story.append(Paragraph(f"New Customer Contribution: {format_number(latest.get('new_customer_contribution', 0))}", body_style))
            story.append(Paragraph(f"Returning Customer Contribution: {format_number(latest.get('returning_customer_contribution', 0))}", body_style))
        story.append(Spacer(1, 15))

    # 5. Gender Sales (simplified)
    if "gender_sales" in batch_metrics and batch_metrics["gender_sales"]:
        story.append(Paragraph("Gender Sales", h2_style))
        gender_sales = batch_metrics["gender_sales"]
        if isinstance(gender_sales, list) and len(gender_sales) > 0:
            latest = gender_sales[-1]
            story.append(Paragraph(f"Men: {format_number(latest.get('men_revenue', 0))}", body_style))
            story.append(Paragraph(f"Women: {format_number(latest.get('women_revenue', 0))}", body_style))
        story.append(Spacer(1, 15))

    # Add footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_CENTER,
        textColor=HexColor('#6B7280'),
    )
    generated_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"Generated on {generated_time} | Week {config.week}", footer_style))

    # Build PDF
    doc.build(story)
    logger.info(f"Successfully generated Weekly Reports PDF: {output_path}")
    return output_path
