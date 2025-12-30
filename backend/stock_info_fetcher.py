"""
Standalone Stock Info Fetcher - Stores complete API responses in MongoDB
Fetches 1 stock per minute to respect API rate limits
Can be safely deleted after data collection is complete

Usage: python stock_info_fetcher.py
"""

import asyncio
import aiohttp
import logging
from datetime import datetime
from pymongo import MongoClient
from typing import Optional, Dict
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration - Use environment variables with defaults
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "VajOJ1XdN_Z1mpb3J2wws7pwn0qeKWNv")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB = os.getenv("MONGO_DB", "stock_analysis")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "stockinfo")
DELAY_BETWEEN_STOCKS = 60  # seconds (1 stock per minute)

# Target years to fetch
TARGET_YEARS = [2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017]

async def fetch_all_stock_symbols(api_key: str) -> list:
    """Fetch ALL available stock symbols from Polygon API (8,000+ stocks)"""
    logger.info("🔍 Fetching ALL stock symbols from Polygon API...")
    
    symbols = []
    next_url = f"https://api.polygon.io/v3/reference/tickers?market=stocks&active=true&limit=1000&apiKey={api_key}"
    
    async with aiohttp.ClientSession() as session:
        page = 1
        while next_url:
            try:
                logger.info(f"   Page {page}...")
                async with session.get(next_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract symbols from results
                        if 'results' in data:
                            page_symbols = [ticker['ticker'] for ticker in data['results'] if 'ticker' in ticker]
                            symbols.extend(page_symbols)
                            logger.info(f"   Page {page}: +{len(page_symbols)} symbols (Total: {len(symbols)})")
                        
                        # Check for next page
                        next_url = data.get('next_url')
                        if next_url:
                            # Add API key to next_url if not present
                            if 'apiKey=' not in next_url:
                                next_url = f"{next_url}&apiKey={api_key}"
                            page += 1
                            await asyncio.sleep(12.1)  # Rate limit: 5 calls/minute for free tier
                        else:
                            break
                    elif response.status == 429:
                        logger.warning(f"⚠️  Rate limited on page {page}, waiting 60 seconds...")
                        await asyncio.sleep(60)
                    else:
                        logger.error(f"❌ Failed to fetch symbols page {page}: HTTP {response.status}")
                        break
                        
            except Exception as e:
                logger.error(f"❌ Error fetching symbols page {page}: {e}")
                break
    
    logger.info(f"✅ Total symbols fetched: {len(symbols)}")
    return sorted(symbols)

class StockInfoFetcher:
    """Fetches complete stock information and stores in MongoDB"""
    
    def __init__(self):
        self.api_key = POLYGON_API_KEY
        self.mongo_client = MongoClient(MONGO_URI)
        self.db = self.mongo_client[MONGO_DB]
        self.collection = self.db[MONGO_COLLECTION]
        self.delay = DELAY_BETWEEN_STOCKS
        
        # Create indexes for efficient querying
        self.collection.create_index([("symbol", 1), ("year", 1), ("month", 1)], unique=True)
        self.collection.create_index([("symbol", 1)])
        self.collection.create_index([("year", 1)])
        self.collection.create_index([("fetched_at", -1)])
        
        logger.info(f"✅ Connected to MongoDB: {MONGO_DB}.{MONGO_COLLECTION}")
    
    async def fetch_company_details(self, symbol: str, session: aiohttp.ClientSession) -> Optional[Dict]:
        """Fetch company details from Polygon API"""
        try:
            url = f"https://api.polygon.io/v3/reference/tickers/{symbol}?apiKey={self.api_key}"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('results', {})
                else:
                    logger.warning(f"[{symbol}] Company details failed: HTTP {response.status}")
                    return None
        except Exception as e:
            logger.error(f"[{symbol}] Error fetching company details: {e}")
            return None
    
    async def fetch_financials(self, symbol: str, year: int, session: aiohttp.ClientSession) -> Optional[Dict]:
        """Fetch financial data for a specific year from Polygon API"""
        try:
            url = f"https://api.polygon.io/vX/reference/financials?ticker={symbol}&timeframe=annual&limit=10&apiKey={self.api_key}"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'results' not in data or not data['results']:
                        return None
                    
                    # Find the report for the requested year
                    for report in data['results']:
                        fiscal_year = report.get('fiscal_year')
                        if fiscal_year and str(fiscal_year) == str(year):
                            return report
                    
                    logger.warning(f"[{symbol}] No data for year {year}")
                    return None
                else:
                    logger.warning(f"[{symbol}] Financials failed: HTTP {response.status}")
                    return None
        except Exception as e:
            logger.error(f"[{symbol}] Error fetching financials: {e}")
            return None
    
    async def fetch_stock_info(self, symbol: str, year: int) -> bool:
        """Fetch complete stock information and store in MongoDB"""
        try:
            async with aiohttp.ClientSession() as session:
                # Fetch company details
                company_data = await self.fetch_company_details(symbol, session)
                if not company_data:
                    logger.warning(f"❌ [{symbol}] No company data available")
                    return False
                
                # Fetch financial data
                financial_data = await self.fetch_financials(symbol, year, session)
                if not financial_data:
                    logger.warning(f"❌ [{symbol}] No financial data for year {year}")
                    return False
                
                # Prepare document for MongoDB
                document = {
                    'symbol': symbol,
                    'year': year,
                    'month': None,  # Annual data
                    'company_name': company_data.get('name', symbol),
                    'company_details': company_data,  # Full company response
                    'financial_data': financial_data,  # Full financial response
                    'fiscal_year': financial_data.get('fiscal_year'),
                    'fiscal_period': financial_data.get('fiscal_period'),
                    'start_date': financial_data.get('start_date'),
                    'end_date': financial_data.get('end_date'),
                    'filing_date': financial_data.get('filing_date'),
                    'source': 'polygon',
                    'api_key_used': self.api_key[:10] + '...',  # Don't store full key
                    'fetched_at': datetime.utcnow()
                }
                
                # Upsert into MongoDB (insert or update if exists)
                result = self.collection.update_one(
                    {'symbol': symbol, 'year': year, 'month': None},
                    {'$set': document},
                    upsert=True
                )
                
                if result.upserted_id:
                    logger.info(f"✅ Inserted {symbol} ({year}) - New record")
                else:
                    logger.info(f"✅ Updated {symbol} ({year}) - Existing record")
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Error processing {symbol} ({year}): {e}")
            return False
    
    async def run_continuous(self):
        """Main loop - fetch stocks continuously"""
        logger.info("="*80)
        logger.info("🚀 STOCK INFO FETCHER STARTED")
        logger.info("="*80)
        
        # Fetch all available stock symbols from Polygon
        stock_symbols = await fetch_all_stock_symbols(self.api_key)
        
        logger.info(f"📊 Total symbols: {len(stock_symbols)}")
        logger.info(f"📅 Target years: {TARGET_YEARS}")
        logger.info(f"🎯 Total combinations: {len(stock_symbols) * len(TARGET_YEARS)}")
        logger.info(f"⏱️  Delay: {self.delay} seconds (1 stock per minute)")
        logger.info(f"💾 MongoDB: {MONGO_DB}.{MONGO_COLLECTION}")
        logger.info("="*80)
        
        total_fetched = 0
        total_failed = 0
        start_time = datetime.now()
        
        # Process each symbol and year
        for symbol in stock_symbols:
            for year in TARGET_YEARS:
                # Check if already exists
                existing = self.collection.find_one({
                    'symbol': symbol,
                    'year': year,
                    'month': None
                })
                
                if existing:
                    logger.info(f"⏭️  Skipping {symbol} ({year}) - Already exists")
                    continue
                
                # Fetch the stock info
                logger.info(f"📥 Fetching {symbol} for year {year}...")
                success = await self.fetch_stock_info(symbol, year)
                
                if success:
                    total_fetched += 1
                else:
                    total_failed += 1
                
                # Progress update every 10 stocks
                total_processed = total_fetched + total_failed
                if total_processed % 10 == 0:
                    elapsed = datetime.now() - start_time
                    rate = total_fetched / (elapsed.total_seconds() / 60) if elapsed.total_seconds() > 0 else 0
                    
                    logger.info("─"*80)
                    logger.info(f"📊 Progress: {total_fetched} fetched, {total_failed} failed")
                    logger.info(f"⏱️  Elapsed: {elapsed}")
                    logger.info(f"📈 Rate: {rate:.2f} stocks/minute")
                    logger.info("─"*80)
                
                # Wait before next fetch
                logger.info(f"⏳ Waiting {self.delay} seconds before next fetch...")
                await asyncio.sleep(self.delay)
        
        # Final summary
        elapsed = datetime.now() - start_time
        logger.info("="*80)
        logger.info("🎉 ALL STOCKS PROCESSED!")
        logger.info("="*80)
        logger.info(f"✅ Total fetched: {total_fetched}")
        logger.info(f"❌ Total failed: {total_failed}")
        logger.info(f"⏱️  Time elapsed: {elapsed}")
        logger.info("="*80)
        
        # Close MongoDB connection
        self.mongo_client.close()
        logger.info("✅ MongoDB connection closed")

async def main():
    """Main entry point"""
    try:
        fetcher = StockInfoFetcher()
        await fetcher.run_continuous()
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║         STOCK INFO FETCHER - MongoDB Storage                 ║
    ║                                                              ║
    ║  This script fetches complete stock information from        ║
    ║  Polygon API and stores it in MongoDB.                      ║
    ║                                                              ║
    ║  • Fetches 1 stock per minute                               ║
    ║  • Stores complete API responses                            ║
    ║  • Can be safely deleted after completion                   ║
    ║                                                              ║
    ║  Press Ctrl+C to stop at any time.                          ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(main())
