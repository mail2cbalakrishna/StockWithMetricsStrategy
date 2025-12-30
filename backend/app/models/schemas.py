"""
Pydantic Models for API Responses
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class StockRanking(BaseModel):
    """Stock with Magic Formula ranking"""
    symbol: str
    name: str
    sector: str
    market_cap: float
    ebit: Optional[float]
    earnings_yield: Optional[float]
    return_on_capital: Optional[float]
    rank: int
    magic_formula_rank: float
    current_price: float
    year: int
    month: Optional[int] = None

class TopStocksResponse(BaseModel):
    """Response for top stocks by year"""
    year: int
    top_n: int
    total_analyzed: int
    stocks: List[Dict]
    generated_at: str

class MonthlyStocksResponse(BaseModel):
    """Response for monthly top stocks"""
    year: int
    month: int
    top_n: int
    total_analyzed: int
    stocks: List[Dict]
    generated_at: str

class UserInfo(BaseModel):
    """User information from Keycloak"""
    username: str
    email: Optional[str]
    roles: List[str]
