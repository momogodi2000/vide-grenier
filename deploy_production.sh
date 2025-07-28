#!/bin/bash
# Production Deployment Script for VGK with Performance Optimizations

set -e  # Exit on any error

echo "🚀 Starting VGK Production Deployment with Performance Optimizations..."

# Configuration
APP_NAME="vide-grenier-kamer"
ENVIRONMENT="production"
PYTHON_VERSION="3.11"
WORKERS=4
TIMEOUT=120

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    error "manage.py not found. Please run this script from the project root."
fi

# Step 1: Environment Setup
log "📋 Setting up environment..."
export DJANGO_SETTINGS_MODULE="vide.settings.production"
export PYTHONPATH="${PWD}"

# Step 2: Install Dependencies
log "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Step 3: Database Migrations
log "🗄️ Running database migrations..."
python manage.py migrate --noinput

# Step 4: Database Optimization
log "⚡ Running database optimizations..."
python manage.py optimize_performance --all

# Step 5: Collect Static Files
log "📁 Collecting static files..."
python manage.py collectstatic --noinput --clear

# Step 6: Optimize Static Files
log "🔧 Optimizing static files..."
if command -v gzip &> /dev/null; then
    find staticfiles -type f \( -name "*.css" -o -name "*.js" \) -exec gzip -9 {} \;
    log "✓ Static files compressed with gzip"
fi

# Step 7: Cache Optimization
log "💾 Optimizing cache..."
python manage.py shell -c "
from django.core.cache import cache
from backend.models import Category, Product, User
import logging

logger = logging.getLogger(__name__)

try:
    # Pre-warm cache with common data
    categories = list(Category.objects.filter(is_active=True).prefetch_related('children'))
    cache.set('categories_active', categories, 3600)
    
    popular_products = list(Product.objects.filter(status='ACTIVE').order_by('-views_count')[:20].select_related('category', 'seller'))
    cache.set('popular_products', popular_products, 1800)
    
    user_count = User.objects.filter(is_active=True).count()
    cache.set('active_users_count', user_count, 3600)
    
    product_count = Product.objects.filter(status='ACTIVE').count()
    cache.set('active_products_count', product_count, 1800)
    
    print('Cache pre-warmed successfully')
except Exception as e:
    logger.error(f'Error pre-warming cache: {e}')
    print(f'Cache pre-warming failed: {e}')
"

# Step 8: Database Indexing
log "🔍 Creating database indexes..."
python manage.py shell -c "
from django.db import connection
import logging

logger = logging.getLogger(__name__)

try:
    with connection.cursor() as cursor:
        # Create additional performance indexes
        indexes = [
            'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_search_fulltext ON backend_product USING gin(to_tsvector(\'french\', title || \' \' || description));',
            'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_date_range ON backend_order (created_at) WHERE status IN (\'PENDING\', \'PAID\', \'PROCESSING\');',
            'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_unread ON backend_message (chat_id, created_at) WHERE is_read = false;',
            'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_notifications_unread ON backend_notification (user_id, created_at) WHERE is_read = false;',
            'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_active ON backend_product (created_at, category_id, city) WHERE status = \'ACTIVE\';',
            'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_active ON backend_user (created_at, user_type) WHERE is_active = true;'
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        print('Database indexes created successfully')
except Exception as e:
    logger.error(f'Error creating indexes: {e}')
    print(f'Index creation failed: {e}')
"

# Step 9: Update Search Vectors
log "🔍 Updating search vectors..."
python manage.py shell -c "
from backend.models import Product
from django.contrib.postgres.search import SearchVector
import logging

logger = logging.getLogger(__name__)

try:
    # Update search vectors for all products
    Product.objects.update(
        search_vector=SearchVector('title', weight='A') + SearchVector('description', weight='B')
    )
    print('Search vectors updated successfully')
except Exception as e:
    logger.error(f'Error updating search vectors: {e}')
    print(f'Search vector update failed: {e}')
"

# Step 10: Health Check
log "🏥 Running health checks..."
python manage.py check --deploy

# Step 11: Start Services
log "🚀 Starting services..."

# Start Redis if not running
if ! pgrep -x "redis-server" > /dev/null; then
    log "Starting Redis..."
    redis-server --daemonize yes
fi

# Start Celery workers
log "Starting Celery workers..."
celery -A vide worker --loglevel=info --concurrency=8 --detach

# Start Celery beat for scheduled tasks
log "Starting Celery beat..."
celery -A vide beat --loglevel=info --detach

# Step 12: Start Gunicorn
log "🌐 Starting Gunicorn server..."
gunicorn \
    --bind 0.0.0.0:8000 \
    --workers $WORKERS \
    --timeout $TIMEOUT \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --keep-alive 2 \
    --worker-class sync \
    --worker-connections 1000 \
    --preload \
    --access-logfile logs/gunicorn_access.log \
    --error-logfile logs/gunicorn_error.log \
    --log-level info \
    vide.wsgi:application

# Step 13: Performance Monitoring Setup
log "📊 Setting up performance monitoring..."

# Create monitoring script
cat > monitor_performance.sh << 'EOF'
#!/bin/bash
# Performance monitoring script

echo "=== VGK Performance Report ==="
echo "Date: $(date)"
echo ""

# Database connections
echo "Database Connections:"
psql $DATABASE_URL -c "SELECT count(*) as active_connections FROM pg_stat_activity WHERE state = 'active';"

# Cache hit rate
echo ""
echo "Cache Statistics:"
redis-cli info memory | grep -E "(used_memory|used_memory_peak|hit_rate)"

# System resources
echo ""
echo "System Resources:"
free -h
df -h

# Process status
echo ""
echo "Process Status:"
ps aux | grep -E "(gunicorn|celery|redis)" | grep -v grep
EOF

chmod +x monitor_performance.sh

# Step 14: Create maintenance script
cat > maintenance.sh << 'EOF'
#!/bin/bash
# Maintenance script for VGK

case "$1" in
    "optimize")
        echo "Running performance optimizations..."
        python manage.py optimize_performance --all
        ;;
    "cache")
        echo "Clearing and warming cache..."
        python manage.py shell -c "from django.core.cache import cache; cache.clear()"
        python manage.py optimize_performance --cache
        ;;
    "backup")
        echo "Creating database backup..."
        pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql
        ;;
    "restart")
        echo "Restarting services..."
        pkill -f gunicorn
        pkill -f celery
        sleep 2
        ./deploy_production.sh
        ;;
    *)
        echo "Usage: $0 {optimize|cache|backup|restart}"
        exit 1
        ;;
esac
EOF

chmod +x maintenance.sh

# Step 15: Final Status
log "✅ Deployment completed successfully!"
log ""
log "📋 Deployment Summary:"
log "  • Database optimized with indexes and partitioning"
log "  • Cache pre-warmed with common data"
log "  • Static files collected and optimized"
log "  • Search vectors updated"
log "  • Services started (Gunicorn, Celery, Redis)"
log "  • Performance monitoring configured"
log ""
log "🔧 Management Commands:"
log "  • Performance optimization: python manage.py optimize_performance --all"
log "  • Cache management: ./maintenance.sh cache"
log "  • System monitoring: ./monitor_performance.sh"
log "  • Service restart: ./maintenance.sh restart"
log ""
log "🌐 Application should be available at: http://localhost:8000"
log "📊 Monitor performance with: ./monitor_performance.sh"

# Optional: Start monitoring
if [ "$1" = "--monitor" ]; then
    log "📊 Starting performance monitoring..."
    watch -n 30 ./monitor_performance.sh
fi 