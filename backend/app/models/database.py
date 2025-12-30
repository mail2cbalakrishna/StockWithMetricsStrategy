"""
Database Models for Stock Data Storage
Stores ALL stocks with complete financial data - Magic Formula applied dynamically on query
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Index, create_engine, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.core.config import settings

Base = declarative_base()

class StockData(Base):
    """
    Comprehensive stock data storage - ALL stocks, ALL years, ALL months
    Magic Formula ranking calculated dynamically when queried, NOT stored
    """
    __tablename__ = 'stock_data'
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Stock identification
    symbol = Column(String(10), nullable=False, index=True)
    company_name = Column(String(255), nullable=False)
    sector = Column(String(100))
    
    # Time period - year is required, month is optional (NULL = yearly data)
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=True, index=True)  # 1-12 or NULL for full year
    
    # Financial metrics for Magic Formula calculation
    ebit = Column(Float, nullable=False)  # Earnings Before Interest & Tax
    enterprise_value = Column(Float, nullable=False)
    tangible_capital = Column(Float, nullable=False)
    
    # Calculated metrics (stored for convenience, but can be recalculated)
    earnings_yield = Column(Float, nullable=False)  # EBIT / Enterprise Value * 100
    return_on_capital = Column(Float, nullable=False)  # EBIT / Tangible Capital * 100
    
    # Market data
    market_cap = Column(Float, nullable=False)
    current_price = Column(Float)
    
    # Data source tracking
    data_source = Column(String(50))  # 'yfinance', 'alpha_vantage', 'polygon'
    
    # Timestamps
    fetched_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for fast queries
    __table_args__ = (
        # Unique constraint: one record per symbol + year + month combination
        UniqueConstraint('symbol', 'year', 'month', name='uix_symbol_year_month'),
        
        # Query optimization indexes
        Index('idx_year', 'year'),
        Index('idx_year_month', 'year', 'month'),
        Index('idx_symbol_year', 'symbol', 'year'),
        Index('idx_earnings_yield', 'earnings_yield'),
        Index('idx_return_on_capital', 'return_on_capital'),
    )


class FailedStock(Base):
    """
    Track failed stock fetches for retry mechanism
    Ensures NO stock is permanently lost - keeps retrying until success
    """
    __tablename__ = 'failed_stocks'
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Stock identification
    symbol = Column(String(10), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=True, index=True)  # NULL for yearly data
    
    # Failure tracking
    error_message = Column(String(1000))  # Last error message
    retry_count = Column(Integer, default=0)  # Number of retry attempts
    max_retries = Column(Integer, default=5)  # Maximum retry attempts
    
    # Status: 'pending', 'retrying', 'failed', 'completed'
    status = Column(String(20), default='pending', index=True)
    
    # Timing
    first_attempt = Column(DateTime, default=datetime.utcnow)
    last_attempt = Column(DateTime, default=datetime.utcnow)
    next_retry = Column(DateTime, nullable=True, index=True)  # When to retry next
    completed_at = Column(DateTime, nullable=True)
    
    # Indexes
    __table_args__ = (
        UniqueConstraint('symbol', 'year', 'month', name='uix_failed_symbol_year_month'),
        Index('idx_status_next_retry', 'status', 'next_retry'),
        Index('idx_year_status', 'year', 'status'),
    )


class YearCompletion(Base):
    """
    Track completion status for each year
    Shows which years are 100% complete vs still have pending/failed stocks
    """
    __tablename__ = 'year_completion'
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Year tracking
    year = Column(Integer, nullable=False, unique=True, index=True)
    month = Column(Integer, nullable=True, index=True)  # NULL for yearly data
    
    # Statistics
    total_symbols = Column(Integer, default=0)  # Total symbols to fetch
    successful_fetches = Column(Integer, default=0)  # Successfully fetched
    pending_retries = Column(Integer, default=0)  # Still retrying
    permanently_failed = Column(Integer, default=0)  # Failed after max retries
    
    # Completion percentage
    completion_percentage = Column(Float, default=0.0)  # 0-100
    
    # Status: 'in_progress', 'completed', 'completed_with_failures'
    status = Column(String(50), default='in_progress')
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Database connection - use Keycloak database
DATABASE_URL = settings.DATABASE_URL
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
