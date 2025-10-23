"""Extract metadata from uploaded data files."""
import pandas as pd
from pathlib import Path
from typing import Dict, Any
from loguru import logger


def extract_file_metadata(file_path: Path, file_type: str) -> Dict[str, Any]:
    """
    Extract first date, last date, and row count from data file.
    
    Returns dict with: first_date, last_date, row_count, date_column_name
    """
    try:
        # Load file
        if file_path.suffix.lower() == '.xlsx':
            df = pd.read_excel(file_path, nrows=10000)  # Sample for speed
        else:
            df = pd.read_csv(file_path, nrows=10000)
        
        # Determine date column based on file type
        date_column_map = {
            "qlik": "Date",
            "dema_spend": "Days",
            "dema_gm2": "Days",
            "shopify": "Day"
        }
        date_col = date_column_map.get(file_type)
        
        if date_col not in df.columns:
            return {
                "error": f"Expected date column '{date_col}' not found",
                "row_count": len(df)
            }
        
        # Parse dates
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col])
        
        if len(df) == 0:
            return {
                "error": "No valid dates found in file",
                "row_count": 0
            }
        
        first_date = df[date_col].min().strftime('%Y-%m-%d')
        last_date = df[date_col].max().strftime('%Y-%m-%d')
        
        # Get full row count (not just sample)
        logger.info(f"Counting rows in {file_path.name}")
        if file_path.suffix.lower() == '.xlsx':
            full_df = pd.read_excel(file_path)
        else:
            full_df = pd.read_csv(file_path)
        row_count = len(full_df)
        
        return {
            "first_date": first_date,
            "last_date": last_date,
            "row_count": row_count,
            "date_column": date_col
        }
        
    except Exception as e:
        logger.error(f"Error extracting metadata from {file_path}: {e}")
        return {
            "error": str(e),
            "row_count": 0
        }

