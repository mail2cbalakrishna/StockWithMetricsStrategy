"""Redis Cache Service"""
import redis
import json
from typing import Optional, List, Dict
from datetime import datetime
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self):
        self.redis = None
        self._initialized = False
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis connection with retry logic"""
        if self._initialized:
            return
        
        redis_host = settings.REDIS_HOST
        redis_port = settings.REDIS_PORT
        
        try:
            self.redis = redis.Redis(
                host=redis_host, port=redis_port,
                decode_responses=True, socket_connect_timeout=5
            )
            ping_result = self.redis.ping()
            logger.info(f"✅ Redis connected: {redis_host}:{redis_port}")
            self._initialized = True
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            logger.error(f"   Tried to connect to {redis_host}:{redis_port}")
            self.redis = None
            self._initialized = False
    
    def get_cached_stocks(self, year: int) -> Optional[List[Dict]]:
        if not self.redis:
            return None
        try:
            data = self.redis.get(f"stocks:year:{year}:all")
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Cache read error: {e}")
            return None
    
    def cache_stocks(self, year: int, stocks: List[Dict], metadata: Dict = None, ttl: int = 86400):
        if not self.redis:
            return False
        try:
            cache_data = {
                "year": year, "stocks": stocks,
                "total_analyzed": len(stocks),
                "cached_at": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            self.redis.setex(f"stocks:year:{year}:all", ttl, json.dumps(cache_data))
            return True
        except Exception as e:
            logger.error(f"Cache write error: {e}")
            return False
    
    def get_cached_monthly_stocks(self, year: int, month: int) -> Optional[List[Dict]]:
        if not self.redis:
            return None
        try:
            data = self.redis.get(f"stocks:monthly:{year}:{month}:all")
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Cache read error: {e}")
            return None
    
    def cache_monthly_stocks(self, year: int, month: int, stocks: List[Dict], metadata: Dict = None, ttl: int = 86400):
        if not self.redis:
            return False
        try:
            cache_data = {
                "year": year, "month": month, "stocks": stocks,
                "total_analyzed": len(stocks),
                "cached_at": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            self.redis.setex(f"stocks:monthly:{year}:{month}:all", ttl, json.dumps(cache_data))
            return True
        except Exception as e:
            logger.error(f"Cache write error: {e}")
            return False
    
    def invalidate_cache(self, year: int):
        if not self.redis:
            return False
        try:
            self.redis.delete(f"stocks:year:{year}:all")
            return True
        except:
            return False
    
    def get_cache_stats(self) -> Dict:
        # Try to reconnect if needed
        if not self.redis:
            self.reconnect()
        
        if not self.redis:
            return {"status": "unavailable", "message": "Redis not connected"}
        
        try:
            # Get number of keys
            dbsize = self.redis.dbsize()
            
            # Get memory usage
            mem_info = self.redis.info('memory')
            memory_usage = mem_info.get('used_memory_human', 'N/A')
            
            # Get all cache keys
            keys = self.redis.keys('stocks:*')
            
            logger.info(f"Cache stats: {dbsize} keys, {len(keys)} cache keys, {memory_usage} memory")
            
            return {
                "status": "connected",
                "total_keys": dbsize,
                "cache_keys": len(keys),
                "memory_usage": memory_usage,
                "keys_sample": [k for k in keys[:5]]  # Show first 5 keys
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"status": "error", "error": str(e)}
    
    def health_check(self) -> bool:
        if not self.redis:
            return False
        try:
            return self.redis.ping()
        except:
            return False
    
    def reconnect(self):
        """Try to reconnect to Redis if connection was lost"""
        self._initialize_redis()
        return self.redis is not None

cache_service = CacheService()
