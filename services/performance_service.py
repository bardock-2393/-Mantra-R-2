"""
Performance Monitoring and Optimization Service
Tracks and optimizes system performance for sub-1000ms latency
"""

import time
import functools
import threading
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
import json
from collections import defaultdict, deque
import redis
from config import Config

@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""
    operation: str
    start_time: float
    end_time: float
    duration: float
    metadata: Dict = None
    
    def to_dict(self):
        return asdict(self)

class PerformanceMonitor:
    """Real-time performance monitoring and optimization"""
    
    def __init__(self):
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.redis_client = None
        self.lock = threading.Lock()
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis connection for caching"""
        try:
            self.redis_client = redis.from_url(Config.REDIS_URL, decode_responses=True)
            self.redis_client.ping()
            print("📊 Performance monitor: Redis connected")
        except Exception as e:
            print(f"⚠️ Performance monitor: Redis connection failed: {e}")
    
    def measure_performance(self, operation: str, metadata: Dict = None):
        """Decorator to measure function performance"""
        def decorator(func: Callable):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    # Record metrics
                    metric = PerformanceMetrics(
                        operation=operation,
                        start_time=start_time,
                        end_time=end_time,
                        duration=duration,
                        metadata=metadata or {}
                    )
                    self._record_metric(metric)
                    
                    # Log if exceeds target latency
                    if duration > 1.0:  # 1000ms target
                        print(f"⚠️ LATENCY WARNING: {operation} took {duration:.3f}s (target: <1.0s)")
                    else:
                        print(f"✅ PERFORMANCE: {operation} completed in {duration:.3f}s")
                    
                    return result
                except Exception as e:
                    end_time = time.time()
                    duration = end_time - start_time
                    print(f"❌ ERROR: {operation} failed after {duration:.3f}s: {e}")
                    raise
            
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    # Record metrics
                    metric = PerformanceMetrics(
                        operation=operation,
                        start_time=start_time,
                        end_time=end_time,
                        duration=duration,
                        metadata=metadata or {}
                    )
                    self._record_metric(metric)
                    
                    # Log if exceeds target latency
                    if duration > 1.0:  # 1000ms target
                        print(f"⚠️ LATENCY WARNING: {operation} took {duration:.3f}s (target: <1.0s)")
                    else:
                        print(f"✅ PERFORMANCE: {operation} completed in {duration:.3f}s")
                    
                    return result
                except Exception as e:
                    end_time = time.time()
                    duration = end_time - start_time
                    print(f"❌ ERROR: {operation} failed after {duration:.3f}s: {e}")
                    raise
            
            return async_wrapper if hasattr(func, '__call__') and hasattr(func, '__code__') and func.__code__.co_flags & 0x080 else sync_wrapper
        return decorator
    
    def _record_metric(self, metric: PerformanceMetrics):
        """Record performance metric"""
        with self.lock:
            self.metrics[metric.operation].append(metric)
        
        # Cache in Redis for dashboard
        if self.redis_client:
            try:
                key = f"perf:{metric.operation}:latest"
                self.redis_client.setex(key, 3600, json.dumps(metric.to_dict()))
            except Exception as e:
                print(f"⚠️ Failed to cache performance metric: {e}")
    
    def get_latency_stats(self, operation: str = None) -> Dict:
        """Get latency statistics"""
        stats = {}
        
        operations = [operation] if operation else self.metrics.keys()
        
        for op in operations:
            if op in self.metrics and self.metrics[op]:
                durations = [m.duration for m in self.metrics[op]]
                stats[op] = {
                    'count': len(durations),
                    'avg_latency': sum(durations) / len(durations),
                    'min_latency': min(durations),
                    'max_latency': max(durations),
                    'p95_latency': sorted(durations)[int(len(durations) * 0.95)] if len(durations) > 0 else 0,
                    'under_1000ms': len([d for d in durations if d < 1.0]),
                    'success_rate': len([d for d in durations if d < 1.0]) / len(durations) * 100
                }
        
        return stats
    
    def check_performance_targets(self) -> Dict:
        """Check if system meets Round 2 performance targets"""
        stats = self.get_latency_stats()
        targets = {
            'latency_target_ms': 1000,
            'success_rate_target': 95.0,
            'passing': True,
            'operations': {}
        }
        
        for op, data in stats.items():
            op_passing = (
                data['avg_latency'] < 1.0 and 
                data['success_rate'] >= 95.0
            )
            targets['operations'][op] = {
                'avg_latency_ms': data['avg_latency'] * 1000,
                'success_rate': data['success_rate'],
                'passing': op_passing
            }
            if not op_passing:
                targets['passing'] = False
        
        return targets

class CacheManager:
    """High-performance caching for video analysis results"""
    
    def __init__(self):
        self.redis_client = None
        self.local_cache = {}
        self.cache_ttl = 3600  # 1 hour
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(Config.REDIS_URL, decode_responses=True)
            self.redis_client.ping()
            print("🗄️ Cache manager: Redis connected")
        except Exception as e:
            print(f"⚠️ Cache manager: Redis connection failed: {e}")
    
    def get_cache_key(self, video_path: str, operation: str, **kwargs) -> str:
        """Generate cache key for video operations"""
        import hashlib
        # Create unique key based on file path, operation, and parameters
        key_data = f"{video_path}:{operation}:{sorted(kwargs.items())}"
        return f"cache:{hashlib.md5(key_data.encode()).hexdigest()}"
    
    def get(self, key: str):
        """Get cached result"""
        # Try Redis first
        if self.redis_client:
            try:
                cached = self.redis_client.get(key)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                print(f"⚠️ Redis cache get failed: {e}")
        
        # Fallback to local cache
        return self.local_cache.get(key)
    
    def set(self, key: str, value, ttl: int = None):
        """Set cached result"""
        ttl = ttl or self.cache_ttl
        
        # Store in Redis
        if self.redis_client:
            try:
                self.redis_client.setex(key, ttl, json.dumps(value))
            except Exception as e:
                print(f"⚠️ Redis cache set failed: {e}")
        
        # Store in local cache as backup
        self.local_cache[key] = value
        
        # Prevent local cache from growing too large
        if len(self.local_cache) > 100:
            # Remove oldest 20% of entries
            keys_to_remove = list(self.local_cache.keys())[:20]
            for k in keys_to_remove:
                del self.local_cache[k]
    
    def clear(self, pattern: str = None):
        """Clear cache entries"""
        if pattern:
            # Clear specific pattern
            if self.redis_client:
                try:
                    keys = self.redis_client.keys(f"cache:{pattern}*")
                    if keys:
                        self.redis_client.delete(*keys)
                except Exception as e:
                    print(f"⚠️ Redis cache clear failed: {e}")
            
            # Clear from local cache
            keys_to_remove = [k for k in self.local_cache.keys() if pattern in k]
            for k in keys_to_remove:
                del self.local_cache[k]
        else:
            # Clear all
            if self.redis_client:
                try:
                    keys = self.redis_client.keys("cache:*")
                    if keys:
                        self.redis_client.delete(*keys)
                except Exception as e:
                    print(f"⚠️ Redis cache clear failed: {e}")
            
            self.local_cache.clear()

# Global instances
performance_monitor = PerformanceMonitor()
cache_manager = CacheManager()

# Convenience decorators
def measure_latency(operation: str, metadata: Dict = None):
    """Convenience decorator for measuring latency"""
    return performance_monitor.measure_performance(operation, metadata)

def get_performance_stats() -> Dict:
    """Get current performance statistics"""
    return performance_monitor.get_latency_stats()

def check_round2_compliance() -> Dict:
    """Check Round 2 performance compliance"""
    return performance_monitor.check_performance_targets()