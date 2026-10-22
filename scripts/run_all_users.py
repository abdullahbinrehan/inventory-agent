"""
This script runs the inventory pipeline for ALL users in the database.
It is designed to be run by GitHub Actions on a daily schedule.
"""
import sys
import os
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent.db import get_supabase_client
from agent.main import run_pipeline
from agent import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("run_all_users")

def main():
    logger.info("Starting global scheduler run...")
    try:
        supabase = get_supabase_client()
        response = supabase.table("user_configs").select("*").execute()
        users = response.data
        
        if not users:
            logger.info("No users found in database.")
            return

        logger.info(f"Found {len(users)} total users. Checking credentials...")
        
        success_count = 0
        for user in users:
            email = user.get("email")
            # Skip users who haven't connected Shopify yet
            if not user.get("shopify_url") or not user.get("shopify_client_id"):
                logger.info(f"Skipping {email} - No Shopify credentials configured.")
                continue
                
            logger.info(f"Running pipeline for {email}...")
            try:
                # Run the pipeline with the user's specific config
                summary = run_pipeline(user_config=user, source="shopify", dry_run=False, force=False)
                logger.info(f"Success for {email}: {summary}")
                success_count += 1
            except Exception as e:
                logger.error(f"Failed for {email}: {e}")
                
        logger.info(f"Global run complete. Successfully processed {success_count} users.")
        
    except Exception as e:
        logger.error(f"Global scheduler failed: {e}")

if __name__ == "__main__":
    main()