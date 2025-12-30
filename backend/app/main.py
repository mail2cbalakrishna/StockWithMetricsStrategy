"""
Stock With Metrics Strategy - Magic Formula Stock Analysis
Author: Balakrishna C
License: MIT
Copyright (c) 2025 Balakrishna C

FastAPI Backend for Magic Formula Stock Analysis
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import stocks, admin
from app.core.config import settings
from app.models.database import init_db
from app.services.background_processor import background_processor
from app.services.continuous_fetcher import continuous_fetcher
import logging
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Magic Formula Stock Analysis API",
    description="Stock ranking using Magic Formula",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stocks.router, prefix="/api/stocks", tags=["stocks"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Magic Formula API v2.0")
    init_db()
    
    # Start continuous fetcher (1 stock/minute = 60/hour = 1440/day)
    # Will run for 1 WEEK to collect all stocks for years 2017-2024
    logger.info("="*70)
    logger.info("🚀 Starting Continuous Stock Fetcher")
    logger.info("Strategy: 1 stock per minute")
    logger.info("Rate: 60 stocks/hour, 1,440 stocks/day")
    logger.info("Duration: Running for 1 WEEK to complete data collection")
    logger.info("Target: ~516 stocks × 8 years = ~4,128 records")
    logger.info("Years: 2017-2024 (8 years)")
    logger.info("="*70)
    asyncio.create_task(continuous_fetcher.run_continuous())
    
    # DISABLED: background_processor (stopped for 1 WEEK while continuous_fetcher runs)
    # background_processor runs in large batches and hits rate limits
    # continuous_fetcher is slower but respects API limits (1 stock/min)
    # After 3 days, re-enable it and disable continuous_fetcher
    # asyncio.create_task(background_processor.run_continuous())

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down...")
    # background_processor.stop()  # Disabled for now

@app.get("/")
async def root():
    return {"message": "Magic Formula Stock Analysis API", "version": "1.0.0", "docs": "/docs"}

@app.get("/health")
async def health_check():
    from app.services.cache_service import cache_service
    return {
        "status": "healthy",
        "cache": {
            "status": "connected" if cache_service.health_check() else "unavailable",
            "stats": cache_service.get_cache_stats()
        }
    }
