"""
Dynamic Magic Formula Service
Applies Magic Formula ranking ON-DEMAND from stored stock data
This allows flexibility: users can query top stocks for any year/month dynamically
"""
import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.database import StockData
from app.core.config import settings

logger = logging.getLogger(__name__)

class DynamicMagicFormulaService:
    """
    Apply Magic Formula ranking dynamically on query
    - Reads ALL stocks from database for given year/month
    - Filters by Magic Formula criteria
    - Ranks stocks by combined Earnings Yield + Return on Capital
    - Returns top N stocks
    """
    
    def get_top_stocks(
        self,
        db: Session,
        year: int,
        month: Optional[int] = None,
        top_n: int = 10,
        min_earnings_yield: float = 0.0,
        min_return_on_capital: float = 0.0,
        min_market_cap: float = settings.MIN_MARKET_CAP
    ) -> List[Dict]:
        """
        Get top N stocks for a given year/month using Magic Formula
        
        Args:
            db: Database session
            year: Year to query
            month: Optional month (None = yearly data)
            top_n: Number of top stocks to return
            min_earnings_yield: Minimum earnings yield filter
            min_return_on_capital: Minimum return on capital filter
            min_market_cap: Minimum market cap filter
            
        Returns:
            List of top ranked stocks with all data
        """
        period_str = f"{year}-{month:02d}" if month else f"{year}"
        logger.info(f"🎯 Applying Magic Formula dynamically for {period_str}")
        
        # Query ALL stocks for this period
        if month is None:
            # When month is None, query all records for that year (they should all have month=12 or a value)
            query = db.query(StockData).filter(
                StockData.year == year
            )
        else:
            # When month is specified, query for that specific month
            query = db.query(StockData).filter(
                and_(
                    StockData.year == year,
                    StockData.month == month
                )
            )
        
        all_stocks = query.all()
        logger.info(f"📊 Found {len(all_stocks)} total stocks in database for {period_str}")
        
        if not all_stocks:
            logger.warning(f"❌ No stock data found for {period_str}")
            return []
        
        # Convert to dictionaries for processing
        stocks_data = []
        for stock in all_stocks:
            stocks_data.append({
                'symbol': stock.symbol,
                'company_name': stock.company_name,
                'sector': stock.sector,
                'year': stock.year,
                'month': stock.month,
                'ebit': stock.ebit,
                'enterprise_value': stock.enterprise_value,
                'tangible_capital': stock.tangible_capital,
                'earnings_yield': stock.earnings_yield,
                'return_on_capital': stock.return_on_capital,
                'market_cap': stock.market_cap,
                'current_price': stock.current_price,
                'data_source': stock.data_source,
                'updated_at': stock.updated_at
            })
        
        # Apply Magic Formula filters
        filtered_stocks = self._filter_stocks(
            stocks_data,
            min_earnings_yield=min_earnings_yield,
            min_return_on_capital=min_return_on_capital,
            min_market_cap=min_market_cap
        )
        
        logger.info(f"✅ {len(filtered_stocks)} stocks passed Magic Formula criteria")
        
        # Rank stocks
        ranked_stocks = self._rank_stocks(filtered_stocks)
        
        # Return top N
        top_stocks = ranked_stocks[:top_n]
        
        logger.info(f"🏆 Returning top {len(top_stocks)} stocks for {period_str}")
        
        return top_stocks
    
    def _filter_stocks(
        self,
        stocks: List[Dict],
        min_earnings_yield: float,
        min_return_on_capital: float,
        min_market_cap: float
    ) -> List[Dict]:
        """
        Filter stocks by Magic Formula criteria
        
        Criteria:
        1. EBIT > 0 (profitable)
        2. Market cap >= min_market_cap
        3. Earnings yield >= min
        4. Return on capital >= min
        5. Not in excluded sectors
        """
        filtered = []
        
        excluded_sectors = ['Financial Services', 'Financial', 'Utilities']
        
        for stock in stocks:
            # Check EBIT
            if stock['ebit'] <= 0:
                continue
            
            # Check market cap
            if stock['market_cap'] < min_market_cap:
                continue
            
            # Check earnings yield
            if stock['earnings_yield'] < min_earnings_yield:
                continue
            
            # Check return on capital
            if stock['return_on_capital'] < min_return_on_capital:
                continue
            
            # Check sector
            if stock.get('sector') in excluded_sectors:
                continue
            
            filtered.append(stock)
        
        return filtered
    
    def _rank_stocks(self, stocks: List[Dict]) -> List[Dict]:
        """
        Rank stocks using Magic Formula method
        
        Method:
        1. Rank by Earnings Yield (lower rank = better)
        2. Rank by Return on Capital (lower rank = better)
        3. Combined rank = sum of both ranks
        4. Sort by combined rank (lower = better)
        """
        if not stocks:
            return []
        
        # Rank by Earnings Yield (descending - higher is better)
        ey_sorted = sorted(stocks, key=lambda x: x['earnings_yield'], reverse=True)
        for rank, stock in enumerate(ey_sorted, 1):
            stock['ey_rank'] = rank
        
        # Rank by Return on Capital (descending - higher is better)
        roc_sorted = sorted(stocks, key=lambda x: x['return_on_capital'], reverse=True)
        for rank, stock in enumerate(roc_sorted, 1):
            stock['roc_rank'] = rank
        
        # Combined Magic Formula score (lower is better)
        for stock in stocks:
            stock['magic_formula_score'] = stock['ey_rank'] + stock['roc_rank']
        
        # Sort by Magic Formula score (ascending - lower is better)
        ranked = sorted(stocks, key=lambda x: x['magic_formula_score'])
        
        # Add final rank
        for rank, stock in enumerate(ranked, 1):
            stock['rank'] = rank
        
        return ranked
    
    def get_stock_count(self, db: Session, year: int, month: Optional[int] = None) -> int:
        """
        Get count of stocks available for a given year/month
        """
        if month is None:
            # When month is None, count all records for that year
            count = db.query(StockData).filter(
                StockData.year == year
            ).count()
        else:
            # When month is specified, count for that specific month
            count = db.query(StockData).filter(
                and_(
                    StockData.year == year,
                    StockData.month == month
                )
            ).count()
        
        return count
    
    def get_available_periods(self, db: Session) -> List[Dict]:
        """
        Get list of available year/month combinations in database
        Useful for UI to show what data is available
        """
        from sqlalchemy import func, distinct
        
        # Get distinct year/month combinations
        periods = db.query(
            StockData.year,
            StockData.month,
            func.count(StockData.id).label('stock_count'),
            func.max(StockData.updated_at).label('last_updated')
        ).group_by(
            StockData.year,
            StockData.month
        ).order_by(
            StockData.year.desc(),
            StockData.month.desc()
        ).all()
        
        result = []
        for period in periods:
            period_str = f"{period.year}-{period.month:02d}" if period.month else f"{period.year}"
            result.append({
                'year': period.year,
                'month': period.month,
                'period': period_str,
                'stock_count': period.stock_count,
                'last_updated': period.last_updated
            })
        
        return result

# Global instance
dynamic_magic_formula = DynamicMagicFormulaService()
