# Vidé-Grenier Kamer - Enhanced Marketplace Platform

A comprehensive marketplace platform for Cameroon with advanced features including AI-powered recommendations, real-time messaging, mobile app support, and more.

## 🚀 New Features Implemented

### 🤖 AI & Machine Learning Integration

#### Google Gemini AI Integration
- **Replaced OpenAI** with Google Gemini for cost-effective AI features
- **Product Description Enhancement**: Automatically improves product descriptions
- **Sentiment Analysis**: Analyzes user reviews and feedback
- **Content Moderation**: AI-powered content filtering
- **Personalized Recommendations**: Smart product suggestions with explanations

#### TensorFlow Serving Support
- **Custom ML Models**: Support for TensorFlow Serving models
- **Recommendation Engine**: Advanced product recommendation algorithms
- **User Behavior Prediction**: Predicts user actions and preferences
- **Scalable ML Infrastructure**: Ready for production ML workloads

### 📱 Enhanced Mobile App

#### Kivy Mobile Application
- **Offline Mode**: Works without internet connection
- **Splash Screen**: Professional app loading experience
- **Connection Management**: Smart connection detection and fallback
- **Progressive Web App**: PWA features for web-to-mobile conversion

#### APK Generation System
- **Automated Build Process**: Complete APK/AAB generation pipeline
- **Multi-Platform Support**: Android APK, AAB, and iOS builds
- **Build Reports**: Detailed build status and logs
- **Asset Management**: Automatic icon and splash screen generation

### 🔔 Smart Notification System

#### Multi-Channel Notifications
- **SMS Integration**: Twilio, Infobip, and Africa's Talking support
- **Email Notifications**: Enhanced email delivery system
- **WhatsApp Integration**: WhatsApp Business API support
- **In-App Notifications**: Real-time in-app messaging

#### Intelligent Notification Engine
- **Behavior-Based Timing**: Optimal notification delivery times
- **Personalization**: User preference-based notifications
- **A/B Testing**: Notification optimization
- **Rate Limiting**: Prevents notification spam

### 🔐 Two-Factor Authentication (2FA)

#### Secure Authentication
- **Multiple Methods**: Email and SMS verification
- **User Type Support**: Different 2FA requirements for different user types
- **Fallback Mechanisms**: Multiple verification options
- **Security Features**: Lockout protection and attempt limiting

### 💬 Real-Time Chat System

#### WebSocket Chat Implementation
- **Private Messaging**: Direct user-to-user communication
- **Group Chats**: Multi-user conversations
- **Real-Time Features**: Typing indicators, read receipts
- **Message History**: Persistent chat history
- **User Types**: Different chat interfaces for clients, admin, and staff

### ☁️ Advanced File Storage

#### Dropbox Integration
- **Heavy File Storage**: Automatic migration to Dropbox for large files
- **Database Size Monitoring**: Automatic threshold-based switching
- **Shared Links**: Public file sharing capabilities
- **Storage Analytics**: Usage monitoring and reporting

### 📊 Performance Optimizations

#### Database & Caching
- **Redis Integration**: Advanced caching system
- **Database Indexing**: Optimized query performance
- **Connection Pooling**: Efficient database connections
- **Query Optimization**: Reduced database load

#### Image & File Optimization
- **Automatic Compression**: Image optimization
- **Format Conversion**: WebP support for better performance
- **CDN Ready**: Cloud storage integration
- **Lazy Loading**: Optimized content delivery

## 🛠 Installation & Setup

### Prerequisites

```bash
# Python 3.8+
python --version

# Node.js (for frontend assets)
node --version

# Redis (for caching and sessions)
redis-server --version

# PostgreSQL (recommended for production)
psql --version

# Java (for Android builds)
java --version
```

### Environment Configuration

1. **Copy environment template**:
```bash
cp env_config.example .env
```

2. **Configure essential services**:
```bash
# AI Services
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-1.5-flash

# SMS Services
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
INFOBIP_API_KEY=your-infobip-key

# File Storage
DROPBOX_APP_KEY=your-dropbox-key
DROPBOX_APP_SECRET=your-dropbox-secret
DROPBOX_ACCESS_TOKEN=your-dropbox-token

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/vide_grenier_db

# Redis
REDIS_URL=redis://localhost:6379/0
```

### Installation Steps

1. **Clone and setup**:
```bash
git clone <repository-url>
cd vide-grenier
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Database setup**:
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
```

3. **Start services**:
```bash
# Start Redis
redis-server

# Start Django development server
python manage.py runserver

# Start Celery (for background tasks)
celery -A vide worker -l info

# Start Celery Beat (for scheduled tasks)
celery -A vide beat -l info
```

## 📱 Mobile App Development

### Building the Mobile App

1. **Setup Kivy environment**:
```bash
cd kivy_app
pip install kivy buildozer
```

2. **Generate APK**:
```bash
# Generate debug APK
python generate_apk_enhanced.py --platforms android_apk

# Generate release APK and AAB
python generate_apk_enhanced.py --platforms android_apk android_aab --release

# Clean build and generate
python generate_apk_enhanced.py --platforms android_apk --clean
```

3. **iOS Build** (requires macOS):
```bash
python generate_apk_enhanced.py --platforms ios
```

### Mobile App Features

- **Offline Mode**: Browse products without internet
- **Splash Screen**: Professional app loading
- **Connection Management**: Smart online/offline detection
- **Push Notifications**: Real-time updates
- **Camera Integration**: Product photo capture
- **Location Services**: Local product discovery

## 🤖 AI Features Usage

### Product Recommendations

```python
from backend.ai_engine import get_recommendations_for_user

# Get personalized recommendations
recommendations = get_recommendations_for_user(user_id=123, limit=10)

# Get similar products
from backend.ai_engine import get_similar_products
similar = get_similar_products(product_id=456, limit=6)
```

### Content Generation

```python
from backend.ai_engine import generate_product_description

# Enhance product description
enhanced_desc = generate_product_description({
    'title': 'iPhone 12',
    'description': 'Good condition',
    'price': '250000',
    'condition': 'BON'
})
```

### Sentiment Analysis

```python
from backend.ai_engine import analyze_sentiment

# Analyze review sentiment
sentiment = analyze_sentiment("Great product, fast delivery!")
# Returns: {'sentiment': 'positive', 'score': 0.8, 'confidence': 0.9}
```

## 🔔 Notification System

### Sending Notifications

```python
from backend.smart_notifications import smart_notifications

# Send price drop alert
smart_notifications.trigger_notification(
    template_name='price_drop_alert',
    user=user,
    context={
        'product_name': 'iPhone 12',
        'old_price': '300000',
        'new_price': '250000',
        'savings': '50000'
    },
    preferred_channels=['SMS', 'EMAIL']
)
```

### SMS Notifications

```python
from backend.smart_notifications import send_sms_notification

# Send SMS
result = send_sms_notification(
    phone_number='+237694638412',
    message='Your order has been confirmed!'
)
```

## 🔐 2FA Implementation

### Enabling 2FA

```python
from backend.two_factor_auth import enable_2fa_for_user

# Enable 2FA for user
result = enable_2fa_for_user(user, method='email')
if result['success']:
    print("2FA enabled successfully")
```

### Verifying 2FA

```python
from backend.two_factor_auth import verify_2fa_code

# Verify 2FA code
result = verify_2fa_code(user, code='123456', method='email')
if result['success']:
    print("2FA verification successful")
```

## 💬 Chat System

### Creating Chats

```python
from backend.chat_websocket import create_chat_between_users

# Create private chat
chat = create_chat_between_users(user1, user2, product=product)

# Create group chat (admin only)
from backend.chat_websocket import create_group_chat
group_chat = create_group_chat(
    name='Support Group',
    chat_type='ADMIN_CLIENT',
    participants=[user1, user2, admin],
    created_by=admin
)
```

### WebSocket Connection

```javascript
// Connect to private chat
const chatSocket = new WebSocket(
    `ws://localhost:8000/ws/chat/${chatId}/`
);

// Connect to group chat
const groupSocket = new WebSocket(
    `ws://localhost:8000/ws/group_chat/${groupId}/`
);

// Send message
chatSocket.send(JSON.stringify({
    'type': 'message',
    'content': 'Hello!',
    'message_type': 'TEXT'
}));
```

## ☁️ File Storage

### Dropbox Integration

```python
from backend.dropbox_storage import upload_to_dropbox

# Upload file to Dropbox
result = upload_to_dropbox(
    file_path='/path/to/file.jpg',
    dropbox_path='/vgk_files/products/file.jpg'
)

# Create shared link
from backend.dropbox_storage import create_dropbox_shared_link
link = create_dropbox_shared_link('/vgk_files/products/file.jpg')
```

## 📊 Performance Monitoring

### Database Optimization

```python
# Add database indexes
python manage.py makemigrations
python manage.py migrate

# Monitor database size
from backend.dropbox_storage import get_database_size_gb
size_gb = get_database_size_gb()
print(f"Database size: {size_gb} GB")
```

### Cache Management

```python
from django.core.cache import cache

# Cache product recommendations
cache.set('recommendations_user_123', recommendations, 3600)

# Get cached data
cached_data = cache.get('recommendations_user_123')
```

## 🚀 Deployment

### Production Setup

1. **Environment Variables**:
```bash
DEBUG=False
SECRET_KEY=your-production-secret-key
DATABASE_URL=postgresql://user:password@host:5432/db
REDIS_URL=redis://host:6379/0
```

2. **Static Files**:
```bash
python manage.py collectstatic --noinput
```

3. **Database**:
```bash
python manage.py migrate
python manage.py createsuperuser
```

4. **Services**:
```bash
# Start Gunicorn
gunicorn vide.wsgi:application --bind 0.0.0.0:8000

# Start Celery
celery -A vide worker -l info

# Start Redis
redis-server
```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build individual services
docker build -t vide-grenier .
docker run -p 8000:8000 vide-grenier
```

## 🔧 Troubleshooting

### APK Generation Issues

#### Common Problems and Solutions

1. **"Unknown command/target android" Error (Windows)**:
   ```bash
   # This is a known Windows issue with buildozer
   # Try the Windows-specific installation
   python install_buildozer_windows.py
   
   # If that doesn't work, use Docker (recommended for Windows)
   python docker_buildozer.py
   
   # Or use WSL (Windows Subsystem for Linux)
   wsl --install
   # Then in WSL:
   sudo apt update && sudo apt install python3-pip
   pip3 install buildozer
   ```

2. **Buildozer not working on Windows**:
   ```bash
   # Use Docker-based solution (recommended)
   python docker_buildozer.py
   
   # Or install Docker Desktop and run:
   docker pull kivy/buildozer
   docker run --volume "$PWD":/home/user/hostcwd kivy/buildozer --workdir /home/user/hostcwd android debug
   ```

2. **Unicode Encoding Errors (Windows)**:
   ```bash
   # The script now handles this automatically
   # If you still see issues, run:
   chcp 65001
   python generate_apk_enhanced.py
   ```

3. **Java Not Found**:
   ```bash
   # Install OpenJDK
   # Windows: Download from https://adoptium.net/
   # Linux: sudo apt install openjdk-11-jdk
   # macOS: brew install openjdk@11
   ```

4. **Android SDK Issues**:
   ```bash
   # Buildozer will download automatically
   # Or set ANDROID_HOME environment variable
   export ANDROID_HOME=/path/to/android/sdk
   ```

#### Manual Buildozer Commands

If the automated script fails, try manual commands:

```bash
# Initialize buildozer (if not done)
buildozer init

# Build debug APK
buildozer android debug

# Build release APK
buildozer android release

# Clean build
buildozer android clean
```

### Database Issues

1. **Migration Errors**:
   ```bash
   # Reset migrations
   python manage.py migrate --fake-initial
   
   # Or create fresh database
   python manage.py flush
   python manage.py migrate
   ```

2. **Redis Connection Issues**:
   ```bash
   # Check Redis status
   redis-cli ping
   
   # Start Redis if not running
   redis-server
   ```

### AI Service Issues

1. **Gemini API Errors**:
   ```bash
   # Check API key
   echo $GEMINI_API_KEY
   
   # Test API connection
   python -c "import google.generativeai as genai; genai.configure(api_key='your-key')"
   ```

2. **TensorFlow Serving Issues**:
   ```bash
   # Check if TF Serving is running
   curl http://localhost:8501/v1/models
   
   # Start TF Serving
   tensorflow_model_server --port=8501 --rest_api_port=8501 --model_name=recommendation_model --model_base_path=/path/to/model
   ```

### Notification Issues

1. **SMS Not Sending**:
   ```bash
   # Check Twilio credentials
   echo $TWILIO_ACCOUNT_SID
   echo $TWILIO_AUTH_TOKEN
   
   # Test SMS service
   python -c "from backend.smart_notifications import sms_service; print(sms_service.send_sms('+1234567890', 'Test'))"
   ```

2. **Email Not Sending**:
   ```bash
   # Check email settings
   python manage.py shell -c "from django.core.mail import send_mail; send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])"
   ```

## 📈 Analytics & Monitoring

### Performance Metrics

- **Database Query Performance**: Monitor slow queries
- **Cache Hit Rates**: Track Redis performance
- **API Response Times**: Monitor endpoint performance
- **User Engagement**: Track user behavior patterns

### Error Monitoring

- **Sentry Integration**: Error tracking and alerting
- **Log Aggregation**: Centralized logging
- **Performance Alerts**: Automated performance monitoring

## 🔧 Configuration Options

### AI Configuration

```python
# AI settings in settings.py
AI_RECOMMENDATIONS = {
    'ENABLED': True,
    'MIN_INTERACTIONS': 5,
    'SIMILARITY_THRESHOLD': 0.1,
    'CACHE_HOURS': 6
}
```

### Notification Configuration

```python
# Notification settings
SMART_NOTIFICATIONS = {
    'ENABLED': True,
    'CHANNELS': {
        'IN_APP': True,
        'EMAIL': True,
        'SMS': True,
        'WHATSAPP': True
    }
}
```

### Mobile App Configuration

```python
# Mobile app settings
MOBILE_APP = {
    'OFFLINE_MODE': True,
    'SPLASH_SCREEN': True,
    'OFFLINE_PAGES': ['visitor_home', 'visitor_products'],
    'REQUIRE_CONNECTION_FOR': ['chat', 'orders', 'payments']
}
```

## 📋 Development Workflow

### Code Organization

```
vide/
├── backend/                 # Django backend
│   ├── ai_engine.py        # AI integration
│   ├── smart_notifications.py  # Notification system
│   ├── two_factor_auth.py  # 2FA implementation
│   ├── chat_websocket.py   # Real-time chat
│   ├── dropbox_storage.py  # File storage
│   └── models.py           # Database models
├── kivy_app/               # Mobile app
│   ├── main_enhanced.py    # Enhanced mobile app
│   └── main.py             # Basic mobile app
├── templates/              # HTML templates
├── static/                 # Static files
├── requirements.txt        # Python dependencies
├── buildozer.spec          # Mobile build configuration
├── generate_apk_enhanced.py # APK generation script
└── env_config.example      # Environment configuration
```

### Testing

```bash
# Run tests
python manage.py test

# Run specific tests
python manage.py test backend.tests.AITestCase
python manage.py test backend.tests.NotificationTestCase
```

### Code Quality

```bash
# Install development dependencies
pip install flake8 black isort

# Format code
black .
isort .

# Check code quality
flake8 .
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Email: support@videgrenierkamer.com
- Phone: +237 694 63 84 12
- WhatsApp: +237 694 63 84 12

## 🔄 Changelog

### Version 1.0.0 (Latest)
- ✅ AI integration with Google Gemini
- ✅ TensorFlow Serving support
- ✅ Enhanced mobile app with offline mode
- ✅ Smart notification system
- ✅ Two-factor authentication
- ✅ Real-time chat system
- ✅ Dropbox file storage
- ✅ Performance optimizations
- ✅ APK generation system
- ✅ Comprehensive documentation
- ✅ Windows compatibility fixes
- ✅ Troubleshooting guide

### Version 0.9.0
- ✅ Basic marketplace functionality
- ✅ User authentication
- ✅ Product management
- ✅ Order processing
- ✅ Payment integration

---

**Vidé-Grenier Kamer** - The ultimate marketplace platform for Cameroon 🇨🇲 