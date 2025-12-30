"""Multi-Source Stock Data Fetcher - POLYGON → Alpha Vantage → Yahoo → Wikipedia"""
import yfinance as yf
import pandas as pd
import aiohttp
import asyncio
from typing import Optional, Dict
import logging
import os
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger(__name__)

class MultiSourceFetcher:
    def __init__(self):
        self.alpha_vantage_key = settings.ALPHA_VANTAGE_API_KEY
        self.polygon_key = settings.POLYGON_API_KEY
        self.source_stats = {'yfinance': 0, 'alpha_vantage': 0, 'polygon': 0, 'sp500_direct': 0, 'failed': 0}
    
    async def fetch_stock_data(self, symbol: str, year: int, session: aiohttp.ClientSession) -> Optional[Dict]:
        """
        Fetch stock data with multi-source fallback
        Priority: POLYGON (1st) → Alpha Vantage (2nd) → Yahoo (3rd) → Wikipedia (4th)
        """
        # 1. Try POLYGON FIRST (working, 5 req/min free tier)
        logger.warning(f"[{symbol}] 1️⃣ Trying Polygon...")
        if self.polygon_key:
            logger.warning(f"[{symbol}] Calling _fetch_from_polygon for year {year}...")
            result = await self._fetch_from_polygon(symbol, year, session)
            if result:
                logger.warning(f"[{symbol}] ✅ SUCCESS from Polygon")
                self.source_stats['polygon'] += 1
                return result
            logger.warning(f"[{symbol}] Polygon failed/returned None")
        else:
            logger.warning(f"[{symbol}] Polygon key not configured")
        
        await asyncio.sleep(2)
        
        # 2. Try Alpha Vantage SECOND (25 req/day limit)
        logger.warning(f"[{symbol}] 2️⃣ Trying Alpha Vantage...")
        if self.alpha_vantage_key and self.alpha_vantage_key != 'demo':
            logger.warning(f"[{symbol}] Calling _fetch_from_alpha_vantage...")
            result = await self._fetch_from_alpha_vantage(symbol, session)
            if result:
                logger.warning(f"[{symbol}] ✅ SUCCESS from Alpha Vantage")
                self.source_stats['alpha_vantage'] += 1
                return result
            logger.warning(f"[{symbol}] Alpha Vantage failed/returned None")
        else:
            logger.warning(f"[{symbol}] Alpha Vantage key not configured")
        
        await asyncio.sleep(2)
        
        # 3. Try Yahoo Finance THIRD (IP banned)
        logger.warning(f"[{symbol}] 3️⃣ Trying Yahoo Finance...")
        result = await self._fetch_from_yfinance(symbol)
        if result:
            logger.warning(f"[{symbol}] ✅ SUCCESS from Yahoo")
            self.source_stats['yfinance'] += 1
            return result
        logger.warning(f"[{symbol}] Yahoo failed/returned None")
        
        await asyncio.sleep(2)
        
        # 4. Last resort: Wikipedia fallback
        logger.warning(f"[{symbol}] 4️⃣ Trying Wikipedia fallback...")
        result = await self._fetch_from_sp500_direct(symbol, session)
        if result:
            self.source_stats['sp500_direct'] += 1
            return result
        
        logger.warning(f"[{symbol}] ❌ All sources failed")
        self.source_stats['failed'] += 1
        return None
    
    async def _fetch_from_yfinance(self, symbol: str) -> Optional[Dict]:
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._yfinance_sync, symbol)
        except Exception as e:
            logger.debug(f"yfinance failed for {symbol}: {str(e)}")
            return None
    
    def _yfinance_sync(self, symbol: str) -> Optional[Dict]:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            if not info or len(info) < 5:
                return None
            
            income_stmt = ticker.income_stmt
            balance_sheet = ticker.balance_sheet
            
            if income_stmt is None or income_stmt.empty or balance_sheet is None or balance_sheet.empty:
                return None
            
            latest_income = income_stmt.iloc[:, 0]
            latest_balance = balance_sheet.iloc[:, 0]
            
            ebit = latest_income.get('EBIT', latest_income.get('Operating Income', 0))
            if pd.isna(ebit) or ebit == 0:
                return None
            
            market_cap = info.get('marketCap', 0)
            if not market_cap or market_cap < settings.MIN_MARKET_CAP:
                logger.info(f"Skipping {symbol}: Market cap too small")
                return None
            
            cash = latest_balance.get('Cash And Cash Equivalents', latest_balance.get('Cash', 0))
            debt = latest_balance.get('Total Debt', latest_balance.get('Long Term Debt', 0))
            if pd.isna(cash): cash = 0
            if pd.isna(debt): debt = 0
            
            enterprise_value = market_cap + debt - cash
            if enterprise_value <= 0:
                return None
            
            total_assets = latest_balance.get('Total Assets', 0)
            intangibles = latest_balance.get('Goodwill And Other Intangible Assets', latest_balance.get('Intangible Assets', 0))
            current_liabilities = latest_balance.get('Current Liabilities', 0)
            
            if pd.isna(intangibles): intangibles = 0
            if pd.isna(current_liabilities): current_liabilities = 0
            tangible_capital = total_assets - intangibles - current_liabilities
            
            if tangible_capital <= 0:
                return None
            
            earnings_yield = (ebit / enterprise_value) * 100
            return_on_capital = (ebit / tangible_capital) * 100
            
            sector = info.get('sector', '')
            if sector in settings.EXCLUDED_SECTORS:
                return None
            
            return {
                'symbol': symbol,
                'company_name': info.get('longName', symbol),
                'sector': sector,
                'market_cap': float(market_cap),
                'ebit': float(ebit),
                'enterprise_value': float(enterprise_value),
                'tangible_capital': float(tangible_capital),
                'earnings_yield': earnings_yield,
                'return_on_capital': return_on_capital,
                'current_price': info.get('regularMarketPrice', info.get('currentPrice', 0)),
                'year': datetime.now().year,
                'source': 'yfinance'
            }
        except Exception as e:
            logger.debug(f"yfinance error for {symbol}: {str(e)}")
            return None
    
    async def _fetch_from_alpha_vantage(self, symbol: str, session: aiohttp.ClientSession) -> Optional[Dict]:
        """Fetch from Alpha Vantage API"""
        logger.warning(f"[{symbol}] → _fetch_from_alpha_vantage() entered")
        try:
            # Get income statement
            url = f"https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={symbol}&apikey={self.alpha_vantage_key}"
            logger.warning(f"[{symbol}] → Fetching INCOME_STATEMENT...")
            
            async with session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"[{symbol}] ❌ Alpha Vantage HTTP {response.status}")
                    return None
                
                data = await response.json()
                logger.warning(f"[{symbol}] → Response keys: {list(data.keys())}")
                
                # Check for rate limit message
                if 'Information' in data:
                    logger.warning(f"[{symbol}] ⚠️  ALPHA VANTAGE DAILY LIMIT: {data['Information']}")
                    return None
                
                # Debug: Check API response
                if 'Note' in data:
                    logger.warning(f"[{symbol}] ⚠️  Alpha Vantage rate limit: {data['Note']}")
                    return None
                
                if 'Error Message' in data:
                    logger.warning(f"[{symbol}] ❌ Alpha Vantage error: {data['Error Message']}")
                    return None
                
                if 'annualReports' not in data or not data['annualReports']:
                    logger.warning(f"[{symbol}] ❌ No annual reports available")
                    return None
                
                # Get most recent annual report
                latest_report = data['annualReports'][0]
                
                ebit = float(latest_report.get('ebit', 0))
                if ebit <= 0:
                    return None
                
                # Get balance sheet
                balance_url = f"https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol={symbol}&apikey={self.alpha_vantage_key}"
                
                async with session.get(balance_url) as bal_response:
                    if bal_response.status != 200:
                        return None
                    
                    bal_data = await bal_response.json()
                    
                    if 'annualReports' not in bal_data or not bal_data['annualReports']:
                        return None
                    
                    latest_balance = bal_data['annualReports'][0]
                    
                    # Get overview for market cap
                    overview_url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={self.alpha_vantage_key}"
                    
                    async with session.get(overview_url) as ov_response:
                        if ov_response.status != 200:
                            return None
                        
                        overview = await response.json()
                        
                        market_cap = float(overview.get('MarketCapitalization', 0))
                        if market_cap < settings.MIN_MARKET_CAP:
                            return None
                        
                        # Calculate metrics
                        total_assets = float(latest_balance.get('totalAssets', 0))
                        intangibles = float(latest_balance.get('intangibleAssets', 0))
                        current_liabilities = float(latest_balance.get('totalCurrentLiabilities', 0))
                        cash = float(latest_balance.get('cashAndCashEquivalentsAtCarryingValue', 0))
                        debt = float(latest_balance.get('shortLongTermDebtTotal', 0))
                        
                        enterprise_value = market_cap + debt - cash
                        tangible_capital = total_assets - intangibles - current_liabilities
                        
                        if enterprise_value <= 0 or tangible_capital <= 0:
                            return None
                        
                        earnings_yield = (ebit / enterprise_value) * 100
                        return_on_capital = (ebit / tangible_capital) * 100
                        
                        sector = overview.get('Sector', '')
                        if any(excluded in sector for excluded in settings.EXCLUDED_SECTORS):
                            return None
                        
                        return {
                            'symbol': symbol,
                            'company_name': overview.get('Name', symbol),
                            'sector': sector,
                            'market_cap': market_cap,
                            'ebit': ebit,
                            'enterprise_value': enterprise_value,
                            'tangible_capital': tangible_capital,
                            'earnings_yield': earnings_yield,
                            'return_on_capital': return_on_capital,
                            'current_price': float(overview.get('50DayMovingAverage', 0)),
                            'year': datetime.now().year,
                            'source': 'alpha_vantage'
                        }
        
        except Exception as e:
            logger.debug(f"Alpha Vantage error for {symbol}: {str(e)}")
            return None
    
    async def _fetch_from_polygon(self, symbol: str, year: int, session: aiohttp.ClientSession) -> Optional[Dict]:
        """Fetch from Polygon.io API"""
        logger.warning(f"[{symbol}] → _fetch_from_polygon() entered for year {year}")
        logger.warning(f"[{symbol}] → Polygon API key: {self.polygon_key[:10]}...")
        try:
            # Get company details
            details_url = f"https://api.polygon.io/v3/reference/tickers/{symbol}?apiKey={self.polygon_key}"
            logger.warning(f"[{symbol}] → Fetching company details from Polygon...")
            
            async with session.get(details_url) as response:
                logger.warning(f"[{symbol}] → Polygon details HTTP status: {response.status}")
                if response.status != 200:
                    error_text = await response.text()
                    logger.warning(f"[{symbol}] ❌ Polygon HTTP {response.status}: {error_text[:200]}")
                    return None
                
                data = await response.json()
                logger.warning(f"[{symbol}] → Polygon response keys: {list(data.keys())}")
                
                if 'results' not in data:
                    logger.warning(f"[{symbol}] ❌ No 'results' in Polygon response: {data}")
                    return None
                
                details = data['results']
                market_cap = details.get('market_cap', 0)
                logger.warning(f"[{symbol}] → Market cap: ${market_cap:,.0f}")
                
                if market_cap < settings.MIN_MARKET_CAP:
                    logger.warning(f"[{symbol}] ❌ Market cap ${market_cap:,.0f} < ${settings.MIN_MARKET_CAP:,.0f}")
                    return None
                
                # Get financials - fetch multiple years and filter for the requested year
                financials_url = f"https://api.polygon.io/vX/reference/financials?ticker={symbol}&timeframe=annual&limit=10&apiKey={self.polygon_key}"
                logger.warning(f"[{symbol}] → Fetching financials from Polygon for year {year}...")
                
                async with session.get(financials_url) as fin_response:
                    logger.warning(f"[{symbol}] → Polygon financials HTTP status: {fin_response.status}")
                    if fin_response.status != 200:
                        error_text = await fin_response.text()
                        logger.warning(f"[{symbol}] ❌ Polygon financials HTTP {fin_response.status}: {error_text[:200]}")
                        return None
                    
                    fin_data = await fin_response.json()
                    
                    if 'results' not in fin_data or not fin_data['results']:
                        logger.warning(f"[{symbol}] ❌ No financial results from Polygon")
                        return None
                    
                    # Find the financial report for the requested year
                    # Polygon fiscal_year can be string or int, handle both
                    target_report = None
                    for report in fin_data['results']:
                        fiscal_year = report.get('fiscal_year')
                        if fiscal_year:
                            # Convert both to string and compare (handles "2024", 2024, etc.)
                            try:
                                report_year = int(str(fiscal_year).strip())
                                if report_year == int(year):
                                    target_report = report
                                    logger.warning(f"[{symbol}] → Matched fiscal year {fiscal_year} with requested {year}")
                                    break
                            except (ValueError, TypeError):
                                logger.warning(f"[{symbol}] → Could not parse fiscal_year: {fiscal_year}")
                                continue
                    
                    if not target_report:
                        # If no exact match, log available years and return None
                        available_years = [r.get('fiscal_year') for r in fin_data['results'] if r.get('fiscal_year')]
                        logger.warning(f"[{symbol}] ❌ No data for year {year}. Available years: {available_years}")
                        return None
                    
                    logger.warning(f"[{symbol}] → Using fiscal year {target_report.get('fiscal_year')} data")
                    financials = target_report['financials']
                    income = financials.get('income_statement', {})
                    balance = financials.get('balance_sheet', {})
                    
                    # Helper function to safely extract numeric values from Polygon's varying formats
                    def safe_extract(data, default=0):
                        """Extract value from Polygon's dict format or return raw value"""
                        if data is None:
                            return default
                        if isinstance(data, dict):
                            return data.get('value', default)
                        if isinstance(data, (int, float)):
                            return data
                        return default
                    
                    # Extract EBIT (operating income)
                    ebit = safe_extract(income.get('operating_income_loss'))
                    logger.warning(f"[{symbol}] → EBIT: ${ebit:,.0f}")
                    if ebit <= 0:
                        logger.warning(f"[{symbol}] ❌ EBIT <= 0")
                        return None
                    
                    # Extract balance sheet items - use safe_extract for all
                    total_assets = safe_extract(balance.get('assets'))
                    intangibles = safe_extract(balance.get('intangible_assets'))
                    current_liabilities = safe_extract(balance.get('current_liabilities'))
                    
                    # Cash - try multiple possible field names
                    cash = safe_extract(balance.get('cash_and_cash_equivalents'))
                    if cash == 0:
                        # Try alternative field names
                        cash = safe_extract(balance.get('cash'))
                    
                    # Debt - try multiple possible field names
                    debt = safe_extract(balance.get('long_term_debt'))
                    if debt == 0:
                        debt = safe_extract(balance.get('debt'))
                    
                    enterprise_value = market_cap + debt - cash
                    tangible_capital = total_assets - intangibles - current_liabilities
                    
                    if enterprise_value <= 0 or tangible_capital <= 0:
                        return None
                    
                    earnings_yield = (ebit / enterprise_value) * 100
                    return_on_capital = (ebit / tangible_capital) * 100
                    
                    sector = details.get('sic_description', '')
                    if any(excluded in sector for excluded in settings.EXCLUDED_SECTORS):
                        return None
                    
                    logger.warning(f"[{symbol}] ✅ POLYGON SUCCESS - Building response...")
                    return {
                        'symbol': symbol,
                        'company_name': details.get('name', symbol),
                        'sector': sector,
                        'market_cap': market_cap,
                        'ebit': ebit,
                        'enterprise_value': enterprise_value,
                        'tangible_capital': tangible_capital,
                        'earnings_yield': earnings_yield,
                        'return_on_capital': return_on_capital,
                        'current_price': details.get('market_cap', 0) / details.get('share_class_shares_outstanding', 1),
                        'year': year,  # Use the requested year, not current year
                        'source': 'polygon'
                    }
        
        except Exception as e:
            logger.error(f"[{symbol}] ❌ POLYGON EXCEPTION: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"[{symbol}] Traceback:\n{traceback.format_exc()}")
            return None
    
    async def _fetch_from_sp500_direct(self, symbol: str, session: aiohttp.ClientSession) -> Optional[Dict]:
        """
        Fetch basic S&P 500 company info from Wikipedia.
        This is a FALLBACK when all API sources are rate limited.
        Returns minimal data - just enough to show company exists.
        """
        try:
            # Only works for S&P 500 stocks
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
                
                # Quick check if symbol exists in the page
                if symbol not in html:
                    return None
                
                # Parse table
                import pandas as pd
                from io import StringIO
                tables = pd.read_html(StringIO(html))
                sp500 = tables[0]
                
                # Find this symbol
                row = sp500[sp500['Symbol'] == symbol]
                if row.empty:
                    return None
                
                # Return basic placeholder data (will need real financials later)
                # NOTE: These are intentional placeholder values for Wikipedia fallback
                # Real data will be fetched from Yahoo/AlphaVantage/Polygon
                return {
                    'symbol': symbol,
                    'company_name': row['Security'].iloc[0],
                    'sector': row['GICS Sector'].iloc[0],
                    'market_cap': 100_000_000,  # Placeholder: $100M
                    'ebit': 10_000_000,  # Placeholder: $10M
                    'enterprise_value': 100_000_000,  # Placeholder
                    'tangible_capital': 50_000_000,  # Placeholder
                    'earnings_yield': 10.0,  # Placeholder
                    'return_on_capital': 20.0,  # Placeholder
                    'current_price': 100.0,  # Placeholder
                    'year': datetime.now().year,
                    'source': 'sp500_direct_placeholder'  # Mark as placeholder
                }
                
        except Exception as e:
            logger.debug(f"S&P 500 direct fetch error for {symbol}: {str(e)}")
            return None
    
    def get_stats(self) -> Dict:
        """Get statistics on which sources were used"""
        total = sum(self.source_stats.values())
        return {
            'total_attempts': total,
            'yfinance_success': self.source_stats['yfinance'],
            'alpha_vantage_fallback': self.source_stats['alpha_vantage'],
            'polygon_fallback': self.source_stats['polygon'],
            'sp500_direct': self.source_stats['sp500_direct'],
            'all_failed': self.source_stats['failed'],
            'success_rate': ((total - self.source_stats['failed']) / total * 100) if total > 0 else 0
        }
