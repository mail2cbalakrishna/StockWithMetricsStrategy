"""
Admin endpoints for cache management
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict
from app.services.keycloak_auth import get_current_user
from app.services.stock_data_service import stock_data_service
from app.services.magic_formula import magic_formula
from app.services.cache_service import cache_service
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/warm-cache/{year}")
async def warm_cache_for_year(
    year: int,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """
    Admin endpoint: Warm up cache for a specific year
    Fetches ALL 503 stocks and caches the results
    Runs in background so you get immediate response
    """
    
    logger.info(f"User {current_user['username']} requested cache warm-up for {year}")
    
    # Validate year
    current_year = datetime.now().year
    if year < 2000 or year > current_year:
        raise HTTPException(status_code=400, detail=f"Year must be between 2000 and {current_year}")
    
    # Add background task
    background_tasks.add_task(fetch_and_cache_year, year)
    
    return {
        "message": f"Cache warm-up started for {year}",
        "year": year,
        "status": "running_in_background",
        "estimated_time": "3-5 minutes",
        "note": "You'll get instant results once complete"
    }

async def fetch_and_cache_year(year: int):
    """Background task to fetch ALL stocks and cache them"""
    try:
        logger.info(f"🚀 Starting cache warm-up for {year} - fetching ALL 503 stocks...")
        
        # Get ALL S&P 500 symbols
        symbols = stock_data_service.get_sp500_symbols()
        total_symbols = len(symbols)
        logger.info(f"Retrieved {total_symbols} symbols")
        
        # Fetch ALL stocks (no limit)
        stocks_data = await stock_data_service.fetch_multiple_stocks(symbols, year)
        
        if not stocks_data:
            logger.error(f"❌ No stock data retrieved for {year}")
            return
        
        # Apply Magic Formula
        filtered_stocks = magic_formula.filter_by_criteria(stocks_data)
        ranked_stocks = magic_formula.rank_stocks(filtered_stocks)
        
        # Cache the results
        success = cache_service.cache_stocks(
            year=year,
            stocks=ranked_stocks,
            metadata={
                "total_symbols": total_symbols,
                "successful_fetches": len(stocks_data),
                "passed_criteria": len(ranked_stocks),
                "warm_up_completed_at": datetime.now().isoformat()
            },
            ttl=86400  # 24 hours
        )
        
        if success:
            logger.info(f"✅ Cache warm-up complete for {year}: {len(ranked_stocks)} stocks cached")
        else:
            logger.error(f"❌ Failed to cache results for {year}")
            
    except Exception as e:
        logger.error(f"❌ Error in cache warm-up for {year}: {e}", exc_info=True)

@router.get("/cache/stats")
async def get_cache_stats(current_user: Dict = Depends(get_current_user)):
    """Get cache statistics"""
    stats = cache_service.get_cache_stats()
    return {
        "cache": stats,
        "healthy": cache_service.health_check()
    }

@router.delete("/cache/invalidate/{year}")
async def invalidate_cache(
    year: int,
    current_user: Dict = Depends(get_current_user)
):
    """Manually invalidate cache for a year"""
    success = cache_service.invalidate_cache(year)
    
    if success:
        return {"message": f"Cache invalidated for {year}"}
    else:
        raise HTTPException(status_code=500, detail="Failed to invalidate cache")
