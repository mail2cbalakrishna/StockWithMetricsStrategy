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
        redis_host = settings.REDIS_HOST
        redis_port = settings.REDIS_PORT
        
        try:
            self.redis = redis.Redis(
                host=redis_host, port=redis_port,
                decode_responses=True, socket_connect_timeout=5
            )
            self.redis.ping()
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.redis = None
    
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
        if not self.redis:
            return {"status": "unavailable"}
        try:
            info = self.redis.info('stats')
            hits = info.get('keyspace_hits', 0)
            misses = info.get('keyspace_misses', 0)
            return {
                "status": "connected",
                "total_keys": self.redis.dbsize(),
                "hits": hits, "misses": misses,
                "hit_rate": hits / max(hits + misses, 1) * 100
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def health_check(self) -> bool:
        if not self.redis:
            return False
        try:
            return self.redis.ping()
        except:
            return False

cache_service = CacheService()
