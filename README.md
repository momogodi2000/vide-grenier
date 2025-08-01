# Vidé-Grenier Kamer - Complete Marketplace Platform Documentation

## 🏗️ **COMPLETE APPLICATION ARCHITECTURE & TECHNICAL OVERVIEW**

**Vidé-Grenier Kamer** is a comprehensive, production-ready marketplace platform specifically designed for Cameroon, featuring both web and mobile applications with advanced AI integration, real-time communication, and complete e-commerce functionality.

### **🎯 Project Justification & Business Context**

**Market Need**: Cameroon's growing digital economy requires a localized marketplace platform that understands local payment methods (Mobile Money), cultural preferences, and business practices. Traditional e-commerce platforms don't address the specific needs of Cameroonian users.

**Solution**: A complete marketplace ecosystem that combines:
- **Web Platform**: Full-featured Django web application
- **Mobile API**: Complete RESTful API for mobile applications
- **AI Integration**: Smart recommendations and content enhancement
- **Local Payment Integration**: Mobile Money (Orange Money, MTN Money), Campay
- **Real-time Communication**: Chat system for buyers and sellers
- **Visitor Shopping**: Anonymous shopping without registration

### **🏛️ Application Architecture Overview**

```
Vidé-Grenier Kamer Platform
├── 🌐 Web Application (Django)
│   ├── Admin Dashboard (Complete management system)
│   ├── Client Portal (User marketplace interface)
│   ├── Staff Portal (Pickup point management)
│   └── Visitor Interface (Anonymous shopping)
├── 📱 Mobile API Backend (RESTful)
│   ├── Authentication & 2FA
│   ├── Product Management
│   ├── Order Processing
│   └── Admin Functions
├── 🤖 AI Engine (Google Gemini + TensorFlow)
├── 💬 Real-time Chat System (WebSocket)
├── 🔔 Smart Notification System
└── ☁️ Cloud Storage (Dropbox Integration)
```

### **📊 Technical Stack & Technologies**

#### **Backend Framework**
- **Django 4.2.7**: Main web framework with advanced features
- **Django REST Framework**: API development for mobile
- **Django Channels**: WebSocket support for real-time features
- **Celery**: Background task processing
- **Redis**: Caching and session management

#### **Database & Storage**
- **PostgreSQL**: Primary database (production)
- **SQLite**: Development database
- **Redis**: Caching, sessions, and message broker
- **Dropbox**: Cloud file storage for large files

#### **AI & Machine Learning**
- **Google Gemini AI**: Content generation and analysis
- **TensorFlow**: Custom ML models for recommendations
- **scikit-learn**: Data analysis and predictions

#### **Frontend & UI**
- **Tailwind CSS**: Modern, responsive design
- **Progressive Web App (PWA)**: Mobile-like web experience
- **WebSocket**: Real-time chat and notifications
- **African Theme**: Culturally appropriate design

#### **Payment & Communication**
- **Mobile Money**: Orange Money, MTN Money integration
- **Campay**: Payment gateway
- **Twilio/Infobip**: SMS notifications
- **WhatsApp Business API**: Messaging integration

#### **Security & Authentication**
- **JWT Authentication**: Token-based security
- **Two-Factor Authentication (2FA)**: Enhanced security
- **Google OAuth**: Social login integration
- **Django Allauth**: Authentication framework

### **🗂️ Complete Project Structure**

```
vide-grenier/
├── 📁 backend/                          # Django Backend Application
│   ├── 📁 mobile/                       # 🆕 Complete Mobile API
│   │   ├── serializers.py              # 25 API serializers
│   │   ├── views.py                    # 10 view classes
│   │   ├── urls.py                     # URL routing
│   │   ├── jwt_utils.py                # JWT authentication
│   │   ├── authentication.py           # Custom auth classes
│   │   ├── permissions.py              # Permission classes
│   │   ├── tests.py                    # 15 test cases
│   │   └── README.md                   # Mobile API documentation
│   ├── models.py                       # 15+ database models
│   ├── views.py                        # Main web views (5855 lines)
│   ├── views_admin.py                  # Admin views (5432 lines)
│   ├── views_client.py                 # Client views (804 lines)
│   ├── views_visitor.py                # Visitor views (1368 lines)
│   ├── views_staff.py                  # Staff views (620 lines)
│   ├── ai_engine.py                    # AI integration (834 lines)
│   ├── smart_notifications.py          # Notification system (946 lines)
│   ├── chat_websocket.py               # Real-time chat (673 lines)
│   ├── two_factor_auth.py              # 2FA implementation (318 lines)
│   ├── dropbox_storage.py              # Cloud storage (472 lines)
│   ├── forms.py                        # Form definitions (1134 lines)
│   ├── urls.py                         # Main URL routing (351 lines)
│   ├── urls_admin.py                   # Admin URLs (244 lines)
│   ├── urls_mobile.py                  # Mobile API URLs (31 lines)
│   └── 📁 migrations/                  # Database migrations
├── 📁 templates/                       # HTML Templates
│   ├── 📁 backend/
│   │   ├── 📁 admin/                   # Admin interface templates
│   │   ├── 📁 client/                  # Client portal templates
│   │   ├── 📁 staff/                   # Staff portal templates
│   │   ├── 📁 visitor/                 # Visitor interface templates
│   │   └── 📁 admin_chat/              # Chat interface templates
│   ├── 📁 components/                  # Reusable UI components
│   ├── base.html                       # Base template (666 lines)
│   ├── manifest.json                   # PWA manifest
│   └── sw.js                          # Service worker
├── 📁 vide/                           # Django Project Settings
│   ├── 📁 settings/
│   │   ├── base.py                    # Base settings (533 lines)
│   │   ├── development.py             # Development settings
│   │   ├── production.py              # Production settings
│   │   └── social_providers.py        # OAuth configuration
│   ├── urls.py                        # Project URLs
│   ├── asgi.py                        # ASGI configuration
│   └── wsgi.py                        # WSGI configuration
├── 📁 static/                         # Static files (CSS, JS, Images)
├── 📁 media/                          # User-uploaded files
├── 📁 doc/                            # Documentation
├── requirements.txt                   # Python dependencies (164 packages)
├── package.json                       # Node.js dependencies
├── tailwind.config.js                # Tailwind CSS configuration
├── docker-compose.yml                # Docker configuration
├── Dockerfile                        # Docker image definition
├── env_config.example                # Environment variables template
└── manage.py                         # Django management script
```

### **🎭 User Types & Access Levels**

#### **1. ADMIN Users** (Full System Access)
- **Dashboard**: Complete analytics and system overview
- **User Management**: Create, edit, delete all user accounts
- **Product Moderation**: Approve/reject product listings
- **Order Management**: Process and track all orders
- **Financial Management**: Commission tracking and payments
- **System Configuration**: Platform settings and maintenance
- **Mobile API Access**: Full admin functionality on mobile

#### **2. CLIENT Users** (Marketplace Participants)
- **Product Management**: Create, edit, delete personal listings
- **Shopping**: Browse, search, filter, and purchase products
- **Order Management**: Track purchases and sales
- **Communication**: Chat with buyers/sellers
- **Wallet**: Manage funds and transactions
- **Profile**: Personal information and preferences
- **Mobile Access**: Full client functionality on mobile

#### **3. STAFF Users** (Pickup Point Operators)
- **Order Processing**: Handle order pickups and deliveries
- **Inventory Management**: Track stock and movements
- **Customer Service**: Assist customers at pickup points
- **Reporting**: Generate pickup point reports
- **Mobile Access**: Staff-specific mobile functions

#### **4. VISITOR Users** (Anonymous Shopping)
- **Product Browsing**: View all active products
- **Search & Filter**: Advanced search functionality
- **Shopping Cart**: Session-based cart management
- **Guest Checkout**: Purchase without registration
- **Payment Options**: All payment methods available
- **Mobile Access**: Visitor shopping on mobile

### **🔧 Core Functionality Modules**

#### **1. Product Management System**
- **Product Creation**: Multi-image upload, detailed descriptions
- **Category Management**: Hierarchical category system
- **Status Management**: Draft, Pending, Active, Sold, etc.
- **Pricing**: Negotiable prices, commission calculation
- **Condition Tracking**: Product condition assessment
- **Location-based**: City-specific product listings

#### **2. Order & Payment System**
- **Order Processing**: Complete order lifecycle management
- **Payment Integration**: Mobile Money, Card, Cash payments
- **Commission System**: Automatic commission calculation
- **Delivery Options**: Pickup points and home delivery
- **Order Tracking**: Real-time order status updates
- **Visitor Orders**: Anonymous order processing

#### **3. Communication System**
- **Private Chat**: Buyer-seller direct messaging
- **Group Chats**: Multi-user conversations
- **Real-time Messaging**: WebSocket-based communication
- **Message Types**: Text, images, offers, system messages
- **Read Receipts**: Message delivery confirmation
- **Mobile Chat**: Full chat functionality on mobile

#### **4. AI & Recommendation Engine**
- **Product Recommendations**: Personalized suggestions
- **Content Enhancement**: AI-powered product descriptions
- **Sentiment Analysis**: Review and feedback analysis
- **Search Optimization**: Smart search algorithms
- **Behavior Prediction**: User action prediction
- **Content Moderation**: AI-powered content filtering

#### **5. Notification System**
- **Multi-channel**: Email, SMS, WhatsApp, In-app
- **Smart Timing**: Optimal notification delivery
- **Personalization**: User preference-based notifications
- **A/B Testing**: Notification optimization
- **Rate Limiting**: Prevent notification spam
- **Mobile Push**: Real-time mobile notifications

#### **6. Security & Authentication**
- **Two-Factor Authentication**: Email and SMS verification
- **JWT Tokens**: Secure API authentication
- **Google OAuth**: Social login integration
- **Session Management**: Secure session handling
- **Permission System**: Role-based access control
- **Mobile Security**: Secure mobile API access

### **📱 Mobile API Implementation**

#### **Complete Mobile Backend** 🆕
The mobile API provides **32 endpoints** covering all platform functionality:

**Authentication Endpoints (6)**
- Login with 2FA support
- Google OAuth integration
- Registration with phone verification
- Token refresh and management

**Product Endpoints (6)**
- Product listing with advanced filters
- Product details and images
- Favorites and wishlist management
- Trending and recommended products

**Visitor Endpoints (3)**
- Anonymous shopping cart
- Guest checkout process
- Visitor order creation

**Admin Endpoints (5)**
- Dashboard statistics
- User management
- Product moderation
- System analytics

**Payment Endpoints (2)**
- Payment processing
- Payment verification

#### **Mobile API Features**
- **JWT Authentication**: Secure token-based access
- **2FA Support**: Enhanced security for mobile users
- **Visitor Shopping**: Anonymous shopping experience
- **Real-time Updates**: Live data synchronization
- **Offline Support**: Cached data for offline use
- **Performance Optimized**: Efficient API responses

### **🤖 AI Integration & Machine Learning**

#### **Google Gemini AI Integration**
- **Content Generation**: Enhanced product descriptions
- **Sentiment Analysis**: Review and feedback analysis
- **Content Moderation**: AI-powered content filtering
- **Personalized Recommendations**: Smart product suggestions
- **Language Support**: French and English content processing

#### **TensorFlow Serving Support**
- **Custom ML Models**: Recommendation algorithms
- **User Behavior Prediction**: Action and preference prediction
- **Scalable ML Infrastructure**: Production-ready ML deployment
- **Model Versioning**: ML model management and updates

### **💬 Real-time Communication System**

#### **WebSocket Chat Implementation**
- **Private Messaging**: Direct user-to-user communication
- **Group Chats**: Multi-user conversations
- **Real-time Features**: Typing indicators, read receipts
- **Message History**: Persistent chat storage
- **File Sharing**: Image and file uploads
- **Mobile Chat**: Full chat functionality on mobile

### **🔔 Smart Notification System**

#### **Multi-channel Notifications**
- **SMS Integration**: Twilio, Infobip, Africa's Talking
- **Email Notifications**: Enhanced email delivery
- **WhatsApp Integration**: WhatsApp Business API
- **In-app Notifications**: Real-time in-app messaging
- **Push Notifications**: Mobile push notifications

#### **Intelligent Notification Engine**
- **Behavior-based Timing**: Optimal delivery times
- **Personalization**: User preference-based notifications
- **A/B Testing**: Notification optimization
- **Rate Limiting**: Prevent notification spam

### **☁️ Advanced File Storage**

#### **Dropbox Integration**
- **Heavy File Storage**: Automatic migration for large files
- **Database Size Monitoring**: Threshold-based switching
- **Shared Links**: Public file sharing capabilities
- **Storage Analytics**: Usage monitoring and reporting
- **Backup System**: Automatic file backup

### **📊 Performance & Optimization**

#### **Database Optimization**
- **Indexing**: Optimized database indexes
- **Connection Pooling**: Efficient database connections
- **Query Optimization**: Reduced database load
- **Caching**: Redis-based caching system

#### **Image & File Optimization**
- **Automatic Compression**: Image optimization
- **Format Conversion**: WebP support
- **CDN Ready**: Cloud storage integration
- **Lazy Loading**: Optimized content delivery

### **🔐 Security Implementation**

#### **Authentication & Authorization**
- **JWT Tokens**: Secure API authentication
- **Two-Factor Authentication**: Enhanced security
- **Google OAuth**: Social login integration
- **Session Security**: Secure session management
- **Permission System**: Role-based access control

#### **Data Protection**
- **Encryption**: Data encryption at rest and in transit
- **Input Validation**: Comprehensive input sanitization
- **CSRF Protection**: Cross-site request forgery protection
- **XSS Prevention**: Cross-site scripting protection
- **SQL Injection Prevention**: Parameterized queries

### **🚀 Deployment & Infrastructure**

#### **Production Deployment**
- **Docker Support**: Containerized deployment
- **Cloud Ready**: Render, Heroku, AWS compatible
- **Environment Configuration**: Comprehensive settings management
- **Database Migration**: Automated migration system
- **Static File Serving**: Optimized static file delivery

#### **Monitoring & Maintenance**
- **Error Tracking**: Comprehensive error monitoring
- **Performance Monitoring**: System performance tracking
- **Log Management**: Centralized logging system
- **Backup System**: Automated data backup
- **Health Checks**: System health monitoring

### **📈 Business Intelligence & Analytics**

#### **Dashboard Analytics**
- **Sales Analytics**: Revenue and transaction tracking
- **User Analytics**: User behavior and engagement
- **Product Analytics**: Product performance metrics
- **Geographic Analytics**: Location-based insights
- **Mobile Analytics**: Mobile usage statistics

#### **Reporting System**
- **Financial Reports**: Revenue and commission reports
- **User Reports**: User activity and growth reports
- **Product Reports**: Product performance reports
- **Operational Reports**: System operation reports

### **🎨 User Experience & Design**

#### **Responsive Design**
- **Mobile-First**: Mobile-optimized design
- **Progressive Web App**: App-like web experience
- **African Theme**: Culturally appropriate design
- **Accessibility**: WCAG compliance
- **Performance**: Fast loading and smooth interactions

#### **User Interface**
- **Modern UI**: Clean and intuitive interface
- **Tailwind CSS**: Utility-first CSS framework
- **Component Library**: Reusable UI components
- **Theme System**: Customizable design system
- **Internationalization**: Multi-language support

### **🔧 Development & Testing**

#### **Code Quality**
- **Comprehensive Testing**: Unit and integration tests
- **Code Documentation**: Detailed code documentation
- **API Documentation**: Complete API documentation
- **Mobile API Testing**: Dedicated mobile API tests
- **Performance Testing**: Load and stress testing

#### **Development Workflow**
- **Version Control**: Git-based development
- **Code Review**: Peer review process
- **Continuous Integration**: Automated testing
- **Deployment Pipeline**: Automated deployment
- **Environment Management**: Development, staging, production

### **📋 Installation & Setup**

#### **Prerequisites**
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

#### **Environment Configuration**
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

# JWT Settings (for mobile API)
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_LIFETIME=3600
JWT_REFRESH_TOKEN_LIFETIME=604800
```

#### **Installation Steps**
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

### **📱 Mobile App Development**

#### **React Native Integration** 🆕
The mobile backend is **100% ready** for React Native development:

#### **Complete API Client Setup**
```typescript
// API Client Configuration
const apiClient = new ApiClient({
  baseURL: 'http://localhost:8000/mobile/api/',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  }
});
```

#### **Authentication Flow**
```typescript
// Login with 2FA support
const login = async (email: string, password: string) => {
  const response = await apiClient.post('/auth/login/', {
    email, password
  });
  
  if (response.requires_2fa) {
    // Handle 2FA verification
    return { requires2FA: true, message: response.message };
  }
  
  // Store tokens and user data
  await AsyncStorage.setItem('access_token', response.tokens.access_token);
  return { user: response.user, tokens: response.tokens };
};
```

#### **State Management with Redux**
```typescript
// Redux store configuration
const store = configureStore({
  reducer: {
    auth: authReducer,
    products: productReducer,
    cart: cartReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
    }),
});
```

### **🔧 Mobile API Testing**

#### **Test the Mobile Backend** 🆕
```bash
# Run all mobile API tests
python manage.py test backend.mobile.tests

# Run specific test class
python manage.py test backend.mobile.tests.MobileAPITestCase

# Test authentication endpoints
python manage.py test backend.mobile.tests.MobileAPITestCase.test_login_without_2fa

# Test visitor functionality
python manage.py test backend.mobile.tests.MobileAPITestCase.test_visitor_add_to_cart

# Test admin features
python manage.py test backend.mobile.tests.MobileAPITestCase.test_admin_dashboard_stats
```

#### **API Health Check** 🆕
```bash
# Test mobile API health
curl http://localhost:8000/mobile/api/health/

# Expected response:
{
  "success": true,
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0"
}
```

### **🤖 AI Features Usage**

#### **Product Recommendations**
```python
from backend.ai_engine import get_recommendations_for_user

# Get personalized recommendations
recommendations = get_recommendations_for_user(user_id=123, limit=10)

# Get similar products
from backend.ai_engine import get_similar_products
similar = get_similar_products(product_id=456, limit=6)
```

#### **Content Generation**
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

### **🔔 Notification System**

#### **Sending Notifications**
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

### **💬 Chat System**

#### **Creating Chats**
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

### **🚀 Production Deployment**

#### **Environment Variables**
```bash
DEBUG=False
SECRET_KEY=your-production-secret-key
DATABASE_URL=postgresql://user:password@host:5432/db
REDIS_URL=redis://host:6379/0
JWT_SECRET_KEY=your-jwt-secret-key
```

#### **Docker Deployment**
```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build individual services
docker build -t vide-grenier .
docker run -p 8000:8000 vide-grenier
```

### **🔧 Troubleshooting**

#### **Mobile API Issues** 🆕
1. **Import Errors**:
   ```bash
   # Check if mobile package is properly installed
   python manage.py check
   
   # Verify imports
   python -c "from backend.mobile import views, serializers; print('Mobile API imports successful')"
   ```

2. **Authentication Issues**:
   ```bash
   # Test JWT token generation
   curl -X POST http://localhost:8000/mobile/api/auth/login/ \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"password"}'
   ```

### **📈 Analytics & Monitoring**

#### **Performance Metrics**
- **Database Query Performance**: Monitor slow queries
- **Cache Hit Rates**: Track Redis performance
- **API Response Times**: Monitor endpoint performance
- **User Engagement**: Track user behavior patterns
- **Mobile API Performance**: Monitor mobile endpoint usage

### **🔧 Configuration Options**

#### **Mobile API Configuration** 🆕
```python
# Mobile API settings in settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'backend.mobile.authentication.MobileJWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8081",  # React Native Metro
    "http://localhost:19006", # Expo
]
```

### **📋 Development Workflow**

#### **Code Organization**
```
vide/
├── backend/                 # Django backend
│   ├── ai_engine.py        # AI integration
│   ├── smart_notifications.py  # Notification system
│   ├── two_factor_auth.py  # 2FA implementation
│   ├── chat_websocket.py   # Real-time chat
│   ├── dropbox_storage.py  # File storage
│   ├── models.py           # Database models
│   └── mobile/             # 🆕 Mobile API package
│       ├── __init__.py
│       ├── serializers.py  # 25 API serializers
│       ├── views.py        # 10 view classes
│       ├── urls.py         # URL routing
│       ├── jwt_utils.py    # JWT utilities
│       ├── authentication.py # Custom auth
│       ├── permissions.py  # Custom permissions
│       ├── tests.py        # 15 test cases
│       ├── README.md       # API documentation
│       └── doc/            # Documentation folder
├── templates/              # HTML templates
├── static/                 # Static files
├── requirements.txt        # Python dependencies
└── env_config.example      # Environment configuration
```

### **🤝 Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests (including mobile API tests)
5. Submit a pull request

### **📄 License**

This project is licensed under the MIT License - see the LICENSE file for details.

### **🆘 Support**

For support and questions:
- Email: support@videgrenierkamer.com
- Phone: +237 694 63 84 12
- WhatsApp: +237 694 63 84 12

### **🔄 Changelog**

#### **Version 1.1.0 (Latest)** 🆕
- ✅ **COMPLETE MOBILE BACKEND IMPLEMENTATION**
- ✅ 32 API endpoints for mobile applications
- ✅ JWT authentication with 2FA support
- ✅ Visitor shopping functionality
- ✅ Payment integration (Mobile Money, Card, Cash)
- ✅ Admin management on mobile
- ✅ React Native integration ready
- ✅ Comprehensive mobile API documentation
- ✅ 15 test cases for mobile API
- ✅ Zero impact on web functionality
- ✅ Production-ready mobile backend

#### **Version 1.0.0**
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

#### **Version 0.9.0**
- ✅ Basic marketplace functionality
- ✅ User authentication
- ✅ Product management
- ✅ Order processing
- ✅ Payment integration

---

## **🎯 Summary**

**Vidé-Grenier Kamer** is a **complete, production-ready marketplace platform** that provides:

### **✅ Complete Web Application**
- Full-featured Django web platform
- Admin, Client, Staff, and Visitor interfaces
- Real-time chat and notification systems
- AI-powered recommendations and content enhancement
- Advanced payment integration with local methods

### **✅ Complete Mobile API Backend**
- 32 RESTful API endpoints
- JWT authentication with 2FA support
- Visitor shopping functionality
- Admin management capabilities
- React Native integration ready

### **✅ Advanced Features**
- AI integration with Google Gemini
- TensorFlow Serving support
- Smart notification system
- Real-time WebSocket chat
- Dropbox cloud storage
- Performance optimizations

### **✅ Production Ready**
- Docker deployment support
- Comprehensive testing
- Security implementations
- Performance monitoring
- Scalable architecture

**This is a complete marketplace solution specifically designed for Cameroon, with both web and mobile capabilities, ready for immediate deployment and use.** 🇨🇲

---

**Vidé-Grenier Kamer** - The ultimate marketplace platform for Cameroon 🇨🇲 

**Now with Complete Mobile Backend Support! 📱🚀**

## 🚀 New Features Implemented

### 📱 **COMPLETE MOBILE BACKEND IMPLEMENTATION** 🆕

#### **Production-Ready Mobile API**
- **✅ 32 API Endpoints** - Complete RESTful API for mobile applications
- **✅ JWT Authentication** - Secure token-based authentication with 2FA support
- **✅ 2FA & Google OAuth** - Enhanced security with two-factor authentication
- **✅ Visitor Shopping** - Anonymous shopping experience without registration
- **✅ Payment Integration** - Multiple payment methods (Mobile Money, Card, Cash)
- **✅ Admin Management** - Full admin capabilities on mobile
- **✅ Performance Optimized** - Efficient queries, caching, and pagination

#### **Mobile API Architecture**
```
backend/mobile/
├── __init__.py                 # Package initialization
├── serializers.py             # 25 API serializers for data transformation
├── views.py                   # 10 view classes with business logic
├── urls.py                    # URL routing for all endpoints
├── jwt_utils.py               # JWT authentication utilities
├── authentication.py          # Custom authentication classes
├── permissions.py             # Custom permission classes
├── tests.py                   # 15 comprehensive test cases
├── README.md                  # Complete API documentation
└── doc/                       # Documentation folder
    ├── DATABASE_MODELS.md     # Database model documentation
    ├── API_IMPLEMENTATION_GUIDE.md  # Implementation guide
    ├── REACT_NATIVE_INTEGRATION.md  # React Native integration
    └── IMPLEMENTATION_SUMMARY.md    # Overview and verification
```

#### **Mobile API Endpoints**

**Authentication (6 endpoints)**
- `POST /mobile/api/auth/login/` - Login with 2FA support
- `POST /mobile/api/auth/verify_2fa/` - Verify 2FA code
- `POST /mobile/api/auth/google_oauth/` - Google OAuth login
- `POST /mobile/api/auth/register/` - Registration with phone verification
- `POST /mobile/api/auth/verify_phone/` - Phone verification
- `POST /mobile/api/auth/refresh/` - Token refresh

**Products (6 endpoints)**
- `GET /mobile/api/products/` - List products with filters
- `GET /mobile/api/products/{id}/` - Product details
- `POST /mobile/api/products/{id}/favorite/` - Toggle favorite
- `GET /mobile/api/products/trending/` - Trending products
- `GET /mobile/api/products/recommended/` - Recommended products

**Visitor (3 endpoints)**
- `POST /mobile/api/visitor/add_to_cart/` - Add to cart
- `GET /mobile/api/visitor/cart/` - Get cart
- `POST /mobile/api/visitor/create_order/` - Create visitor order

**Admin (5 endpoints)**
- `GET /mobile/api/admin/dashboard_stats/` - Dashboard statistics
- `GET /mobile/api/admin/users/` - User management
- `GET /mobile/api/admin/pending_products/` - Pending products
- `POST /mobile/api/admin/{id}/approve_product/` - Approve product
- `POST /mobile/api/admin/{id}/reject_product/` - Reject product

**Payment (2 endpoints)**
- `POST /mobile/api/payment/` - Process payment
- `PUT /mobile/api/payment/` - Verify payment

#### **User Types & Permissions**

**✅ CLIENT Users**
- Full product management (create, edit, delete)
- Order management (buy, sell, track)
- Favorites and wishlist
- Wallet and transactions
- 2FA setup and management
- Profile management

**✅ ADMIN Users**
- All client permissions
- User management dashboard
- Product moderation (approve/reject)
- System statistics and analytics
- Admin-specific endpoints

**✅ VISITOR (No Authentication)**
- Browse all active products
- Search and filter functionality
- Session-based shopping cart
- Add items without registration
- Guest checkout with customer information
- Pickup point selection
- Multiple payment methods

#### **Database Integration**
- **✅ Perfect Compatibility** - Uses existing database models without changes
- **✅ Zero Web Impact** - No impact on existing web functionality
- **✅ Model Relationships** - All relationships properly maintained
- **✅ Visitor Orders** - Uses regular Order model with visitor fields
- **✅ Performance Optimized** - Efficient queries with select_related/prefetch_related

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

#### Mobile Application (React Native/Flutter)
- **Offline Mode**: Works without internet connection
- **Splash Screen**: Professional app loading experience
- **Connection Management**: Smart connection detection and fallback
- **Progressive Web App**: PWA features for web-to-mobile conversion
- **African Theme**: Cultural customization ready
- **Visitor Landing Page**: Anonymous shopping experience

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
- **Mobile Integration**: 2FA support in mobile API

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

# JWT Settings (for mobile API)
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_LIFETIME=3600
JWT_REFRESH_TOKEN_LIFETIME=604800
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

### **React Native Integration** 🆕

The mobile backend is **100% ready** for React Native development with:

#### **Complete API Client Setup**
```typescript
// API Client Configuration
const apiClient = new ApiClient({
  baseURL: 'http://localhost:8000/mobile/api/',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  }
});
```

#### **Authentication Flow**
```typescript
// Login with 2FA support
const login = async (email: string, password: string) => {
  const response = await apiClient.post('/auth/login/', {
    email, password
  });
  
  if (response.requires_2fa) {
    // Handle 2FA verification
    return { requires2FA: true, message: response.message };
  }
  
  // Store tokens and user data
  await AsyncStorage.setItem('access_token', response.tokens.access_token);
  return { user: response.user, tokens: response.tokens };
};
```

#### **State Management with Redux**
```typescript
// Redux store configuration
const store = configureStore({
  reducer: {
    auth: authReducer,
    products: productReducer,
    cart: cartReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
    }),
});
```

#### **African Theme Components**
```typescript
// African-themed button component
const AfricanButton = ({ title, onPress, variant = 'primary' }) => {
  return (
    <TouchableOpacity
      style={[styles.base, styles[variant]]}
      onPress={onPress}
    >
      <Text style={styles.text}>{title}</Text>
    </TouchableOpacity>
  );
};
```

### Building the Mobile App

1. **Mobile App Development**:
   ```bash
   # For React Native development
   npx react-native init VGKMobileApp --template react-native-template-typescript
   cd VGKMobileApp
   
   # Install dependencies
   npm install @react-navigation/native @react-navigation/stack
   npm install @reduxjs/toolkit react-redux
   npm install axios @react-native-async-storage/async-storage
   npm install react-native-elements react-native-vector-icons
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
- **Splash Screen**: Professional app loading with African theme
- **Connection Management**: Smart online/offline detection
- **Push Notifications**: Real-time updates
- **Camera Integration**: Product photo capture
- **Location Services**: Local product discovery
- **Visitor Shopping**: Anonymous shopping experience
- **2FA Authentication**: Enhanced security
- **Payment Integration**: Multiple payment methods

## 🔧 Mobile API Testing

### **Test the Mobile Backend** 🆕

```bash
# Run all mobile API tests
python manage.py test backend.mobile.tests

# Run specific test class
python manage.py test backend.mobile.tests.MobileAPITestCase

# Test authentication endpoints
python manage.py test backend.mobile.tests.MobileAPITestCase.test_login_without_2fa

# Test visitor functionality
python manage.py test backend.mobile.tests.MobileAPITestCase.test_visitor_add_to_cart

# Test admin features
python manage.py test backend.mobile.tests.MobileAPITestCase.test_admin_dashboard_stats
```

### **API Health Check** 🆕

```bash
# Test mobile API health
curl http://localhost:8000/mobile/api/health/

# Expected response:
{
  "success": true,
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0"
}
```

### **Authentication Test** 🆕

```bash
# Test login endpoint
curl -X POST http://localhost:8000/mobile/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# Test visitor cart
curl -X POST http://localhost:8000/mobile/api/visitor/add_to_cart/ \
  -H "Content-Type: application/json" \
  -d '{"product_id":"product_id","quantity":1,"session_key":"test_session"}'
```

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
JWT_SECRET_KEY=your-jwt-secret-key
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

### **Mobile API Issues** 🆕

1. **Import Errors**:
   ```bash
   # Check if mobile package is properly installed
   python manage.py check
   
   # Verify imports
   python -c "from backend.mobile import views, serializers; print('Mobile API imports successful')"
   ```

2. **Authentication Issues**:
   ```bash
   # Test JWT token generation
   curl -X POST http://localhost:8000/mobile/api/auth/login/ \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"password"}'
   
   # Test 2FA verification
   curl -X POST http://localhost:8000/mobile/api/auth/verify_2fa/ \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","code":"123456"}'
   ```

3. **Visitor Cart Issues**:
   ```bash
   # Test visitor cart functionality
   curl -X POST http://localhost:8000/mobile/api/visitor/add_to_cart/ \
     -H "Content-Type: application/json" \
     -d '{"product_id":"product_id","quantity":1,"session_key":"test_session"}'
   ```

4. **Admin Endpoint Issues**:
   ```bash
   # Test admin endpoints (requires admin user)
   curl -X GET http://localhost:8000/mobile/api/admin/dashboard_stats/ \
     -H "Authorization: Bearer your_admin_token"
   ```

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

2. **Mobile App Development Issues**:
   ```bash
   # React Native setup issues
   npx react-native doctor
   
   # Flutter setup issues
   flutter doctor
   
   # Android SDK setup
   # Download Android Studio and configure SDK
   ```

3. **API Connection Issues**:
   ```bash
   # Test Django API endpoints
   curl http://localhost:8000/mobile/api/health/
   
   # Check CORS configuration
   # Ensure mobile app can access Django backend
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
- **Mobile API Performance**: Monitor mobile endpoint usage

### Error Monitoring

- **Sentry Integration**: Error tracking and alerting
- **Log Aggregation**: Centralized logging
- **Performance Alerts**: Automated performance monitoring
- **Mobile API Monitoring**: Track mobile-specific errors

## 🔧 Configuration Options

### **Mobile API Configuration** 🆕

```python
# Mobile API settings in settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'backend.mobile.authentication.MobileJWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8081",  # React Native Metro
    "http://localhost:19006", # Expo
]
```

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
    'REQUIRE_CONNECTION_FOR': ['chat', 'orders', 'payments'],
    'AFRICAN_THEME': True,
    'VISITOR_SHOPPING': True,
    '2FA_SUPPORT': True
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
│   ├── models.py           # Database models
│   └── mobile/             # 🆕 Mobile API package
│       ├── __init__.py
│       ├── serializers.py  # 25 API serializers
│       ├── views.py        # 10 view classes
│       ├── urls.py         # URL routing
│       ├── jwt_utils.py    # JWT utilities
│       ├── authentication.py # Custom auth
│       ├── permissions.py  # Custom permissions
│       ├── tests.py        # 15 test cases
│       ├── README.md       # API documentation
│       └── doc/            # Documentation folder
├── mobile_api/             # Mobile API endpoints
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
# Run all tests
python manage.py test

# Run specific tests
python manage.py test backend.tests.AITestCase
python manage.py test backend.tests.NotificationTestCase

# 🆕 Run mobile API tests
python manage.py test backend.mobile.tests
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
4. Add tests (including mobile API tests)
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Email: support@videgrenierkamer.com
- Phone: +237 694 63 84 12
- WhatsApp: +237 694 63 84 12

## 🔄 Changelog

### Version 1.1.0 (Latest) 🆕
- ✅ **COMPLETE MOBILE BACKEND IMPLEMENTATION**
- ✅ 32 API endpoints for mobile applications
- ✅ JWT authentication with 2FA support
- ✅ Visitor shopping functionality
- ✅ Payment integration (Mobile Money, Card, Cash)
- ✅ Admin management on mobile
- ✅ React Native integration ready
- ✅ Comprehensive mobile API documentation
- ✅ 15 test cases for mobile API
- ✅ Zero impact on web functionality
- ✅ Production-ready mobile backend

### Version 1.0.0
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

**Now with Complete Mobile Backend Support! 📱🚀** 