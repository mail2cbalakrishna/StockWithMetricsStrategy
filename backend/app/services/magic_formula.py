"""Magic Formula Implementation"""
from typing import List, Dict, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)

from app.models.database import StockData
from app.services.cache_service import CacheService
from app.core.config import settings

class MagicFormulaService:
    def __init__(self, cache_service: CacheService):
        self.cache_service = cache_service
        self.min_market_cap = settings.MIN_MARKET_CAP
    
    def calculate_earnings_yield(self, ebit: float, enterprise_value: float) -> Optional[float]:
        if enterprise_value <= 0 or pd.isna(ebit) or pd.isna(enterprise_value):
            return None
        return (ebit / enterprise_value) * 100
    
    def calculate_return_on_capital(self, ebit: float, tangible_capital: float) -> Optional[float]:
        if tangible_capital <= 0 or pd.isna(ebit) or pd.isna(tangible_capital):
            return None
        return (ebit / tangible_capital) * 100
    
    def rank_stocks(self, stocks_data: List[Dict]) -> List[Dict]:
        if not stocks_data:
            return []
        
        df = pd.DataFrame(stocks_data)
        df = df[df['earnings_yield'].notna() & df['return_on_capital'].notna()]
        
        if df.empty:
            return []
        
        df['ey_rank'] = df['earnings_yield'].rank(ascending=False, method='average')
        df['roc_rank'] = df['return_on_capital'].rank(ascending=False, method='average')
        df['magic_formula_rank'] = df['ey_rank'] + df['roc_rank']
        df = df.sort_values('magic_formula_rank')
        df['rank'] = range(1, len(df) + 1)
        
        return df.to_dict('records')
    
    def filter_by_criteria(self, stocks_data: List[Dict]) -> List[Dict]:
        filtered = []
        for stock in stocks_data:
            if stock.get('market_cap', 0) < self.min_market_cap:
                continue
            if stock.get('ebit', 0) <= 0:
                continue
            sector = stock.get('sector', '').lower()
            if sector in ['financials', 'financial services', 'utilities']:
                continue
            filtered.append(stock)
        return filtered
    
    def get_top_stocks(self, stocks_data: List[Dict], top_n: int = 10) -> List[Dict]:
        filtered_stocks = self.filter_by_criteria(stocks_data)
        ranked_stocks = self.rank_stocks(filtered_stocks)
        return ranked_stocks[:top_n]

# Instantiate for use in admin router
from app.services.cache_service import cache_service
magic_formula = MagicFormulaService(cache_service)
