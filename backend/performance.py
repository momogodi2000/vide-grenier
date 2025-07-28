# backend/performance.py
"""
Performance Monitoring and Optimization for VGK
Tracks query performance, response times, and provides optimization insights
"""

import time
import logging
from functools import wraps
from django.core.cache import cache
from django.db import connection
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Monitors application performance and provides insights"""
    
    def __init__(self):
        self.slow_query_threshold = getattr(settings, 'PERFORMANCE_SETTINGS', {}).get('SLOW_QUERY_THRESHOLD', 1.0)
        self.max_queries_threshold = getattr(settings, 'PERFORMANCE_SETTINGS', {}).get('MAX_QUERIES_PER_REQUEST', 20)
    
    def monitor_request(self, request, response):
        """Monitor request performance"""
        start_time = getattr(request, '_start_time', time.time())
        duration = time.time() - start_time
        
        # Get query count
        query_count = len(connection.queries)
        
        # Log slow requests
        if duration > self.slow_query_threshold:
            logger.warning(
                f"Slow request: {request.path} took {duration:.2f}s "
                f"with {query_count} queries"
            )
        
        # Log high query count
        if query_count > self.max_queries_threshold:
            logger.warning(
                f"High query count: {request.path} made {query_count} queries "
                f"in {duration:.2f}s"
            )
        
        # Store performance metrics
        self.store_performance_metrics(request.path, duration, query_count)
        
        return response
    
    def store_performance_metrics(self, path, duration, query_count):
        """Store performance metrics in cache for analysis"""
        try:
            metrics_key = f"performance_metrics_{path.replace('/', '_')}"
            metrics = cache.get(metrics_key, {
                'count': 0,
                'total_duration': 0,
                'total_queries': 0,
                'max_duration': 0,
                'max_queries': 0,
                'last_updated': timezone.now().isoformat()
            })
            
            metrics['count'] += 1
            metrics['total_duration'] += duration
            metrics['total_queries'] += query_count
            metrics['max_duration'] = max(metrics['max_duration'], duration)
            metrics['max_queries'] = max(metrics['max_queries'], query_count)
            metrics['last_updated'] = timezone.now().isoformat()
            
            cache.set(metrics_key, metrics, 3600)  # Cache for 1 hour
        except Exception as e:
            logger.error(f"Error storing performance metrics: {e}")
    
    def get_performance_report(self, path=None, hours=24):
        """Get performance report for analysis"""
        try:
            if path:
                metrics_key = f"performance_metrics_{path.replace('/', '_')}"
                metrics = cache.get(metrics_key)
                if metrics:
                    return {
                        'path': path,
                        'avg_duration': metrics['total_duration'] / metrics['count'],
                        'avg_queries': metrics['total_queries'] / metrics['count'],
                        'max_duration': metrics['max_duration'],
                        'max_queries': metrics['max_queries'],
                        'request_count': metrics['count'],
                        'last_updated': metrics['last_updated']
                    }
                return None
            
            # Get all performance metrics
            all_metrics = {}
            for key in cache.keys('performance_metrics_*'):
                metrics = cache.get(key)
                if metrics:
                    path_name = key.replace('performance_metrics_', '').replace('_', '/')
                    all_metrics[path_name] = {
                        'avg_duration': metrics['total_duration'] / metrics['count'],
                        'avg_queries': metrics['total_queries'] / metrics['count'],
                        'max_duration': metrics['max_duration'],
                        'max_queries': metrics['max_queries'],
                        'request_count': metrics['count']
                    }
            
            return all_metrics
        except Exception as e:
            logger.error(f"Error getting performance report: {e}")
            return None


class QueryOptimizer:
    """Analyzes and optimizes database queries"""
    
    def __init__(self):
        self.slow_queries = []
    
    def analyze_queries(self):
        """Analyze current queries for optimization opportunities"""
        try:
            queries = connection.queries
            analysis = {
                'total_queries': len(queries),
                'total_time': sum(float(q['time']) for q in queries),
                'slow_queries': [],
                'duplicate_queries': [],
                'n_plus_one_queries': []
            }
            
            # Find slow queries
            for query in queries:
                if float(query['time']) > 0.1:  # Queries taking more than 100ms
                    analysis['slow_queries'].append({
                        'sql': query['sql'],
                        'time': query['time'],
                        'count': 1
                    })
            
            # Find duplicate queries
            query_counts = {}
            for query in queries:
                sql = query['sql']
                if sql in query_counts:
                    query_counts[sql]['count'] += 1
                    query_counts[sql]['total_time'] += float(query['time'])
                else:
                    query_counts[sql] = {
                        'sql': sql,
                        'count': 1,
                        'total_time': float(query['time'])
                    }
            
            analysis['duplicate_queries'] = [
                q for q in query_counts.values() if q['count'] > 1
            ]
            
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing queries: {e}")
            return None
    
    def suggest_optimizations(self, analysis):
        """Suggest query optimizations based on analysis"""
        suggestions = []
        
        if analysis:
            # Suggest caching for slow queries
            for query in analysis['slow_queries']:
                if query['time'] > 0.5:  # Very slow queries
                    suggestions.append({
                        'type': 'cache',
                        'priority': 'high',
                        'message': f"Consider caching query taking {query['time']}s",
                        'query': query['sql'][:100] + '...'
                    })
            
            # Suggest select_related/prefetch_related for duplicate queries
            for query in analysis['duplicate_queries']:
                if query['count'] > 3:  # Many duplicates
                    suggestions.append({
                        'type': 'optimization',
                        'priority': 'medium',
                        'message': f"Query executed {query['count']} times, consider select_related/prefetch_related",
                        'query': query['sql'][:100] + '...'
                    })
            
            # Suggest database indexes
            if analysis['total_queries'] > 20:
                suggestions.append({
                    'type': 'index',
                    'priority': 'medium',
                    'message': f"High query count ({analysis['total_queries']}), consider adding database indexes"
                })
        
        return suggestions


class CacheOptimizer:
    """Optimizes cache usage and provides cache analytics"""
    
    def __init__(self):
        self.cache_stats = {}
    
    def analyze_cache_usage(self):
        """Analyze cache usage patterns"""
        try:
            # Get cache statistics (this would depend on your cache backend)
            stats = {
                'hits': 0,
                'misses': 0,
                'keys': 0,
                'memory_usage': 0
            }
            
            # In a real implementation, you'd get these from your cache backend
            # For Redis, you could use redis-cli info memory
            
            return stats
        except Exception as e:
            logger.error(f"Error analyzing cache usage: {e}")
            return None
    
    def suggest_cache_optimizations(self, stats):
        """Suggest cache optimizations"""
        suggestions = []
        
        if stats:
            hit_rate = stats['hits'] / (stats['hits'] + stats['misses']) if (stats['hits'] + stats['misses']) > 0 else 0
            
            if hit_rate < 0.8:  # Low cache hit rate
                suggestions.append({
                    'type': 'cache_strategy',
                    'priority': 'high',
                    'message': f"Low cache hit rate ({hit_rate:.2%}), consider adjusting cache keys or TTL"
                })
            
            if stats['memory_usage'] > 100 * 1024 * 1024:  # 100MB
                suggestions.append({
                    'type': 'cache_cleanup',
                    'priority': 'medium',
                    'message': f"High cache memory usage ({stats['memory_usage'] / 1024 / 1024:.1f}MB), consider cleanup"
                })
        
        return suggestions


def monitor_performance(func):
    """Decorator to monitor function performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_queries = len(connection.queries)
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start_time
            query_count = len(connection.queries) - start_queries
            
            # Log if function is slow
            if duration > 1.0:  # More than 1 second
                logger.warning(
                    f"Slow function: {func.__name__} took {duration:.2f}s "
                    f"with {query_count} queries"
                )
            
            # Store metrics
            monitor = PerformanceMonitor()
            monitor.store_performance_metrics(f"function_{func.__name__}", duration, query_count)
    
    return wrapper


def cache_result(timeout=300, key_func=None):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}_{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator


def optimize_queryset(queryset, select_related=None, prefetch_related=None, only=None):
    """Optimize queryset with common optimizations"""
    if select_related:
        queryset = queryset.select_related(*select_related)
    
    if prefetch_related:
        queryset = queryset.prefetch_related(*prefetch_related)
    
    if only:
        queryset = queryset.only(*only)
    
    return queryset


class DatabaseOptimizer:
    """Provides database optimization utilities"""
    
    @staticmethod
    def get_table_sizes():
        """Get sizes of database tables"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                        pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY size_bytes DESC;
                """)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting table sizes: {e}")
            return []
    
    @staticmethod
    def get_index_usage():
        """Get index usage statistics"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        idx_scan,
                        idx_tup_read,
                        idx_tup_fetch
                    FROM pg_stat_user_indexes 
                    ORDER BY idx_scan DESC;
                """)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting index usage: {e}")
            return []
    
    @staticmethod
    def get_slow_queries():
        """Get slow query statistics (requires pg_stat_statements extension)"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        query,
                        calls,
                        total_time,
                        mean_time,
                        rows
                    FROM pg_stat_statements 
                    ORDER BY mean_time DESC 
                    LIMIT 10;
                """)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting slow queries: {e}")
            return []


# Global instances
performance_monitor = PerformanceMonitor()
query_optimizer = QueryOptimizer()
cache_optimizer = CacheOptimizer()
database_optimizer = DatabaseOptimizer()


def get_performance_summary():
    """Get a summary of current performance metrics"""
    try:
        # Get recent performance data
        report = performance_monitor.get_performance_report()
        
        # Get query analysis
        query_analysis = query_optimizer.analyze_queries()
        
        # Get cache analysis
        cache_stats = cache_optimizer.analyze_cache_usage()
        
        summary = {
            'timestamp': timezone.now().isoformat(),
            'performance_report': report,
            'query_analysis': query_analysis,
            'cache_stats': cache_stats,
            'optimization_suggestions': []
        }
        
        # Add suggestions
        if query_analysis:
            summary['optimization_suggestions'].extend(
                query_optimizer.suggest_optimizations(query_analysis)
            )
        
        if cache_stats:
            summary['optimization_suggestions'].extend(
                cache_optimizer.suggest_cache_optimizations(cache_stats)
            )
        
        return summary
    except Exception as e:
        logger.error(f"Error getting performance summary: {e}")
        return None 