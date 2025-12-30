"""
Continuous Stock Fetcher - Respects Polygon API Rate Limits
Fetches 1 stock per minute = 60 stocks/hour = 1,440 stocks/day
Timeline: 1 WEEK to collect ~516 stocks x 8 years (2017-2024) = ~4,128 records
Strategy: Slow and steady to avoid hitting API rate limits
"""
import asyncio
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.database import SessionLocal, StockData
from app.services.stock_data_service import stock_data_service
from sqlalchemy import and_

logger = logging.getLogger(__name__)

class ContinuousFetcher:
    """
    Continuous stock fetcher - respects API rate limits
    Fetches stocks one at a time with delays between each
    """
    
    def __init__(self):
        self.target_years = [2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017]  # 8 years
        self.delay_between_stocks = 60  # 60 seconds = 1 minute (safe for Polygon 5/min limit)
        self.stocks_per_hour = 60
        self.stocks_per_day = 1440
        self.failed_attempts = {}  # Track failed stock+year combinations to avoid retrying
        
    def get_next_stock_to_fetch(self, db: Session) -> tuple:
        """
        Find the next stock+year combination that needs to be fetched
        Strategy: Rotate through years for each stock to spread the load
        Skips combinations that have already failed
        Returns: (symbol, year) or (None, None) if all done
        """
        all_symbols = stock_data_service.get_all_market_symbols()
        
        # For each symbol, check which years are missing
        for symbol in all_symbols:
            for year in self.target_years:
                # Skip if we've already tried and failed this combination
                fail_key = f"{symbol}_{year}"
                if fail_key in self.failed_attempts:
                    continue
                
                # Check if this symbol+year already exists (any month)
                exists = db.query(StockData).filter(
                    and_(
                        StockData.symbol == symbol,
                        StockData.year == year
                    )
                ).first()
                
                if not exists:
                    return (symbol, year)
        
        # All stocks fetched!
        return (None, None)
    
    async def fetch_one_stock(self, symbol: str, year: int, db: Session) -> bool:
        """
        Fetch a single stock for a single year
        Returns: True if successful, False if failed
        """
        try:
            logger.info(f"📥 Fetching {symbol} for year {year}...")
            
            # Fetch the stock data
            stocks_data = await stock_data_service.fetch_multiple_stocks_async([symbol], year, limit=1)
            
            if stocks_data and len(stocks_data) > 0:
                stock = stocks_data[0]
                
                # Check if already exists (symbol+year, any month)
                existing = db.query(StockData).filter(
                    and_(
                        StockData.symbol == stock['symbol'],
                        StockData.year == year
                    )
                ).first()
                
                if existing:
                    # Update existing record
                    for key in ['company_name', 'sector', 'ebit', 'enterprise_value', 'tangible_capital',
                               'earnings_yield', 'return_on_capital', 'market_cap', 'current_price']:
                        setattr(existing, key, stock.get(key))
                    existing.data_source = stock.get('source', 'polygon')
                    existing.updated_at = datetime.utcnow()
                    logger.info(f"✅ Updated {symbol} ({year})")
                else:
                    # Create new record
                    # Month comes from the stock data itself (financial data month)
                    db_stock = StockData(
                        symbol=stock['symbol'],
                        company_name=stock['company_name'],
                        sector=stock.get('sector'),
                        year=year,
                        month=stock.get('month'),  # Use stock's month (or None if not available)
                        ebit=stock['ebit'],
                        enterprise_value=stock['enterprise_value'],
                        tangible_capital=stock['tangible_capital'],
                        earnings_yield=stock['earnings_yield'],
                        return_on_capital=stock['return_on_capital'],
                        market_cap=stock['market_cap'],
                        current_price=stock.get('current_price'),
                        data_source=stock.get('source', 'polygon')
                    )
                    db.add(db_stock)
                    logger.info(f"✅ Stored {symbol} ({year}) - Source: {stock.get('source', 'polygon')}")
                
                db.commit()
                return True
            else:
                logger.warning(f"❌ Failed to fetch {symbol} ({year}) - No data from any source")
                # Mark this combination as failed to avoid retrying
                fail_key = f"{symbol}_{year}"
                self.failed_attempts[fail_key] = datetime.now()
                logger.info(f"📝 Marked {fail_key} as failed (total failed: {len(self.failed_attempts)})")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error fetching {symbol} ({year}): {str(e)}")
            db.rollback()
            return False
    
    async def run_continuous(self):
        """
        Main continuous loop - runs forever fetching stocks one by one
        """
        logger.info("="*70)
        logger.info("🚀 CONTINUOUS STOCK FETCHER STARTED")
        logger.info("="*70)
        logger.info(f"Strategy: 1 stock every {self.delay_between_stocks} seconds")
        logger.info(f"Rate: {self.stocks_per_hour} stocks/hour, {self.stocks_per_day} stocks/day")
        logger.info(f"Target: All S&P 500 + NASDAQ 100 + Dow 30 stocks")
        logger.info(f"Years: {', '.join(map(str, self.target_years))}")
        logger.info("="*70)
        
        stocks_fetched = 0
        stocks_failed = 0
        start_time = datetime.now()
        
        while True:
            db = SessionLocal()
            
            try:
                # Get next stock to fetch
                symbol, year = self.get_next_stock_to_fetch(db)
                
                if symbol is None:
                    logger.info("="*70)
                    logger.info("🎉 ALL STOCKS FETCHED!")
                    logger.info(f"Total fetched: {stocks_fetched}")
                    logger.info(f"Total failed: {stocks_failed}")
                    elapsed = datetime.now() - start_time
                    logger.info(f"Time elapsed: {elapsed}")
                    logger.info("="*70)
                    
                    # Check again after 1 hour (in case new stocks added)
                    logger.info("⏳ Sleeping for 1 hour before checking for new stocks...")
                    await asyncio.sleep(3600)
                    continue
                
                # Fetch the stock
                success = await self.fetch_one_stock(symbol, year, db)
                
                if success:
                    stocks_fetched += 1
                else:
                    stocks_failed += 1
                
                # Progress update every 10 stocks
                if (stocks_fetched + stocks_failed) % 10 == 0:
                    total_stocks = db.query(StockData).count()
                    elapsed = datetime.now() - start_time
                    rate = stocks_fetched / (elapsed.total_seconds() / 3600) if elapsed.total_seconds() > 0 else 0
                    
                    logger.info("─"*70)
                    logger.info(f"📊 Progress: {stocks_fetched} fetched, {stocks_failed} failed")
                    logger.info(f"📈 Database: {total_stocks} total records")
                    logger.info(f"⏱️  Rate: {rate:.1f} stocks/hour")
                    logger.info(f"⏳ Elapsed: {elapsed}")
                    logger.info("─"*70)
                
            finally:
                db.close()
            
            # Wait before next fetch (60 seconds = 1 stock/minute)
            logger.info(f"⏳ Waiting {self.delay_between_stocks} seconds before next fetch...")
            await asyncio.sleep(self.delay_between_stocks)

# Global instance
continuous_fetcher = ContinuousFetcher()
