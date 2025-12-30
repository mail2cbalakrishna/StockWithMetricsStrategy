"""Background Stock Data Processor"""
import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.database import StockData, FailedStock, YearCompletion, get_db, init_db
from app.services.stock_data_service import stock_data_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackgroundStockProcessor:
    def __init__(self):
        self.running = False
    
    async def process_year(self, year: int, db: Session, month: int = None):
        """
        Fetch and store stocks for given year/month
        
        Args:
            year: Year to fetch (e.g., 2024, 2023)
            db: Database session
            month: Month (1-12) for monthly data, None for annual data
        
        Note: Financial statements (EBIT, balance sheet) are typically ANNUAL.
        Monthly tracking would be for stock price changes, not fundamentals.
        For Magic Formula strategy, we use ANNUAL financial data.
        """
        period_str = f"{year}-{month:02d}" if month else f"{year}"
        logger.info(f"Processing {period_str}...")
        
        year_completion = db.query(YearCompletion).filter(
            and_(YearCompletion.year == year, YearCompletion.month == month)
        ).first()
        
        if not year_completion:
            year_completion = YearCompletion(
                year=year, month=month, status='in_progress', started_at=datetime.utcnow()
            )
            db.add(year_completion)
            db.commit()
        
        symbols = stock_data_service.get_all_market_symbols()
        year_completion.total_symbols = len(symbols)
        db.commit()
        
        logger.info(f"Fetching {len(symbols)} stocks...")
        stocks_data = await stock_data_service.fetch_multiple_stocks_async(symbols, year)
        
        successful_symbols = set()
        if stocks_data:
            successful_symbols = {stock['symbol'] for stock in stocks_data}
            logger.info(f"Fetched {len(stocks_data)} stocks")
        
        failed_symbols = set(symbols) - successful_symbols
        
        stored_count = 0
        updated_count = 0
        
        if stocks_data:
            for stock in stocks_data:
                try:
                    existing = db.query(StockData).filter(
                        and_(
                            StockData.symbol == stock['symbol'],
                            StockData.year == year,
                            StockData.month == month
                        )
                    ).first()
                    
                    if existing:
                        for key in ['company_name', 'sector', 'ebit', 'enterprise_value', 'tangible_capital',
                                   'earnings_yield', 'return_on_capital', 'market_cap', 'current_price']:
                            setattr(existing, key, stock.get(key))
                        existing.data_source = stock.get('source', 'yfinance')
                        existing.updated_at = datetime.utcnow()
                        updated_count += 1
                    else:
                        db_stock = StockData(
                            symbol=stock['symbol'],
                            company_name=stock['company_name'],
                            sector=stock.get('sector'),
                            year=year,
                            month=month,
                            ebit=stock['ebit'],
                            enterprise_value=stock['enterprise_value'],
                            tangible_capital=stock['tangible_capital'],
                            earnings_yield=stock['earnings_yield'],
                            return_on_capital=stock['return_on_capital'],
                            market_cap=stock['market_cap'],
                            current_price=stock.get('current_price'),
                            data_source=stock.get('source', 'yfinance'),
                            fetched_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )
                        db.add(db_stock)
                        stored_count += 1
                    
                    failed = db.query(FailedStock).filter(
                        and_(
                            FailedStock.symbol == stock['symbol'],
                            FailedStock.year == year,
                            FailedStock.month == month
                        )
                    ).first()
                    if failed:
                        failed.status = 'completed'
                        failed.completed_at = datetime.utcnow()
                    
                    if (stored_count + updated_count) % 100 == 0:
                        db.commit()
                        
                except Exception as e:
                    logger.error(f"Error storing {stock['symbol']}: {e}")
                    continue
        
        failed_count = 0
        for symbol in failed_symbols:
            try:
                existing_failed = db.query(FailedStock).filter(
                    and_(FailedStock.symbol == symbol, FailedStock.year == year, FailedStock.month == month)
                ).first()
                
                if existing_failed:
                    existing_failed.retry_count += 1
                    existing_failed.last_attempt = datetime.utcnow()
                    existing_failed.next_retry = datetime.utcnow() + timedelta(seconds=3)
                    
                    if existing_failed.retry_count >= existing_failed.max_retries:
                        existing_failed.status = 'failed'
                        existing_failed.next_retry = None
                    else:
                        existing_failed.status = 'pending'
                else:
                    failed_stock = FailedStock(
                        symbol=symbol, year=year, month=month,
                        error_message="Fetch failed", retry_count=1, status='pending',
                        first_attempt=datetime.utcnow(), last_attempt=datetime.utcnow(),
                        next_retry=datetime.utcnow() + timedelta(seconds=3)
                    )
                    db.add(failed_stock)
                
                failed_count += 1
            except Exception as e:
                logger.error(f"Error recording failure for {symbol}: {e}")
                continue
        
        db.commit()
        
        year_completion.successful_fetches = stored_count + updated_count
        year_completion.pending_retries = db.query(FailedStock).filter(
            and_(FailedStock.year == year, FailedStock.month == month, FailedStock.status == 'pending')
        ).count()
        year_completion.permanently_failed = db.query(FailedStock).filter(
            and_(FailedStock.year == year, FailedStock.month == month, FailedStock.status == 'failed')
        ).count()
        
        total = year_completion.total_symbols
        success = year_completion.successful_fetches
        year_completion.completion_percentage = (success / total * 100) if total > 0 else 0
        
        if year_completion.pending_retries == 0:
            year_completion.status = 'completed_with_failures' if year_completion.permanently_failed > 0 else 'completed'
            year_completion.completed_at = datetime.utcnow()
        
        year_completion.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Complete: {stored_count} new, {updated_count} updated, {failed_count} failed")
    
    async def should_refresh_year(self, year: int, month: int, db: Session) -> bool:
        """Check if period needs refresh"""
        latest_record = db.query(StockData).filter(
            and_(StockData.year == year, StockData.month == month)
        ).order_by(StockData.updated_at.desc()).first()
        
        if not latest_record:
            return True
        
        refresh_hours = 24 if year == datetime.now().year else 168
        age_hours = (datetime.utcnow() - latest_record.updated_at).total_seconds() / 3600
        return age_hours >= refresh_hours
    
    async def monitor_current_year(self, db: Session):
        """Monitor and update current year data"""
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        year_completion = db.query(YearCompletion).filter(
            and_(YearCompletion.year == current_year, YearCompletion.month.is_(None))
        ).first()
        
        if not year_completion:
            year_completion = YearCompletion(
                year=current_year, month=None, total_symbols=516,
                status='in_progress', started_at=datetime.utcnow()
            )
            db.add(year_completion)
            db.commit()
        
        await self.process_year(current_year, db, month=None)
        await self.process_year(current_year, db, month=current_month)
        
        if datetime.now().day <= 5:
            last_month = current_month - 1 if current_month > 1 else 12
            last_year = current_year if current_month > 1 else current_year - 1
            await self.process_year(last_year, db, month=last_month)
        
        await self.retry_failed_stocks(db)
    
    async def retry_failed_stocks(self, db: Session):
        """Retry failed stocks"""
        now = datetime.utcnow()
        failed_stocks = db.query(FailedStock).filter(
            and_(FailedStock.status == 'pending', FailedStock.next_retry <= now)
        ).all()
        
        if not failed_stocks:
            return
        
        retry_success = 0
        
        for failed in failed_stocks:
            try:
                failed.status = 'retrying'
                db.commit()
                
                result = await stock_data_service.fetch_multiple_stocks_async([failed.symbol], failed.year)
                
                if result and len(result) > 0:
                    stock = result[0]
                    db_stock = StockData(
                        symbol=stock['symbol'], company_name=stock['company_name'],
                        sector=stock.get('sector'), year=failed.year, month=failed.month,
                        ebit=stock['ebit'], enterprise_value=stock['enterprise_value'],
                        tangible_capital=stock['tangible_capital'],
                        earnings_yield=stock['earnings_yield'],
                        return_on_capital=stock['return_on_capital'],
                        market_cap=stock['market_cap'],
                        current_price=stock.get('current_price'),
                        data_source=stock.get('source', 'yfinance'),
                        fetched_at=datetime.utcnow(), updated_at=datetime.utcnow()
                    )
                    db.add(db_stock)
                    failed.status = 'completed'
                    failed.completed_at = datetime.utcnow()
                    retry_success += 1
                else:
                    failed.retry_count += 1
                    failed.last_attempt = datetime.utcnow()
                    failed.next_retry = datetime.utcnow() + timedelta(seconds=3)
                    
                    if failed.retry_count >= failed.max_retries:
                        failed.status = 'failed'
                        failed.next_retry = None
                    else:
                        failed.status = 'pending'
                
                db.commit()
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error retrying {failed.symbol}: {e}")
                failed.status = 'pending'
                db.commit()
        
        if retry_success > 0:
            logger.info(f"Retry complete: {retry_success} succeeded")
    
    async def process_years_sequentially(self, db: Session, start_year: int = 2024, end_year: int = 2017):
        """Process years sequentially"""
        logger.info(f"Processing years: {start_year} → {end_year}")
        
        for year in range(start_year, end_year - 1, -1):
            await self.process_year(year, db, month=None)
            
            retry_cycle = 0
            while retry_cycle < 100:
                year_completion = db.query(YearCompletion).filter(
                    and_(YearCompletion.year == year, YearCompletion.month.is_(None))
                ).first()
                
                if not year_completion or year_completion.pending_retries == 0:
                    break
                
                await self.retry_failed_stocks(db)
                
                year_completion.pending_retries = db.query(FailedStock).filter(
                    and_(FailedStock.year == year, FailedStock.month.is_(None), FailedStock.status == 'pending')
                ).count()
                year_completion.permanently_failed = db.query(FailedStock).filter(
                    and_(FailedStock.year == year, FailedStock.month.is_(None), FailedStock.status == 'failed')
                ).count()
                year_completion.successful_fetches = db.query(StockData).filter(
                    and_(StockData.year == year, StockData.month.is_(None))
                ).count()
                
                total = year_completion.total_symbols
                success = year_completion.successful_fetches
                year_completion.completion_percentage = (success / total * 100) if total > 0 else 0
                
                if year_completion.pending_retries == 0:
                    year_completion.status = 'completed_with_failures' if year_completion.permanently_failed > 0 else 'completed'
                    year_completion.completed_at = datetime.utcnow()
                
                db.commit()
                retry_cycle += 1
                await asyncio.sleep(5)
    
    
    
    async def run_continuous(self):
        """Run continuous processing with scheduled batch jobs"""
        self.running = True
        logger.info("Background processor started with scheduled batch jobs (3 AM - 10 AM daily)")
        init_db()
        db = next(get_db())
        
        try:
            last_batch_date = None
            last_retry_check = datetime.now()
            
            while self.running:
                try:
                    now = datetime.now()
                    current_date = now.date()
                    current_hour = now.hour
                    
                    # SCHEDULED BATCH JOB: Run between 3 AM - 10 AM daily
                    if 3 <= current_hour < 10:
                        # Run batch job once per day
                        if last_batch_date != current_date:
                            logger.info(f"Starting scheduled batch job at {now.strftime('%Y-%m-%d %H:%M:%S')}")
                            logger.info("Processing years 2017-2025 (2025 will use latest available data)")
                            
                            # Process years sequentially: 2024 → 2017 (skip 2025 - no annual data yet)
                            await self.process_years_sequentially(db, start_year=2024, end_year=2017)
                            
                            last_batch_date = current_date
                            logger.info(f"Batch job completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    # CONTINUOUS RETRY: Check every 5 seconds for failed stocks
                    if (now - last_retry_check).total_seconds() >= 5:
                        pending = db.query(FailedStock).filter(
                            and_(FailedStock.status == 'pending', FailedStock.next_retry <= now)
                        ).count()
                        
                        if pending > 0:
                            await self.retry_failed_stocks(db)
                        
                        last_retry_check = now
                    
                    # Sleep for 60 seconds before next check
                    await asyncio.sleep(60)
                    
                except Exception as e:
                    logger.error(f"Error in monitoring: {e}")
                    await asyncio.sleep(600)
        except Exception as e:
            logger.error(f"Error in processing: {e}")
            await asyncio.sleep(3600)
        finally:
            db.close()
    
    def stop(self):
        self.running = False

background_processor = BackgroundStockProcessor()
