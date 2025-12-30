"""
FAST API Routes for Dynamic Magic Formula Ranking
Reads ALL stocks from database, applies Magic Formula dynamically
Fast responses with flexible filtering
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.models.database import StockData, get_db
from app.services.dynamic_magic_formula import dynamic_magic_formula
from app.services.keycloak_auth import get_current_user
from app.core.config import settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/top/year/{year}")
async def get_top_stocks_by_year(
    year: int,
    top_n: int = Query(default=10, ge=1, le=500, description="Number of top stocks to return"),
    min_earnings_yield: float = Query(default=0.0, description="Minimum earnings yield filter"),
    min_return_on_capital: float = Query(default=0.0, description="Minimum return on capital filter"),
    min_market_cap: float = Query(default=settings.MIN_MARKET_CAP, description="Minimum market cap filter"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get top N stocks for a year using DYNAMIC Magic Formula ranking
    
    - Reads ALL stocks from database for the year
    - Applies Magic Formula ranking dynamically
    - Supports flexible filtering
    - Fast response (<1 second for 10,000+ stocks)
    
    Query Parameters:
    - top_n: Number of top stocks (1-500)
    - min_earnings_yield: Minimum earnings yield % (default: 0)
    - min_return_on_capital: Minimum return on capital % (default: 0)
    - min_market_cap: Minimum market cap in $ (default: 1B)
    """
    logger.info(f"User {current_user['username']} requesting top {top_n} stocks for {year}")
    logger.info(f"Filters: EY>={min_earnings_yield}%, ROC>={min_return_on_capital}%, Market Cap>=${min_market_cap}")
    
    # Validate year
    current_year = datetime.now().year
    if year < 2000 or year > current_year:
        raise HTTPException(status_code=400, detail=f"Year must be between 2000 and {current_year}")
    
    # Check if data exists
    stock_count = dynamic_magic_formula.get_stock_count(db, year=year, month=None)
    if stock_count == 0:
        raise HTTPException(
            status_code=404, 
            detail=f"No data available for {year}. Background job may still be processing. Check /periods for available data."
        )
    
    logger.info(f"📊 Found {stock_count} stocks in database for {year}")
    
    # Apply Magic Formula dynamically
    top_stocks = dynamic_magic_formula.get_top_stocks(
        db=db,
        year=year,
        month=None,
        top_n=top_n,
        min_earnings_yield=min_earnings_yield,
        min_return_on_capital=min_return_on_capital,
        min_market_cap=min_market_cap
    )
    
    if not top_stocks:
        raise HTTPException(
            status_code=404,
            detail=f"No stocks match the criteria for {year}. Try relaxing filters."
        )
    
    logger.info(f"✅ Returned {len(top_stocks)} stocks after dynamic Magic Formula ranking")
    
    return {
        "year": year,
        "month": None,
        "top_n": top_n,
        "total_in_database": stock_count,
        "total_after_filter": len(top_stocks),
        "stocks": top_stocks,
        "filters_applied": {
            "min_earnings_yield": min_earnings_yield,
            "min_return_on_capital": min_return_on_capital,
            "min_market_cap": min_market_cap
        },
        "generated_at": datetime.now().isoformat()
    }

@router.get("/top/monthly/{year}/{month}")
async def get_top_stocks_by_month(
    year: int,
    month: int,
    top_n: int = Query(default=10, ge=1, le=500, description="Number of top stocks to return"),
    min_earnings_yield: float = Query(default=0.0, description="Minimum earnings yield filter"),
    min_return_on_capital: float = Query(default=0.0, description="Minimum return on capital filter"),
    min_market_cap: float = Query(default=settings.MIN_MARKET_CAP, description="Minimum market cap filter"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get top N stocks for a specific month using DYNAMIC Magic Formula ranking
    
    - Reads ALL stocks from database for the year/month
    - Applies Magic Formula ranking dynamically
    - Supports flexible filtering
    
    Query Parameters:
    - top_n: Number of top stocks (1-500)
    - min_earnings_yield: Minimum earnings yield % (default: 0)
    - min_return_on_capital: Minimum return on capital % (default: 0)
    - min_market_cap: Minimum market cap in $ (default: 1B)
    """
    logger.info(f"User {current_user['username']} requesting top {top_n} stocks for {year}-{month:02d}")
    logger.info(f"Filters: EY>={min_earnings_yield}%, ROC>={min_return_on_capital}%, Market Cap>=${min_market_cap}")
    
    # Validate
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
    
    current_year = datetime.now().year
    if year < 2000 or year > current_year:
        raise HTTPException(status_code=400, detail=f"Year must be between 2000 and {current_year}")
    
    # Check if monthly data exists
    stock_count = dynamic_magic_formula.get_stock_count(db, year=year, month=month)
    
    # If no monthly data, fall back to yearly
    if stock_count == 0:
        logger.info(f"No monthly data for {year}-{month:02d}, falling back to yearly data")
        stock_count = dynamic_magic_formula.get_stock_count(db, year=year, month=None)
        used_month = None
    else:
        used_month = month
    
    if stock_count == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No data available for {year}. Background job may still be processing. Check /periods for available data."
        )
    
    logger.info(f"📊 Found {stock_count} stocks in database for {year}{f'-{month:02d}' if used_month else ''}")
    
    # Apply Magic Formula dynamically
    top_stocks = dynamic_magic_formula.get_top_stocks(
        db=db,
        year=year,
        month=used_month,
        top_n=top_n,
        min_earnings_yield=min_earnings_yield,
        min_return_on_capital=min_return_on_capital,
        min_market_cap=min_market_cap
    )
    
    if not top_stocks:
        raise HTTPException(
            status_code=404,
            detail=f"No stocks match the criteria for {year}-{month:02d}. Try relaxing filters."
        )
    
    logger.info(f"✅ Returned {len(top_stocks)} stocks after dynamic Magic Formula ranking")
    
    return {
        "year": year,
        "month": used_month,
        "requested_month": month,
        "fallback_to_yearly": (used_month is None and month is not None),
        "top_n": top_n,
        "total_in_database": stock_count,
        "total_after_filter": len(top_stocks),
        "stocks": top_stocks,
        "filters_applied": {
            "min_earnings_yield": min_earnings_yield,
            "min_return_on_capital": min_return_on_capital,
            "min_market_cap": min_market_cap
        },
        "generated_at": datetime.now().isoformat()
    }

@router.get("/periods")
async def get_available_periods(
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of available year/month combinations in database
    Useful for UI to show what data user can query
    """
    periods = dynamic_magic_formula.get_available_periods(db)
    
    return {
        "available_periods": periods,
        "total_periods": len(periods),
        "generated_at": datetime.now().isoformat()
    }

@router.get("/completion")
async def get_completion_status(
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get completion status for all years
    Shows which years are complete, in progress, or have failures
    Critical for UI to show data quality and completeness
    """
    from app.models.database import YearCompletion
    
    # Get all year completions ordered by year descending
    completions = db.query(YearCompletion).order_by(YearCompletion.year.desc()).all()
    
    status_list = []
    for comp in completions:
        period_str = f"{comp.year}-{comp.month:02d}" if comp.month else f"{comp.year}"
        
        status_list.append({
            "year": comp.year,
            "month": comp.month,
            "period": period_str,
            "status": comp.status,
            "total_symbols": comp.total_symbols,
            "successful_fetches": comp.successful_fetches,
            "pending_retries": comp.pending_retries,
            "permanently_failed": comp.permanently_failed,
            "completion_percentage": round(comp.completion_percentage, 2),
            "is_complete": comp.status in ['completed', 'completed_with_failures'],
            "started_at": comp.started_at.isoformat() if comp.started_at else None,
            "completed_at": comp.completed_at.isoformat() if comp.completed_at else None,
            "updated_at": comp.updated_at.isoformat() if comp.updated_at else None
        })
    
    # Calculate overall statistics
    total_years = len(status_list)
    completed_years = sum(1 for s in status_list if s['is_complete'])
    in_progress_years = sum(1 for s in status_list if s['status'] == 'in_progress')
    total_pending_retries = sum(s['pending_retries'] for s in status_list)
    
    return {
        "year_completions": status_list,
        "summary": {
            "total_years": total_years,
            "completed_years": completed_years,
            "in_progress_years": in_progress_years,
            "total_pending_retries": total_pending_retries,
            "overall_health": "healthy" if total_pending_retries < 100 else "needs_attention"
        },
        "generated_at": datetime.now().isoformat()
    }

# Legacy endpoint maintained for backward compatibility (removed later)
@router.get("/legacy/top/year/{year}")
async def get_cached_top_stocks_legacy(
    year: int,
    top_n: int = Query(default=10, ge=1, le=100),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    DEPRECATED: Legacy endpoint that returns pre-cached rankings
    Use /top/year/{year} instead for dynamic ranking with filters
    """
    logger.warning("Legacy endpoint called - redirect to /top/year/{year}")
    return await get_top_stocks_by_year(
        year=year,
        top_n=top_n,
        min_earnings_yield=0.0,
        min_return_on_capital=0.0,
        min_market_cap=settings.MIN_MARKET_CAP,
        current_user=current_user,
        db=db
    )
