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
            # Try semicolon separator first (common in European CSV files)
            try:
                df = pd.read_csv(file_path, sep=';', nrows=10000)
            except Exception:
                # Try comma separator
                try:
                    df = pd.read_csv(file_path, nrows=10000, quotechar='"')
                except Exception:
                    df = pd.read_csv(file_path, nrows=10000)
        
        # Remove quotes from column names if present
        df.columns = df.columns.str.strip('"').str.strip("'")
        
        logger.info(f"File {file_path.name} columns: {df.columns.tolist()}")
        
        # Determine date column based on file type
        date_column_map = {
            "qlik": "Date",
            "dema_spend": "Days",
            "dema_gm2": "Days",
            "shopify": "Day"
        }
        date_col = date_column_map.get(file_type)
        
        # Case-insensitive search for date column
        matching_cols = [col for col in df.columns if col.lower() == date_col.lower()]
        if not matching_cols:
            logger.warning(f"Column '{date_col}' not found in {file_path.name}. Available columns: {df.columns.tolist()}")
            return {
                "error": f"Expected date column '{date_col}' not found",
                "row_count": len(df)
            }
        
        # Use the actual column name (case-sensitive)
        date_col = matching_cols[0]
        
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
            # Try semicolon separator first
            try:
                full_df = pd.read_csv(file_path, sep=';')
            except Exception:
                # Try comma separator
                try:
                    full_df = pd.read_csv(file_path, quotechar='"')
                except Exception:
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

