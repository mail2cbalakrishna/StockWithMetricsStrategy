"""
Application Configuration
"""
from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000", 
        "http://localhost:8080",
        "http://192.168.1.209:3000",
        "http://192.168.1.209:8080"
    ]
    
    # Keycloak Configuration
    KEYCLOAK_SERVER_URL: str = os.getenv("KEYCLOAK_SERVER_URL", "http://localhost:8081")
    KEYCLOAK_REALM: str = os.getenv("KEYCLOAK_REALM", "stock-analysis")
    KEYCLOAK_CLIENT_ID: str = os.getenv("KEYCLOAK_CLIENT_ID", "stock-analysis-client")
    KEYCLOAK_CLIENT_SECRET: str = os.getenv("KEYCLOAK_CLIENT_SECRET", "your-client-secret")
    
    # API Keys for Stock Data Sources
    ALPHA_VANTAGE_API_KEY: str = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")
    POLYGON_API_KEY: str = os.getenv("POLYGON_API_KEY", "")
    
    # Rate Limits (requests per hour)
    YFINANCE_RATE_LIMIT: int = 100
    ALPHA_VANTAGE_RATE_LIMIT: int = 25
    POLYGON_RATE_LIMIT: int = 50
    
    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://keycloak:keycloak_password@postgres:5432/keycloak")
    
    # Magic Formula Parameters
    MIN_MARKET_CAP: float = 1_000_000_000  # $1B minimum
    EXCLUDE_FINANCIALS: bool = True
    EXCLUDE_UTILITIES: bool = True
    EXCLUDED_SECTORS: list = ["Financial Services", "Financial", "Utilities"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

settings = Settings()
