"""
Database layer using Supabase.
Handles fetching and saving user credentials.
"""

import os
import logging
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")

def get_supabase_client() -> Client:
    """Initialize and return the Supabase client."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Supabase URL or Key missing from environment.")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def get_user_config(email: str) -> dict | None:
    """Fetch a user's configuration by email."""
    try:
        supabase = get_supabase_client()
        response = supabase.table("user_configs").select("*").eq("email", email).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        logger.error("Failed to fetch user config: %s", e)
        return None

def save_user_config(email: str, data: dict) -> bool:
    """Insert or update a user's configuration."""
    try:
        supabase = get_supabase_client()
        data["email"] = email
        
        # Check if user exists
        existing = get_user_config(email)
        
        if existing:
            # Update
            supabase.table("user_configs").update(data).eq("email", email).execute()
        else:
            # Insert
            supabase.table("user_configs").insert(data).execute()
        return True
    except Exception as e:
        logger.error("Failed to save user config: %s", e)
        return False