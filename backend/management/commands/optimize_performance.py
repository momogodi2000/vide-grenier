# backend/management/commands/optimize_performance.py
"""
Django management command to optimize database performance and cache
"""

from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.db import connection
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Optimize database performance and cache'

    def add_arguments(self, parser):
        parser.add_argument(
            '--analyze',
            action='store_true',
            help='Analyze database performance',
        )
        parser.add_argument(
            '--optimize',
            action='store_true',
            help='Run database optimizations',
        )
        parser.add_argument(
            '--cache',
            action='store_true',
            help='Optimize cache',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Run all optimizations',
        )

    def handle(self, *args, **options):
        if options['all'] or options['analyze']:
            self.analyze_performance()
        
        if options['all'] or options['optimize']:
            self.optimize_database()
        
        if options['all'] or options['cache']:
            self.optimize_cache()
        
        self.stdout.write(
            self.style.SUCCESS('Performance optimization completed successfully!')
        )

    def analyze_performance(self):
        """Analyze database performance"""
        self.stdout.write('Analyzing database performance...')
        
        try:
            with connection.cursor() as cursor:
                # Get table sizes
                cursor.execute("""
                    SELECT 
                        tablename,
                        pg_size_pretty(pg_total_relation_size(tablename::text)) as size
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY pg_total_relation_size(tablename::text) DESC;
                """)
                table_sizes = cursor.fetchall()
                
                self.stdout.write('\nTable Sizes:')
                for table, size in table_sizes:
                    self.stdout.write(f'  {table}: {size}')
                
                # Get index usage
                cursor.execute("""
                    SELECT 
                        tablename,
                        indexname,
                        idx_scan,
                        idx_tup_read
                    FROM pg_stat_user_indexes 
                    ORDER BY idx_scan DESC
                    LIMIT 10;
                """)
                index_usage = cursor.fetchall()
                
                self.stdout.write('\nIndex Usage:')
                for table, index, scans, reads in index_usage:
                    self.stdout.write(f'  {table}.{index}: {scans} scans, {reads} reads')
                
                # Get slow queries (if pg_stat_statements is available)
                try:
                    cursor.execute("""
                        SELECT 
                            query,
                            calls,
                            mean_time
                        FROM pg_stat_statements 
                        ORDER BY mean_time DESC 
                        LIMIT 5;
                    """)
                    slow_queries = cursor.fetchall()
                    
                    if slow_queries:
                        self.stdout.write('\nSlow Queries:')
                        for query, calls, mean_time in slow_queries:
                            self.stdout.write(f'  {calls} calls, {mean_time:.2f}ms avg: {query[:100]}...')
                except Exception:
                    self.stdout.write('\npg_stat_statements not available for slow query analysis')
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error analyzing performance: {e}')
            )

    def optimize_database(self):
        """Run database optimizations"""
        self.stdout.write('Running database optimizations...')
        
        try:
            with connection.cursor() as cursor:
                # Update table statistics
                cursor.execute('ANALYZE;')
                self.stdout.write('  ✓ Updated table statistics')
                
                # Vacuum tables
                cursor.execute('VACUUM ANALYZE;')
                self.stdout.write('  ✓ Vacuumed and analyzed tables')
                
                # Reindex if needed
                cursor.execute("""
                    SELECT schemaname, tablename, indexname
                    FROM pg_stat_user_indexes 
                    WHERE idx_scan = 0 AND idx_tup_read = 0;
                """)
                unused_indexes = cursor.fetchall()
                
                if unused_indexes:
                    self.stdout.write(f'  Found {len(unused_indexes)} unused indexes')
                    for schema, table, index in unused_indexes:
                        self.stdout.write(f'    {schema}.{table}.{index}')
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error optimizing database: {e}')
            )

    def optimize_cache(self):
        """Optimize cache"""
        self.stdout.write('Optimizing cache...')
        
        try:
            # Clear expired cache entries
            cache.clear()
            self.stdout.write('  ✓ Cleared cache')
            
            # Pre-warm common cache entries
            self.prewarm_cache()
            self.stdout.write('  ✓ Pre-warmed cache')
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error optimizing cache: {e}')
            )

    def prewarm_cache(self):
        """Pre-warm commonly accessed cache entries"""
        try:
            from backend.models import Category, Product, User
            
            # Cache active categories
            categories = Category.objects.filter(is_active=True).prefetch_related('children')
            cache.set('categories_active', list(categories), 3600)
            
            # Cache popular products
            popular_products = Product.objects.filter(
                status='ACTIVE'
            ).order_by('-views_count')[:20].select_related('category', 'seller')
            cache.set('popular_products', list(popular_products), 1800)
            
            # Cache user counts
            user_count = User.objects.filter(is_active=True).count()
            cache.set('active_users_count', user_count, 3600)
            
            # Cache product counts
            product_count = Product.objects.filter(status='ACTIVE').count()
            cache.set('active_products_count', product_count, 1800)
        
        except Exception as e:
            logger.error(f'Error pre-warming cache: {e}') 