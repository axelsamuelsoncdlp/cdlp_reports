"""Supabase client adapter for read-optimized data storage."""

import os
from typing import Optional

from loguru import logger

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not required if env vars are set externally


try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.warning("supabase-py not installed. Install with: pip install supabase")


def get_supabase_client() -> Optional['Client']:
    """Initialize Supabase client using environment variables."""
    if not SUPABASE_AVAILABLE:
        logger.error("Supabase client not available. Install supabase-py.")
        return None
    
    url = os.getenv("SUPABASE_URL")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not service_role_key:
        logger.error("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY environment variables")
        return None
    
    try:
        client = create_client(url, service_role_key)
        logger.info("Supabase client initialized successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        return None

