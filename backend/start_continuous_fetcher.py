#!/usr/bin/env python3
"""
Continuous Stock Fetcher - Startup Script
Run this to start continuous background fetching
"""
import asyncio
import logging
from app.services.continuous_fetcher import continuous_fetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def main():
    """Start the continuous fetcher"""
    logger.info("Starting Continuous Stock Fetcher...")
    
    try:
        await continuous_fetcher.run_continuous()
    except KeyboardInterrupt:
        logger.info("\n🛑 Stopping continuous fetcher...")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
