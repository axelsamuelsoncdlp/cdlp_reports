"""Utility to calculate file hashes for cache invalidation."""

import hashlib
from pathlib import Path
from typing import Dict, Optional
from loguru import logger


def calculate_file_hash(file_path: Path) -> Optional[str]:
    """
    Calculate MD5 hash of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        MD5 hash as hex string, or None if file doesn't exist or error occurs
    """
    if not file_path.exists():
        return None
    
    try:
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logger.warning(f"Failed to calculate hash for {file_path}: {e}")
        return None


def get_file_hashes_for_week(week: str, data_root: Path) -> Dict[str, str]:
    """
    Calculate MD5 hashes for all data files in a week's directory.
    
    Used for cache invalidation - if file hashes change, metrics need to be recomputed.
    
    Args:
        week: ISO week string like '2025-42'
        data_root: Root data directory (e.g., 'data')
        
    Returns:
        Dictionary mapping file_type to hash: {"qlik": "md5...", "dema_spend": "md5..."}
    """
    hashes = {}
    week_path = data_root / "raw" / week
    
    if not week_path.exists():
        logger.debug(f"Week directory does not exist: {week_path}")
        return hashes
    
    # File types to check
    file_types = ["qlik", "dema_spend", "dema_gm2", "shopify"]
    
    for file_type in file_types:
        type_path = week_path / file_type
        
        if not type_path.exists():
            continue
        
        # Find all non-hidden files in the directory
        files = [f for f in type_path.glob("*.*") if not f.name.startswith('.')]
        
        if files:
            # Use the most recently modified file (typically only one file per type)
            latest_file = max(files, key=lambda f: f.stat().st_mtime)
            file_hash = calculate_file_hash(latest_file)
            
            if file_hash:
                hashes[file_type] = file_hash
                logger.debug(f"File hash for {file_type}: {file_hash[:8]}... ({latest_file.name})")
    
    return hashes


def hashes_match(stored_hashes: Dict[str, str], current_hashes: Dict[str, str]) -> bool:
    """
    Check if stored file hashes match current file hashes.
    
    Args:
        stored_hashes: Hashes from Supabase (from previous computation)
        current_hashes: Current file hashes
        
    Returns:
        True if all hashes match, False otherwise
    """
    if not stored_hashes:
        return False
    
    if not current_hashes:
        return False
    
    # Check if all file types in stored_hashes are present and match
    for file_type, stored_hash in stored_hashes.items():
        if file_type not in current_hashes:
            logger.debug(f"File type {file_type} missing in current hashes")
            return False
        
        if current_hashes[file_type] != stored_hash:
            logger.debug(f"Hash mismatch for {file_type}: stored={stored_hash[:8]}... current={current_hashes[file_type][:8]}...")
            return False
    
    return True






