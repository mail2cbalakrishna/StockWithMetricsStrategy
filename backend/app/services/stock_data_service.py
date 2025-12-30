"""
Stock Data Service - RESTORED
Fetches stock data using multi-source fallback strategy
"""
import yfinance as yf
import pandas as pd
from typing import List, Dict, Optional
import logging
import asyncio
import aiohttp
import time
from .multi_source_fetcher import MultiSourceFetcher

logger = logging.getLogger(__name__)

class StockDataService:
    """Service to fetch and process stock data"""
    
    def __init__(self):
        self._sp500_symbols = None
        self.max_concurrent_requests = 1
        self.request_delay = 3.0
        self.batch_size = 100
        self.batch_break = 300
        self.multi_source = MultiSourceFetcher()
        self.source_rotation_index = 0
        self.sources = ['yfinance', 'alpha_vantage', 'polygon', 'wikipedia']
        
        logger.info("Stock Data Service initialized: 20 stocks/min, 100/batch, 5min breaks")
    
    def get_all_market_symbols(self) -> List[str]:
        """Get S&P 500 + NASDAQ 100 + Dow 30 symbols"""
        try:
            symbols = self._fetch_quality_stocks()
            if symbols and len(symbols) >= 500:
                logger.info(f"Fetched {len(symbols)} quality stocks")
                return symbols
            return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']
        except Exception as e:
            logger.error(f"Error fetching symbols: {e}")
            return ['AAPL', 'MSFT', 'GOOGL']
    
    def _fetch_quality_stocks(self) -> List[str]:
        """Fetch from S&P 500, NASDAQ 100, Dow 30"""
        all_symbols = set()
        sp500 = self._get_sp500_symbols()
        if sp500:
            all_symbols.update(sp500)
        nasdaq100 = self._get_nasdaq100_symbols()
        if nasdaq100:
            all_symbols.update(nasdaq100)
        dow30 = self._get_dow30_symbols()
        if dow30:
            all_symbols.update(dow30)
        return sorted(list(all_symbols))
    
    def _get_sp500_symbols(self) -> List[str]:
        try:
            url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
            # Wikipedia requires User-Agent header
            tables = pd.read_html(url, storage_options={'User-Agent': 'Mozilla/5.0'})
            # Be resilient: scan all tables for a column containing 'symbol' (case-insensitive)
            for i, df in enumerate(tables):
                cols = [str(c) for c in df.columns]
                if any('symbol' in c.lower() for c in cols):
                    col = next(c for c in df.columns if 'symbol' in str(c).lower())
                    logger.info(f"Found S&P 500 symbols in Wikipedia table {i} column '{col}'")
                    return df[col].astype(str).str.replace('.', '-').str.strip().tolist()
            logger.error("Could not find a 'Symbol' column in any S&P 500 Wikipedia tables")
            return []
        except Exception as e:
            logger.error(f"Error fetching S&P 500: {e}")
            return []
    
    def _get_nasdaq100_symbols(self) -> List[str]:
        try:
            url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
            tables = pd.read_html(url, storage_options={'User-Agent': 'Mozilla/5.0'})
            for i, df in enumerate(tables):
                cols = [str(c) for c in df.columns]
                if any('ticker' in c.lower() or 'symbol' in c.lower() for c in cols):
                    col = next(c for c in df.columns if ('ticker' in str(c).lower() or 'symbol' in str(c).lower()))
                    logger.info(f"Found NASDAQ-100 symbols in Wikipedia table {i} column '{col}'")
                    return df[col].astype(str).str.replace('.', '-').str.strip().tolist()
            logger.error("Could not find 'Ticker' or 'Symbol' column in NASDAQ-100 tables")
            return []
        except Exception as e:
            logger.error(f"Error fetching NASDAQ 100: {e}")
            return []
    
    def _get_dow30_symbols(self) -> List[str]:
        try:
            url = 'https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average'
            tables = pd.read_html(url, storage_options={'User-Agent': 'Mozilla/5.0'})
            for i, df in enumerate(tables):
                cols = [str(c) for c in df.columns]
                if any('symbol' in c.lower() or 'ticker' in c.lower() for c in cols):
                    col = next(c for c in df.columns if ('symbol' in str(c).lower() or 'ticker' in str(c).lower()))
                    logger.info(f"Found Dow 30 symbols in Wikipedia table {i} column '{col}'")
                    return df[col].astype(str).str.replace('.', '-').str.strip().tolist()
            logger.error("Could not find 'Symbol' or 'Ticker' column in Dow 30 tables")
            return []
        except Exception as e:
            logger.error(f"Error fetching Dow 30: {e}")
            return []
    
    async def fetch_stock_data_async(self, symbol: str, year: int, semaphore: asyncio.Semaphore, session: aiohttp.ClientSession) -> Optional[Dict]:
        """Fetch single stock with rate limiting"""
        async with semaphore:
            try:
                stock_data = await self.multi_source.fetch_stock_data(symbol, year, session)
                await asyncio.sleep(self.request_delay)
                return stock_data
            except Exception as e:
                logger.error(f"Failed to fetch {symbol}: {e}")
                return None
    
    async def fetch_multiple_stocks_async(self, symbols: List[str], year: int, limit: Optional[int] = None) -> List[Dict]:
        """Fetch multiple stocks in batches with breaks"""
        if limit:
            symbols = symbols[:limit]
        
        logger.info(f"Processing {len(symbols)} stocks in batches of {self.batch_size}")
        start_time = time.time()
        
        BATCH_SIZE = self.batch_size
        total_symbols = len(symbols)
        all_results = []
        semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        
        async with aiohttp.ClientSession() as session:
            for batch_num in range(0, total_symbols, BATCH_SIZE):
                batch_symbols = symbols[batch_num:batch_num + BATCH_SIZE]
                batch_end = min(batch_num + BATCH_SIZE, total_symbols)
                
                logger.info(f"Processing batch {batch_num//BATCH_SIZE + 1}: stocks {batch_num + 1}-{batch_end}")
                
                tasks = [self.fetch_stock_data_async(symbol, year, semaphore, session) for symbol in batch_symbols]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                all_results.extend(batch_results)
                
                batch_success = sum(1 for r in batch_results if r is not None and not isinstance(r, Exception))
                logger.info(f"Batch complete: {batch_success}/{len(batch_symbols)} successful")
                
                if batch_end < total_symbols:
                    logger.info(f"Taking {self.batch_break}s break...")
                    await asyncio.sleep(self.batch_break)
            
            results = all_results
        
        valid_results = [r for r in results if r is not None and not isinstance(r, Exception)]
        total_time = time.time() - start_time
        logger.info(f"Complete! {len(valid_results)}/{len(symbols)} successful in {total_time/60:.1f} min")
        
        return valid_results

stock_data_service = StockDataService()
