# Mobile Development Guide - Vidé-Grenier Kamer

## Overview

This guide provides comprehensive instructions for developing a React Native mobile application using MVVM architecture that connects to the Vidé-Grenier Kamer Django backend. The mobile app features a rich African theme with vibrant colors, cultural elements, and a user-friendly flow: Splash Screen → Terms & Conditions → Visitor Landing Page → Authentication → Main App.

## Technology Stack

### Mobile App
- **Framework**: React Native (Latest version)
- **Architecture**: MVVM (Model-View-ViewModel)
- **State Management**: Redux Toolkit or Zustand
- **Navigation**: React Navigation v6
- **HTTP Client**: Axios
- **Storage**: AsyncStorage
- **UI Components**: React Native Elements + Custom African Theme
- **Icons**: React Native Vector Icons
- **Animations**: React Native Reanimated

### Backend API
- **Framework**: Django 4.x
- **API**: Django REST Framework
- **Authentication**: JWT Tokens
- **Database**: PostgreSQL/SQLite
- **File Storage**: Local + Cloud (AWS S3)

## African Theme Design Guidelines

### Color Palette
```javascript
// Primary Colors - African Heritage
const colors = {
  // Primary Colors
  primaryOrange: '#FF6B35',      // African Sunset
  primaryYellow: '#FFD23F',      // African Gold
  primaryGreen: '#2E8B57',       // African Forest
  primaryBrown: '#8B4513',       // African Soil
  primaryRed: '#DC143C',         // African Ruby
  
  // Secondary Colors
  secondaryBeige: '#F5F5DC',     // African Sand
  secondaryCream: '#FFF8DC',     // African Ivory
  secondaryDark: '#2F2F2F',      // African Night
  secondaryLight: '#FAFAFA',     // African Cloud
  
  // Accent Colors
  accentGold: '#FFD700',         // African Gold
  accentCopper: '#B87333',       // African Copper
  accentTerracotta: '#E2725B',   // African Terracotta
  
  // Additional Colors
  white: '#FFFFFF',
  black: '#000000',
  gray: '#666666',
  lightGray: '#E0E0E0',
  success: '#28A745',
  error: '#DC3545',
  warning: '#FFC107',
  info: '#17A2B8'
};
```

### Typography
```javascript
// Font Families
const fonts = {
  primary: 'Poppins-Regular',      // Modern African
  primaryBold: 'Poppins-Bold',     // Bold variant
  primaryMedium: 'Poppins-Medium', // Medium variant
  secondary: 'Roboto-Regular',     // Clean & Readable
  secondaryBold: 'Roboto-Bold',    // Bold variant
  accent: 'PlayfairDisplay-Regular' // Elegant Headers
};

// Font Sizes
const fontSizes = {
  xs: 12,
  sm: 14,
  base: 16,
  lg: 18,
  xl: 20,
  '2xl': 24,
  '3xl': 30,
  '4xl': 36,
  '5xl': 48
};
```

### Design Elements
- **Patterns**: African geometric patterns, tribal motifs
- **Icons**: Hand-drawn style, organic shapes
- **Images**: African marketplace scenes, local products
- **Animations**: Smooth transitions with African rhythm
- **Spacing**: Generous padding and margins for breathing room

## MVVM Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    React Native App                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │    Views    │    │ ViewModels  │    │   Models    │    │
│  │             │    │             │    │             │    │
│  │ • Splash    │◄──►│ • AuthVM    │◄──►│ • User      │    │
│  │ • Terms     │    │ • ProductVM │    │ • Product   │    │
│  │ • Landing   │    │ • OrderVM   │    │ • Order     │    │
│  │ • Auth      │    │ • ChatVM    │    │ • Chat      │    │
│  │ • Dashboard │    │ • WalletVM  │    │ • Wallet    │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Django Backend API                      │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │   Views     │    │ Serializers │    │   Models    │    │
│  │             │    │             │    │             │    │
│  │ • Auth      │◄──►│ • User      │◄──►│ • User      │    │
│  │ • Products  │    │ • Product   │    │ • Product   │    │
│  │ • Orders    │    │ • Order     │    │ • Order     │    │
│  │ • Chat      │    │ • Chat      │    │ • Chat      │    │
│  │ • Admin     │    │ • Admin     │    │ • Admin     │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## User Types for Mobile

The mobile application supports **3 user types**:

1. **Admin** - Full administrative access
2. **Client** - Regular users who can buy and sell
3. **Visitor** - Anonymous users (limited functionality)

## Mobile App Flow

### App Launch Sequence
1. **Splash Screen** (3-5 seconds)
   - African-themed logo animation with gradient colors
   - App name "Vidé-Grenier Kamer" with African typography
   - Tagline "Le Marché Africain Numérique"
   - Loading animation with African-inspired dots
   - Smooth fade-in transitions

2. **Terms & Conditions** (First time only)
   - African-themed design with warm colors
   - Clear, readable terms in French
   - Checkbox for acceptance
   - Accept/Decline buttons with confirmation dialogs
   - Scrollable content with proper spacing

3. **Visitor Landing Page**
   - Welcome message with African hospitality
   - Featured products showcase with horizontal scroll
   - "Pourquoi Choisir VGK?" section with features
   - Three main action buttons:
     - "Parcourir les Produits" (Browse Products)
     - "Se Connecter" (Login)
     - "S'inscrire" (Register)
   - African cultural elements and patterns

4. **Authentication Flow** (Optional)
   - Login screen with African theme
   - Registration screen with form validation
   - Password reset functionality
   - Phone verification process

5. **Main App Interface**
   - User type-specific dashboard
   - African-themed navigation
   - Cultural elements throughout
   - Bottom tab navigation with African icons

## Backend API Updates Required

### 1. Django Settings Updates
```python
# settings/base.py - Add mobile API settings
INSTALLED_APPS += [
    'rest_framework',
    'corsheaders',
    'rest_framework_simplejwt',
]

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# JWT Settings
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# CORS Settings for Mobile
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8081",  # React Native Metro
    "http://localhost:19006", # Expo
]

CORS_ALLOW_CREDENTIALS = True
```

### 2. Mobile API Serializers
```python
# backend/serializers.py
from rest_framework import serializers
from .models import User, Product, Order, Category

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'phone', 'first_name', 'last_name', 
                 'user_type', 'city', 'is_verified', 'phone_verified',
                 'trust_score', 'loyalty_points', 'loyalty_level', 
                 'profile_picture', 'date_joined']
        read_only_fields = ['id', 'date_joined', 'trust_score', 
                           'loyalty_points', 'loyalty_level']

class ProductSerializer(serializers.ModelSerializer):
    seller = UserSerializer(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Product
        fields = ['id', 'title', 'description', 'price', 'condition',
                 'category', 'category_name', 'seller', 'images',
                 'is_favorite', 'created_at', 'status']
        read_only_fields = ['id', 'seller', 'created_at', 'status']

class OrderSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    buyer = UserSerializer(read_only=True)
    seller = UserSerializer(read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'product', 'buyer', 'seller', 'quantity',
                 'total_amount', 'status', 'pickup_point', 'created_at']
        read_only_fields = ['id', 'created_at']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'icon', 'product_count']
```

### 3. Mobile API Views
```python
# backend/mobile_views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from django_filters.rest_framework import DjangoFilterBackend
from .serializers import *
from .models import *

class MobileAuthViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        # Custom login logic with JWT
        pass
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        # Custom registration logic
        pass

class MobileProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category', 'condition', 'price', 'city']
    
    def get_queryset(self):
        return Product.objects.filter(status='ACTIVE')
    
    @action(detail=True, methods=['post'])
    def favorite(self, request, pk=None):
        # Toggle favorite logic
        pass

class MobileOrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'ADMIN':
            return Order.objects.all()
        return Order.objects.filter(buyer=user) | Order.objects.filter(seller=user)
```

### 4. Mobile API URLs
```python
# backend/urls_mobile.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .mobile_views import *

router = DefaultRouter()
router.register(r'auth', MobileAuthViewSet, basename='mobile-auth')
router.register(r'products', MobileProductViewSet, basename='mobile-products')
router.register(r'orders', MobileOrderViewSet, basename='mobile-orders')
router.register(r'categories', CategoryViewSet, basename='mobile-categories')

urlpatterns = [
    path('mobile/api/', include(router.urls)),
    path('mobile/api/health/', HealthCheckView.as_view(), name='mobile-health'),
    path('mobile/api/search/', SearchView.as_view(), name='mobile-search'),
]
```

## API Base URL

```
Development: http://localhost:8000/mobile/api/
Production: https://yourdomain.com/mobile/api/
```

## Authentication

### JWT Token Authentication

The mobile API uses JWT (JSON Web Tokens) for authentication.

#### Login
```http
POST /mobile/api/auth/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "success": true,
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "phone": "+237123456789",
    "first_name": "John",
    "last_name": "Doe",
    "user_type": "CLIENT",
    "city": "DOUALA",
    "is_verified": true,
    "phone_verified": true,
    "trust_score": 100,
    "loyalty_points": 150,
    "loyalty_level": "silver",
    "profile_picture": "https://.../profile.jpg"
  }
}
```

#### Register
```http
POST /mobile/api/auth/register/
Content-Type: application/json

{
  "email": "newuser@example.com",
  "phone": "+237123456789",
  "password": "password123",
  "first_name": "John",
  "last_name": "Doe",
  "user_type": "CLIENT",
  "city": "DOUALA",
  "address": "123 Main Street"
}
```

#### Using JWT Token
Include the token in the Authorization header:
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## API Endpoints

### 1. Authentication
- `POST /mobile/api/auth/login/` - User login
- `POST /mobile/api/auth/register/` - User registration
- `POST /mobile/api/auth/logout/` - User logout

### 2. Products
- `GET /mobile/api/products/` - List products (with filters)
- `GET /mobile/api/products/{id}/` - Get product details
- `POST /mobile/api/products/{id}/favorite/` - Toggle favorite

### 3. Categories
- `GET /mobile/api/categories/` - List all categories

### 4. User Profile
- `GET /mobile/api/user/profile/` - Get user profile
- `PUT /mobile/api/user/profile/update/` - Update profile
- `GET /mobile/api/user/favorites/` - Get user favorites

### 5. Search
- `GET /mobile/api/search/?q=query` - Search products

### 6. Health Check
- `GET /mobile/api/health/` - API health status

## React Native Implementation

### Project Setup
```bash
# Create new React Native project
npx react-native@latest init VGKMobileApp --template react-native-template-typescript

# Navigate to project
cd VGKMobileApp

# Install core dependencies
npm install @react-navigation/native @react-navigation/stack @react-navigation/bottom-tabs
npm install react-native-screens react-native-safe-area-context
npm install react-native-gesture-handler react-native-reanimated
npm install react-native-vector-icons react-native-linear-gradient
npm install react-native-splash-screen react-native-screens

# Install state management and API
npm install @reduxjs/toolkit react-redux
npm install axios @react-native-async-storage/async-storage
npm install react-hook-form @hookform/resolvers yup

# Install UI and utilities
npm install react-native-elements react-native-paper
npm install react-native-image-picker react-native-fast-image
npm install react-native-modal react-native-toast-message
npm install react-native-sound react-native-vibration

# Install development dependencies
npm install --save-dev @types/react-native @types/react
npm install --save-dev react-native-flipper
```

### Project Structure (MVVM Architecture)
```
src/
├── assets/
│   ├── images/
│   │   ├── african-logo.png
│   │   ├── african-welcome.png
│   │   ├── patterns/
│   │   └── products/
│   ├── icons/
│   │   ├── african-market.svg
│   │   ├── african-phone.svg
│   │   └── african-bag.svg
│   └── fonts/
│       ├── Poppins-Regular.ttf
│       ├── Poppins-Bold.ttf
│       └── Poppins-Medium.ttf
├── components/
│   ├── common/
│   │   ├── AfricanButton.tsx
│   │   ├── AfricanCard.tsx
│   │   ├── AfricanInput.tsx
│   │   └── LoadingSpinner.tsx
│   ├── SplashScreen.tsx
│   ├── TermsConditions.tsx
│   └── VisitorLanding.tsx
├── screens/
│   ├── auth/
│   │   ├── LoginScreen.tsx
│   │   ├── RegisterScreen.tsx
│   │   └── ForgotPasswordScreen.tsx
│   ├── visitor/
│   │   ├── ProductListScreen.tsx
│   │   ├── ProductDetailScreen.tsx
│   │   └── SearchScreen.tsx
│   ├── client/
│   │   ├── DashboardScreen.tsx
│   │   ├── MyProductsScreen.tsx
│   │   ├── OrdersScreen.tsx
│   │   ├── ChatScreen.tsx
│   │   └── WalletScreen.tsx
│   └── admin/
│       ├── AdminDashboardScreen.tsx
│       ├── UserManagementScreen.tsx
│       └── ProductModerationScreen.tsx
├── navigation/
│   ├── AppNavigator.tsx
│   ├── AuthNavigator.tsx
│   ├── VisitorNavigator.tsx
│   ├── ClientNavigator.tsx
│   └── AdminNavigator.tsx
├── viewmodels/
│   ├── AuthViewModel.ts
│   ├── ProductViewModel.ts
│   ├── OrderViewModel.ts
│   ├── ChatViewModel.ts
│   └── WalletViewModel.ts
├── models/
│   ├── User.ts
│   ├── Product.ts
│   ├── Order.ts
│   ├── Chat.ts
│   └── Wallet.ts
├── services/
│   ├── api/
│   │   ├── ApiService.ts
│   │   ├── AuthService.ts
│   │   ├── ProductService.ts
│   │   └── OrderService.ts
│   ├── storage/
│   │   ├── AsyncStorageService.ts
│   │   └── SecureStorageService.ts
│   └── utils/
│       ├── ValidationUtils.ts
│       ├── FormatUtils.ts
│       └── NotificationUtils.ts
├── store/
│   ├── index.ts
│   ├── slices/
│   │   ├── authSlice.ts
│   │   ├── productSlice.ts
│   │   └── orderSlice.ts
│   └── middleware/
│       └── apiMiddleware.ts
├── theme/
│   ├── colors.ts
│   ├── fonts.ts
│   ├── spacing.ts
│   └── index.ts
└── utils/
    ├── constants.ts
    ├── helpers.ts
    └── types.ts
```

### Theme Configuration
```typescript
// src/theme/index.ts
import { colors } from './colors';
import { fonts } from './fonts';
import { spacing } from './spacing';

export const theme = {
  colors,
  fonts,
  spacing,
  borderRadius: {
    sm: 4,
    md: 8,
    lg: 12,
    xl: 16,
    full: 9999,
  },
  shadows: {
    sm: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.05,
      shadowRadius: 2,
      elevation: 2,
    },
    md: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.1,
      shadowRadius: 4,
      elevation: 4,
    },
    lg: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.15,
      shadowRadius: 8,
      elevation: 8,
    },
  },
};

export type Theme = typeof theme;
```

### Key Component Implementations

#### 1. African Button Component
```typescript
// src/components/common/AfricanButton.tsx
import React from 'react';
import {
  TouchableOpacity,
  Text,
  StyleSheet,
  ActivityIndicator,
  ViewStyle,
  TextStyle,
} from 'react-native';
import { theme } from '../../theme';

interface AfricanButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'outline';
  size?: 'small' | 'medium' | 'large';
  loading?: boolean;
  disabled?: boolean;
  style?: ViewStyle;
  textStyle?: TextStyle;
}

export const AfricanButton: React.FC<AfricanButtonProps> = ({
  title,
  onPress,
  variant = 'primary',
  size = 'medium',
  loading = false,
  disabled = false,
  style,
  textStyle,
}) => {
  const buttonStyle = [
    styles.button,
    styles[variant],
    styles[size],
    disabled && styles.disabled,
    style,
  ];

  const textStyleCombined = [
    styles.text,
    styles[`${variant}Text`],
    styles[`${size}Text`],
    disabled && styles.disabledText,
    textStyle,
  ];

  return (
    <TouchableOpacity
      style={buttonStyle}
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.8}
    >
      {loading ? (
        <ActivityIndicator
          color={variant === 'primary' ? theme.colors.white : theme.colors.primaryOrange}
          size="small"
        />
      ) : (
        <Text style={textStyleCombined}>{title}</Text>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  button: {
    borderRadius: theme.borderRadius.lg,
    alignItems: 'center',
    justifyContent: 'center',
  },
  primary: {
    backgroundColor: theme.colors.primaryOrange,
  },
  secondary: {
    backgroundColor: theme.colors.primaryGreen,
  },
  outline: {
    backgroundColor: 'transparent',
    borderWidth: 2,
    borderColor: theme.colors.primaryOrange,
  },
  small: {
    paddingVertical: 8,
    paddingHorizontal: 16,
  },
  medium: {
    paddingVertical: 12,
    paddingHorizontal: 24,
  },
  large: {
    paddingVertical: 16,
    paddingHorizontal: 32,
  },
  disabled: {
    backgroundColor: theme.colors.lightGray,
    borderColor: theme.colors.lightGray,
  },
  text: {
    fontFamily: theme.fonts.primaryBold,
    textAlign: 'center',
  },
  primaryText: {
    color: theme.colors.white,
  },
  secondaryText: {
    color: theme.colors.white,
  },
  outlineText: {
    color: theme.colors.primaryOrange,
  },
  smallText: {
    fontSize: theme.fontSizes.sm,
  },
  mediumText: {
    fontSize: theme.fontSizes.base,
  },
  largeText: {
    fontSize: theme.fontSizes.lg,
  },
  disabledText: {
    color: theme.colors.gray,
  },
});
```

### Splash Screen Implementation
```typescript
// src/components/SplashScreen.tsx
import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  Dimensions,
  Image,
} from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import { theme } from '../theme';

const { width, height } = Dimensions.get('window');

interface SplashScreenProps {
  onComplete: () => void;
}

export const SplashScreen: React.FC<SplashScreenProps> = ({ onComplete }) => {
  const logoOpacity = useRef(new Animated.Value(0)).current;
  const logoScale = useRef(new Animated.Value(0.3)).current;
  const textOpacity = useRef(new Animated.Value(0)).current;
  const dotScales = useRef([
    new Animated.Value(1),
    new Animated.Value(1),
    new Animated.Value(1),
  ]).current;

  useEffect(() => {
    // Logo animation sequence
    Animated.sequence([
      Animated.parallel([
        Animated.timing(logoOpacity, {
          toValue: 1,
          duration: 1000,
          useNativeDriver: true,
        }),
        Animated.spring(logoScale, {
          toValue: 1,
          tension: 50,
          friction: 7,
          useNativeDriver: true,
        }),
      ]),
      Animated.timing(textOpacity, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
    ]).start();

    // Loading dots animation
    const dotAnimations = dotScales.map((dotScale, index) =>
      Animated.loop(
        Animated.sequence([
          Animated.timing(dotScale, {
            toValue: 1.2,
            duration: 600,
            delay: index * 200,
            useNativeDriver: true,
          }),
          Animated.timing(dotScale, {
            toValue: 1,
            duration: 600,
            useNativeDriver: true,
          }),
        ])
      )
    );

    Animated.parallel(dotAnimations).start();

    // Auto navigate after 3.5 seconds
    const timer = setTimeout(() => {
      onComplete();
    }, 3500);

    return () => clearTimeout(timer);
  }, [onComplete]);

  return (
    <LinearGradient
      colors={[
        theme.colors.primaryOrange,
        theme.colors.primaryYellow,
        theme.colors.primaryGreen,
      ]}
      style={styles.container}
    >
      <View style={styles.content}>
        <Animated.View
          style={[
            styles.logoContainer,
            {
              opacity: logoOpacity,
              transform: [{ scale: logoScale }],
            },
          ]}
        >
          <Image
            source={require('../assets/images/african-logo.png')}
            style={styles.logo}
            resizeMode="contain"
          />
        </Animated.View>

        <Animated.Text
          style={[
            styles.appName,
            { opacity: textOpacity },
          ]}
        >
          Vidé-Grenier Kamer
        </Animated.Text>

        <Animated.Text
          style={[
            styles.tagline,
            { opacity: textOpacity },
          ]}
        >
          Le Marché Africain Numérique
        </Animated.Text>

        <View style={styles.loadingContainer}>
          <View style={styles.loadingDots}>
            {dotScales.map((dotScale, index) => (
              <Animated.View
                key={index}
                style={[
                  styles.dot,
                  {
                    transform: [{ scale: dotScale }],
                  },
                ]}
              />
            ))}
          </View>
        </View>
      </View>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    alignItems: 'center',
  },
  logoContainer: {
    marginBottom: 30,
  },
  logo: {
    width: 120,
    height: 120,
  },
  appName: {
    fontSize: theme.fontSizes['4xl'],
    fontFamily: theme.fonts.primaryBold,
    color: theme.colors.white,
    textAlign: 'center',
    marginBottom: 10,
  },
  tagline: {
    fontSize: theme.fontSizes.base,
    fontFamily: theme.fonts.primary,
    color: theme.colors.white,
    textAlign: 'center',
    marginBottom: 50,
  },
  loadingContainer: {
    marginTop: 50,
  },
  loadingDots: {
    flexDirection: 'row',
    justifyContent: 'center',
  },
  dot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginHorizontal: 5,
    backgroundColor: theme.colors.white,
  },
});
```

### Terms & Conditions Screen
```typescript
// src/components/TermsConditions.tsx
import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import { theme } from '../theme';
import { AfricanButton } from './common/AfricanButton';

interface TermsConditionsProps {
  onAccept: () => void;
  onDecline: () => void;
}

export const TermsConditions: React.FC<TermsConditionsProps> = ({
  onAccept,
  onDecline,
}) => {
  const [accepted, setAccepted] = useState(false);

  const handleAccept = () => {
    if (accepted) {
      onAccept();
    } else {
      Alert.alert(
        'Conditions Requises',
        'Veuillez accepter les termes et conditions pour continuer.',
        [{ text: 'OK' }]
      );
    }
  };

  const handleDecline = () => {
    Alert.alert(
      'Confirmation',
      'Êtes-vous sûr de vouloir refuser les termes et conditions ? L\'application ne peut pas fonctionner sans votre acceptation.',
      [
        { text: 'Annuler', style: 'cancel' },
        { text: 'Refuser', style: 'destructive', onPress: onDecline },
      ]
    );
  };

  return (
    <LinearGradient
      colors={[theme.colors.secondaryBeige, theme.colors.secondaryCream]}
      style={styles.container}
    >
      <View style={styles.header}>
        <Text style={styles.title}>Termes et Conditions</Text>
        <Text style={styles.subtitle}>Vidé-Grenier Kamer</Text>
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>1. Acceptation des Conditions</Text>
          <Text style={styles.text}>
            En utilisant l'application Vidé-Grenier Kamer, vous acceptez d'être lié par ces termes et conditions.
          </Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>2. Utilisation du Service</Text>
          <Text style={styles.text}>
            L'application permet aux utilisateurs de vendre et acheter des articles d'occasion de manière sécurisée.
          </Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>3. Responsabilités</Text>
          <Text style={styles.text}>
            Les utilisateurs sont responsables de la véracité des informations fournies et de la qualité des produits vendus.
          </Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>4. Protection des Données</Text>
          <Text style={styles.text}>
            Vos données personnelles sont protégées conformément à notre politique de confidentialité.
          </Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>5. Paiements</Text>
          <Text style={styles.text}>
            Les transactions sont sécurisées et gérées par nos partenaires de paiement certifiés.
          </Text>
        </View>
      </ScrollView>

      <View style={styles.footer}>
        <TouchableOpacity
          style={styles.checkboxContainer}
          onPress={() => setAccepted(!accepted)}
        >
          <View style={[styles.checkbox, accepted && styles.checkboxChecked]}>
            {accepted && <Text style={styles.checkmark}>✓</Text>}
          </View>
          <Text style={styles.checkboxText}>
            J'accepte les termes et conditions
          </Text>
        </TouchableOpacity>

        <View style={styles.buttonContainer}>
          <AfricanButton
            title="Refuser"
            onPress={handleDecline}
            variant="outline"
            style={styles.declineButton}
          />

          <AfricanButton
            title="Accepter"
            onPress={handleAccept}
            variant="primary"
            disabled={!accepted}
            style={styles.acceptButton}
          />
        </View>
      </View>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    padding: 20,
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.lightGray,
  },
  title: {
    fontSize: theme.fontSizes['2xl'],
    fontFamily: theme.fonts.primaryBold,
    color: theme.colors.secondaryDark,
    marginBottom: 5,
  },
  subtitle: {
    fontSize: theme.fontSizes.base,
    fontFamily: theme.fonts.primary,
    color: theme.colors.gray,
  },
  content: {
    flex: 1,
    padding: 20,
  },
  section: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: theme.fontSizes.lg,
    fontFamily: theme.fonts.primaryBold,
    color: theme.colors.secondaryDark,
    marginBottom: 10,
  },
  text: {
    fontSize: theme.fontSizes.sm,
    fontFamily: theme.fonts.primary,
    color: theme.colors.gray,
    lineHeight: 22,
  },
  footer: {
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: theme.colors.lightGray,
  },
  checkboxContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  checkbox: {
    width: 24,
    height: 24,
    borderWidth: 2,
    borderColor: theme.colors.primaryOrange,
    borderRadius: 4,
    marginRight: 10,
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkboxChecked: {
    backgroundColor: theme.colors.primaryOrange,
  },
  checkmark: {
    color: theme.colors.white,
    fontSize: 16,
    fontFamily: theme.fonts.primaryBold,
  },
  checkboxText: {
    fontSize: theme.fontSizes.sm,
    fontFamily: theme.fonts.primary,
    color: theme.colors.secondaryDark,
  },
  buttonContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 10,
  },
  declineButton: {
    flex: 1,
  },
  acceptButton: {
    flex: 1,
  },
});
```

### Visitor Landing Page
```javascript
// src/components/VisitorLanding.js
import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
  Dimensions,
} from 'react-native';
import LinearGradient from 'react-native-linear-gradient';

const { width } = Dimensions.get('window');

const VisitorLanding = ({ onLogin, onRegister, onBrowseProducts }) => {
  const featuredProducts = [
    {
      id: 1,
      name: 'Téléphone Samsung',
      price: '45,000 FCFA',
      image: require('../assets/images/product1.jpg'),
    },
    {
      id: 2,
      name: 'Sac à Main Africain',
      price: '15,000 FCFA',
      image: require('../assets/images/product2.jpg'),
    },
    {
      id: 3,
      name: 'Chaussures Confortables',
      price: '25,000 FCFA',
      image: require('../assets/images/product3.jpg'),
    },
  ];

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      <LinearGradient
        colors={['#FF6B35', '#FFD23F']}
        style={styles.header}
      >
        <View style={styles.headerContent}>
          <Image
            source={require('../assets/images/african-welcome.png')}
            style={styles.welcomeImage}
            resizeMode="contain"
          />
          <Text style={styles.welcomeTitle}>
            Bienvenue sur Vidé-Grenier Kamer
          </Text>
          <Text style={styles.welcomeSubtitle}>
            Le marché africain numérique où vous trouvez tout ce dont vous avez besoin
          </Text>
        </View>
      </LinearGradient>

      <View style={styles.content}>
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Produits Vedettes</Text>
          <Text style={styles.sectionSubtitle}>
            Découvrez nos meilleures offres du moment
          </Text>
        </View>

        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={styles.productsContainer}
        >
          {featuredProducts.map((product) => (
            <TouchableOpacity
              key={product.id}
              style={styles.productCard}
              onPress={() => onBrowseProducts()}
            >
              <Image source={product.image} style={styles.productImage} />
              <View style={styles.productInfo}>
                <Text style={styles.productName}>{product.name}</Text>
                <Text style={styles.productPrice}>{product.price}</Text>
              </View>
            </TouchableOpacity>
          ))}
        </ScrollView>

        <View style={styles.featuresSection}>
          <Text style={styles.sectionTitle}>Pourquoi Choisir VGK ?</Text>
          
          <View style={styles.featureItem}>
            <View style={styles.featureIcon}>
              <Text style={styles.iconText}>🛡️</Text>
            </View>
            <View style={styles.featureContent}>
              <Text style={styles.featureTitle}>Transactions Sécurisées</Text>
              <Text style={styles.featureDescription}>
                Paiements sécurisés et protection des données
              </Text>
            </View>
          </View>

          <View style={styles.featureItem}>
            <View style={styles.featureIcon}>
              <Text style={styles.iconText}>🚚</Text>
            </View>
            <View style={styles.featureContent}>
              <Text style={styles.featureTitle}>Livraison Rapide</Text>
              <Text style={styles.featureDescription}>
                Points de retrait dans toutes les villes
              </Text>
            </View>
          </View>

          <View style={styles.featureItem}>
            <View style={styles.featureIcon}>
              <Text style={styles.iconText}>💬</Text>
            </View>
            <View style={styles.featureContent}>
              <Text style={styles.featureTitle}>Support Client</Text>
              <Text style={styles.featureDescription}>
                Assistance 24/7 en français et langues locales
              </Text>
            </View>
          </View>
        </View>

        <View style={styles.actionSection}>
          <TouchableOpacity
            style={[styles.actionButton, styles.primaryButton]}
            onPress={onBrowseProducts}
          >
            <Text style={styles.primaryButtonText}>
              Parcourir les Produits
            </Text>
          </TouchableOpacity>

          <View style={styles.authButtons}>
            <TouchableOpacity
              style={[styles.actionButton, styles.secondaryButton]}
              onPress={onLogin}
            >
              <Text style={styles.secondaryButtonText}>Se Connecter</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.actionButton, styles.registerButton]}
              onPress={onRegister}
            >
              <Text style={styles.registerButtonText}>S'inscrire</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FAFAFA',
  },
  header: {
    paddingTop: 60,
    paddingBottom: 40,
    paddingHorizontal: 20,
  },
  headerContent: {
    alignItems: 'center',
  },
  welcomeImage: {
    width: 120,
    height: 120,
    marginBottom: 20,
  },
  welcomeTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#FFF',
    textAlign: 'center',
    fontFamily: 'Poppins-Bold',
    marginBottom: 10,
  },
  welcomeSubtitle: {
    fontSize: 16,
    color: '#FFF',
    textAlign: 'center',
    fontFamily: 'Poppins-Regular',
    lineHeight: 24,
  },
  content: {
    padding: 20,
  },
  section: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#2F2F2F',
    fontFamily: 'Poppins-Bold',
    marginBottom: 5,
  },
  sectionSubtitle: {
    fontSize: 14,
    color: '#666',
    fontFamily: 'Poppins-Regular',
  },
  productsContainer: {
    marginBottom: 30,
  },
  productCard: {
    width: 160,
    marginRight: 15,
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  productImage: {
    width: '100%',
    height: 120,
    borderRadius: 8,
    marginBottom: 10,
  },
  productInfo: {
    alignItems: 'center',
  },
  productName: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#2F2F2F',
    fontFamily: 'Poppins-Bold',
    marginBottom: 5,
  },
  productPrice: {
    fontSize: 16,
    color: '#FF6B35',
    fontWeight: 'bold',
    fontFamily: 'Poppins-Bold',
  },
  featuresSection: {
    marginBottom: 30,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
    backgroundColor: '#FFF',
    padding: 15,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  featureIcon: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#FFD23F',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 15,
  },
  iconText: {
    fontSize: 24,
  },
  featureContent: {
    flex: 1,
  },
  featureTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2F2F2F',
    fontFamily: 'Poppins-Bold',
    marginBottom: 5,
  },
  featureDescription: {
    fontSize: 14,
    color: '#666',
    fontFamily: 'Poppins-Regular',
    lineHeight: 20,
  },
  actionSection: {
    marginBottom: 30,
  },
  actionButton: {
    paddingVertical: 15,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 15,
  },
  primaryButton: {
    backgroundColor: '#FF6B35',
  },
  primaryButtonText: {
    color: '#FFF',
    fontSize: 18,
    fontWeight: 'bold',
    fontFamily: 'Poppins-Bold',
  },
  authButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  secondaryButton: {
    flex: 1,
    backgroundColor: '#F5F5DC',
    borderWidth: 1,
    borderColor: '#FF6B35',
    marginRight: 10,
  },
  registerButton: {
    flex: 1,
    backgroundColor: '#2E8B57',
    marginLeft: 10,
  },
  secondaryButtonText: {
    color: '#FF6B35',
    fontSize: 16,
    fontWeight: 'bold',
    fontFamily: 'Poppins-Bold',
  },
  registerButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: 'bold',
    fontFamily: 'Poppins-Bold',
  },
});

export default VisitorLanding;
```

### API Service
```javascript
// services/api.js
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = 'http://localhost:8000/mobile/api';

class ApiService {
  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add token to requests
    this.api.interceptors.request.use(async (config) => {
      const token = await AsyncStorage.getItem('authToken');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });
  }

  // Authentication
  async login(email, password) {
    const response = await this.api.post('/auth/login/', {
      email,
      password,
    });
    return response.data;
  }

  async register(userData) {
    const response = await this.api.post('/auth/register/', userData);
    return response.data;
  }

  // Products
  async getProducts(params = {}) {
    const response = await this.api.get('/products/', { params });
    return response.data;
  }

  async getProduct(id) {
    const response = await this.api.get(`/products/${id}/`);
    return response.data;
  }

  async toggleFavorite(productId) {
    const response = await this.api.post(`/products/${productId}/favorite/`);
    return response.data;
  }

  // User Profile
  async getUserProfile() {
    const response = await this.api.get('/user/profile/');
    return response.data;
  }

  async updateProfile(profileData) {
    const response = await this.api.put('/user/profile/update/', profileData);
    return response.data;
  }

  // Search
  async searchProducts(query) {
    const response = await this.api.get('/search/', { params: { q: query } });
    return response.data;
  }
}

export default new ApiService();
```

### Authentication Context
```javascript
// contexts/AuthContext.js
import React, { createContext, useState, useContext, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import ApiService from '../services/api';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStoredAuth();
  }, []);

  const loadStoredAuth = async () => {
    try {
      const storedToken = await AsyncStorage.getItem('authToken');
      const storedUser = await AsyncStorage.getItem('user');
      
      if (storedToken && storedUser) {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
      }
    } catch (error) {
      console.error('Error loading stored auth:', error);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await ApiService.login(email, password);
      
      await AsyncStorage.setItem('authToken', response.token);
      await AsyncStorage.setItem('user', JSON.stringify(response.user));
      
      setToken(response.token);
      setUser(response.user);
      
      return response;
    } catch (error) {
      throw error;
    }
  };

  const register = async (userData) => {
    try {
      const response = await ApiService.register(userData);
      
      await AsyncStorage.setItem('authToken', response.token);
      await AsyncStorage.setItem('user', JSON.stringify(response.user));
      
      setToken(response.token);
      setUser(response.user);
      
      return response;
    } catch (error) {
      throw error;
    }
  };

  const logout = async () => {
    try {
      await AsyncStorage.removeItem('authToken');
      await AsyncStorage.removeItem('user');
      
      setToken(null);
      setUser(null);
    } catch (error) {
      console.error('Error during logout:', error);
    }
  };

  return (
    <AuthContext.Provider value={{
      user,
      token,
      loading,
      login,
      register,
      logout,
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
```

## Flutter Implementation

### Setup
```bash
flutter create vgk_mobile_app
cd vgk_mobile_app
flutter pub add http shared_preferences dio
flutter pub add google_fonts flutter_svg
flutter pub add flutter_animate lottie
flutter pub add provider get
```

### App Structure
```
lib/
├── components/
│   ├── splash_screen.dart
│   ├── terms_conditions.dart
│   ├── visitor_landing.dart
│   ├── african_theme.dart
│   └── common/
├── screens/
│   ├── auth/
│   ├── visitor/
│   ├── client/
│   └── admin/
├── navigation/
├── services/
├── utils/
└── assets/
    ├── images/
    ├── icons/
    └── patterns/
```

### Splash Screen Implementation
```dart
// lib/components/splash_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:google_fonts/google_fonts.dart';

class SplashScreen extends StatefulWidget {
  final VoidCallback onComplete;
  
  const SplashScreen({Key? key, required this.onComplete}) : super(key: key);

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    _startAnimation();
  }

  void _startAnimation() {
    Future.delayed(const Duration(seconds: 3), () {
      widget.onComplete();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [
              Color(0xFFFF6B35),
              Color(0xFFFFD23F),
              Color(0xFF2E8B57),
            ],
          ),
        ),
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // Logo with animation
              Image.asset(
                'assets/images/african-logo.png',
                width: 120,
                height: 120,
              )
                  .animate()
                  .fadeIn(duration: 1000.ms)
                  .scale(begin: const Offset(0.3, 0.3), end: const Offset(1, 1))
                  .then()
                  .shake(duration: 500.ms),

              const SizedBox(height: 30),

              // App name with animation
              Text(
                'Vidé-Grenier Kamer',
                style: GoogleFonts.poppins(
                  fontSize: 32,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              )
                  .animate()
                  .fadeIn(delay: 1000.ms, duration: 800.ms)
                  .slideY(begin: 0.3, end: 0),

              const SizedBox(height: 10),

              // Tagline with animation
              Text(
                'Le Marché Africain Numérique',
                style: GoogleFonts.poppins(
                  fontSize: 16,
                  color: Colors.white,
                ),
              )
                  .animate()
                  .fadeIn(delay: 1500.ms, duration: 800.ms)
                  .slideY(begin: 0.3, end: 0),

              const SizedBox(height: 50),

              // Loading dots
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: List.generate(3, (index) {
                  return Container(
                    width: 12,
                    height: 12,
                    margin: const EdgeInsets.symmetric(horizontal: 5),
                    decoration: const BoxDecoration(
                      color: Colors.white,
                      shape: BoxShape.circle,
                    ),
                  )
                      .animate(
                        onPlay: (controller) => controller.repeat(),
                      )
                      .scale(
                        begin: const Offset(1, 1),
                        end: const Offset(1.2, 1.2),
                        duration: 600.ms,
                        delay: Duration(milliseconds: index * 200),
                      )
                      .then()
                      .scale(
                        begin: const Offset(1.2, 1.2),
                        end: const Offset(1, 1),
                        duration: 600.ms,
                      );
                }),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
```

### Terms & Conditions Screen
```dart
// lib/components/terms_conditions.dart
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class TermsConditions extends StatefulWidget {
  final VoidCallback onAccept;
  final VoidCallback onDecline;
  
  const TermsConditions({
    Key? key,
    required this.onAccept,
    required this.onDecline,
  }) : super(key: key);

  @override
  State<TermsConditions> createState() => _TermsConditionsState();
}

class _TermsConditionsState extends State<TermsConditions> {
  bool accepted = false;

  void _handleAccept() {
    if (accepted) {
      widget.onAccept();
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Veuillez accepter les termes et conditions pour continuer.'),
          backgroundColor: Color(0xFFFF6B35),
        ),
      );
    }
  }

  void _handleDecline() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Confirmation'),
        content: const Text(
          'Êtes-vous sûr de vouloir refuser les termes et conditions ? '
          'L\'application ne peut pas fonctionner sans votre acceptation.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Annuler'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              widget.onDecline();
            },
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Refuser'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [
              Color(0xFFF5F5DC),
              Color(0xFFFFF8DC),
            ],
          ),
        ),
        child: Column(
          children: [
            // Header
            Container(
              padding: const EdgeInsets.all(20),
              decoration: const BoxDecoration(
                border: Border(
                  bottom: BorderSide(color: Color(0xFFE0E0E0)),
                ),
              ),
              child: Column(
                children: [
                  Text(
                    'Termes et Conditions',
                    style: GoogleFonts.poppins(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: const Color(0xFF2F2F2F),
                    ),
                  ),
                  const SizedBox(height: 5),
                  Text(
                    'Vidé-Grenier Kamer',
                    style: GoogleFonts.poppins(
                      fontSize: 16,
                      color: const Color(0xFF666666),
                    ),
                  ),
                ],
              ),
            ),

            // Content
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildSection(
                      '1. Acceptation des Conditions',
                      'En utilisant l\'application Vidé-Grenier Kamer, vous acceptez d\'être lié par ces termes et conditions.',
                    ),
                    _buildSection(
                      '2. Utilisation du Service',
                      'L\'application permet aux utilisateurs de vendre et acheter des articles d\'occasion de manière sécurisée.',
                    ),
                    _buildSection(
                      '3. Responsabilités',
                      'Les utilisateurs sont responsables de la véracité des informations fournies et de la qualité des produits vendus.',
                    ),
                    _buildSection(
                      '4. Protection des Données',
                      'Vos données personnelles sont protégées conformément à notre politique de confidentialité.',
                    ),
                    _buildSection(
                      '5. Paiements',
                      'Les transactions sont sécurisées et gérées par nos partenaires de paiement certifiés.',
                    ),
                  ],
                ),
              ),
            ),

            // Footer
            Container(
              padding: const EdgeInsets.all(20),
              decoration: const BoxDecoration(
                border: Border(
                  top: BorderSide(color: Color(0xFFE0E0E0)),
                ),
              ),
              child: Column(
                children: [
                  // Checkbox
                  Row(
                    children: [
                      GestureDetector(
                        onTap: () => setState(() => accepted = !accepted),
                        child: Container(
                          width: 24,
                          height: 24,
                          decoration: BoxDecoration(
                            color: accepted ? const Color(0xFFFF6B35) : Colors.transparent,
                            border: Border.all(
                              color: const Color(0xFFFF6B35),
                              width: 2,
                            ),
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: accepted
                              ? const Icon(
                                  Icons.check,
                                  color: Colors.white,
                                  size: 16,
                                )
                              : null,
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          'J\'accepte les termes et conditions',
                          style: GoogleFonts.poppins(
                            fontSize: 14,
                            color: const Color(0xFF2F2F2F),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 20),

                  // Buttons
                  Row(
                    children: [
                      Expanded(
                        child: ElevatedButton(
                          onPressed: _handleDecline,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFFF5F5DC),
                            foregroundColor: const Color(0xFFFF6B35),
                            side: const BorderSide(color: Color(0xFFFF6B35)),
                            padding: const EdgeInsets.symmetric(vertical: 15),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(8),
                            ),
                          ),
                          child: Text(
                            'Refuser',
                            style: GoogleFonts.poppins(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: ElevatedButton(
                          onPressed: accepted ? _handleAccept : null,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: accepted
                                ? const Color(0xFFFF6B35)
                                : const Color(0xFFCCCCCC),
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(vertical: 15),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(8),
                            ),
                          ),
                          child: Text(
                            'Accepter',
                            style: GoogleFonts.poppins(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSection(String title, String content) {
    return Container(
      margin: const EdgeInsets.only(bottom: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: GoogleFonts.poppins(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: const Color(0xFF2F2F2F),
            ),
          ),
          const SizedBox(height: 10),
          Text(
            content,
            style: GoogleFonts.poppins(
              fontSize: 14,
              color: const Color(0xFF666666),
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }
}
```

### Visitor Landing Page
```dart
// lib/components/visitor_landing.dart
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class VisitorLanding extends StatelessWidget {
  final VoidCallback onLogin;
  final VoidCallback onRegister;
  final VoidCallback onBrowseProducts;

  const VisitorLanding({
    Key? key,
    required this.onLogin,
    required this.onRegister,
    required this.onBrowseProducts,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final featuredProducts = [
      {
        'name': 'Téléphone Samsung',
        'price': '45,000 FCFA',
        'image': 'assets/images/product1.jpg',
      },
      {
        'name': 'Sac à Main Africain',
        'price': '15,000 FCFA',
        'image': 'assets/images/product2.jpg',
      },
      {
        'name': 'Chaussures Confortables',
        'price': '25,000 FCFA',
        'image': 'assets/images/product3.jpg',
      },
    ];

    return Scaffold(
      body: SingleChildScrollView(
        child: Column(
          children: [
            // Header with gradient
            Container(
              padding: const EdgeInsets.fromLTRB(20, 60, 20, 40),
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [
                    Color(0xFFFF6B35),
                    Color(0xFFFFD23F),
                  ],
                ),
              ),
              child: Column(
                children: [
                  Image.asset(
                    'assets/images/african-welcome.png',
                    width: 120,
                    height: 120,
                  ),
                  const SizedBox(height: 20),
                  Text(
                    'Bienvenue sur Vidé-Grenier Kamer',
                    style: GoogleFonts.poppins(
                      fontSize: 28,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 10),
                  Text(
                    'Le marché africain numérique où vous trouvez tout ce dont vous avez besoin',
                    style: GoogleFonts.poppins(
                      fontSize: 16,
                      color: Colors.white,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),

            // Content
            Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Featured Products Section
                  Text(
                    'Produits Vedettes',
                    style: GoogleFonts.poppins(
                      fontSize: 22,
                      fontWeight: FontWeight.bold,
                      color: const Color(0xFF2F2F2F),
                    ),
                  ),
                  const SizedBox(height: 5),
                  Text(
                    'Découvrez nos meilleures offres du moment',
                    style: GoogleFonts.poppins(
                      fontSize: 14,
                      color: const Color(0xFF666666),
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Products horizontal scroll
                  SizedBox(
                    height: 200,
                    child: ListView.builder(
                      scrollDirection: Axis.horizontal,
                      itemCount: featuredProducts.length,
                      itemBuilder: (context, index) {
                        final product = featuredProducts[index];
                        return Container(
                          width: 160,
                          margin: const EdgeInsets.only(right: 15),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(12),
                            boxShadow: [
                              BoxShadow(
                                color: Colors.black.withOpacity(0.1),
                                blurRadius: 4,
                                offset: const Offset(0, 2),
                              ),
                            ],
                          ),
                          child: Column(
                            children: [
                              ClipRRect(
                                borderRadius: const BorderRadius.vertical(
                                  top: Radius.circular(12),
                                ),
                                child: Image.asset(
                                  product['image']!,
                                  width: double.infinity,
                                  height: 120,
                                  fit: BoxFit.cover,
                                ),
                              ),
                              Padding(
                                padding: const EdgeInsets.all(10),
                                child: Column(
                                  children: [
                                    Text(
                                      product['name']!,
                                      style: GoogleFonts.poppins(
                                        fontSize: 14,
                                        fontWeight: FontWeight.bold,
                                        color: const Color(0xFF2F2F2F),
                                      ),
                                      textAlign: TextAlign.center,
                                    ),
                                    const SizedBox(height: 5),
                                    Text(
                                      product['price']!,
                                      style: GoogleFonts.poppins(
                                        fontSize: 16,
                                        fontWeight: FontWeight.bold,
                                        color: const Color(0xFFFF6B35),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        );
                      },
                    ),
                  ),

                  const SizedBox(height: 30),

                  // Features Section
                  Text(
                    'Pourquoi Choisir VGK ?',
                    style: GoogleFonts.poppins(
                      fontSize: 22,
                      fontWeight: FontWeight.bold,
                      color: const Color(0xFF2F2F2F),
                    ),
                  ),
                  const SizedBox(height: 20),

                  _buildFeatureItem(
                    '🛡️',
                    'Transactions Sécurisées',
                    'Paiements sécurisés et protection des données',
                  ),
                  _buildFeatureItem(
                    '🚚',
                    'Livraison Rapide',
                    'Points de retrait dans toutes les villes',
                  ),
                  _buildFeatureItem(
                    '💬',
                    'Support Client',
                    'Assistance 24/7 en français et langues locales',
                  ),

                  const SizedBox(height: 30),

                  // Action Buttons
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: onBrowseProducts,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFFFF6B35),
                        padding: const EdgeInsets.symmetric(vertical: 15),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                      child: Text(
                        'Parcourir les Produits',
                        style: GoogleFonts.poppins(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 15),

                  Row(
                    children: [
                      Expanded(
                        child: ElevatedButton(
                          onPressed: onLogin,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFFF5F5DC),
                            foregroundColor: const Color(0xFFFF6B35),
                            side: const BorderSide(color: Color(0xFFFF6B35)),
                            padding: const EdgeInsets.symmetric(vertical: 15),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                          ),
                          child: Text(
                            'Se Connecter',
                            style: GoogleFonts.poppins(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: ElevatedButton(
                          onPressed: onRegister,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFF2E8B57),
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(vertical: 15),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                          ),
                          child: Text(
                            'S\'inscrire',
                            style: GoogleFonts.poppins(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFeatureItem(String icon, String title, String description) {
    return Container(
      margin: const EdgeInsets.only(bottom: 20),
      padding: const EdgeInsets.all(15),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 2,
            offset: const Offset(0, 1),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            width: 50,
            height: 50,
            decoration: const BoxDecoration(
              color: Color(0xFFFFD23F),
              shape: BoxShape.circle,
            ),
            child: Center(
              child: Text(
                icon,
                style: const TextStyle(fontSize: 24),
              ),
            ),
          ),
          const SizedBox(width: 15),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: GoogleFonts.poppins(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: const Color(0xFF2F2F2F),
                  ),
                ),
                const SizedBox(height: 5),
                Text(
                  description,
                  style: GoogleFonts.poppins(
                    fontSize: 14,
                    color: const Color(0xFF666666),
                    height: 1.4,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
```

### API Service
```dart
// lib/services/api_service.dart
import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  static const String baseUrl = 'http://localhost:8000/mobile/api';
  late Dio _dio;

  ApiService() {
    _dio = Dio(BaseOptions(
      baseUrl: baseUrl,
      headers: {'Content-Type': 'application/json'},
    ));

    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final prefs = await SharedPreferences.getInstance();
        final token = prefs.getString('authToken');
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
    ));
  }

  // Authentication
  Future<Map<String, dynamic>> login(String email, String password) async {
    try {
      final response = await _dio.post('/auth/login/', data: {
        'email': email,
        'password': password,
      });
      return response.data;
    } catch (e) {
      throw _handleError(e);
    }
  }

  Future<Map<String, dynamic>> register(Map<String, dynamic> userData) async {
    try {
      final response = await _dio.post('/auth/register/', data: userData);
      return response.data;
    } catch (e) {
      throw _handleError(e);
    }
  }

  // Products
  Future<Map<String, dynamic>> getProducts({Map<String, dynamic>? params}) async {
    try {
      final response = await _dio.get('/products/', queryParameters: params);
      return response.data;
    } catch (e) {
      throw _handleError(e);
    }
  }

  Future<Map<String, dynamic>> getProduct(String id) async {
    try {
      final response = await _dio.get('/products/$id/');
      return response.data;
    } catch (e) {
      throw _handleError(e);
    }
  }

  Future<Map<String, dynamic>> toggleFavorite(String productId) async {
    try {
      final response = await _dio.post('/products/$productId/favorite/');
      return response.data;
    } catch (e) {
      throw _handleError(e);
    }
  }

  // User Profile
  Future<Map<String, dynamic>> getUserProfile() async {
    try {
      final response = await _dio.get('/user/profile/');
      return response.data;
    } catch (e) {
      throw _handleError(e);
    }
  }

  // Search
  Future<Map<String, dynamic>> searchProducts(String query) async {
    try {
      final response = await _dio.get('/search/', queryParameters: {'q': query});
      return response.data;
    } catch (e) {
      throw _handleError(e);
    }
  }

  Exception _handleError(dynamic error) {
    if (error is DioException) {
      if (error.response?.statusCode == 401) {
        return Exception('Authentication failed');
      } else if (error.response?.statusCode == 400) {
        return Exception('Invalid request');
      } else if (error.response?.statusCode == 500) {
        return Exception('Server error');
      }
    }
    return Exception('Network error');
  }
}
```

### Authentication Provider
```dart
// lib/providers/auth_provider.dart
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/api_service.dart';

class AuthProvider with ChangeNotifier {
  final ApiService _apiService = ApiService();
  
  Map<String, dynamic>? _user;
  String? _token;
  bool _isLoading = false;

  Map<String, dynamic>? get user => _user;
  String? get token => _token;
  bool get isLoading => _isLoading;
  bool get isAuthenticated => _token != null;

  Future<void> loadStoredAuth() async {
    _isLoading = true;
    notifyListeners();

    try {
      final prefs = await SharedPreferences.getInstance();
      final storedToken = prefs.getString('authToken');
      final storedUser = prefs.getString('user');

      if (storedToken != null && storedUser != null) {
        _token = storedToken;
        _user = json.decode(storedUser);
      }
    } catch (e) {
      print('Error loading stored auth: $e');
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> login(String email, String password) async {
    _isLoading = true;
    notifyListeners();

    try {
      final response = await _apiService.login(email, password);
      
      _token = response['token'];
      _user = response['user'];

      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('authToken', _token!);
      await prefs.setString('user', json.encode(_user));
      
    } catch (e) {
      rethrow;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> register(Map<String, dynamic> userData) async {
    _isLoading = true;
    notifyListeners();

    try {
      final response = await _apiService.register(userData);
      
      _token = response['token'];
      _user = response['user'];

      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('authToken', _token!);
      await prefs.setString('user', json.encode(_user));
      
    } catch (e) {
      rethrow;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> logout() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove('authToken');
      await prefs.remove('user');
      
      _token = null;
      _user = null;
      
    } catch (e) {
      print('Error during logout: $e');
    } finally {
      notifyListeners();
    }
  }
}
```

## Mobile App Features

### App Launch Flow
1. **Splash Screen** (3-5 seconds)
   - African-themed logo animation with gradient colors
   - App name "Vidé-Grenier Kamer" with African typography
   - Tagline "Le Marché Africain Numérique"
   - Loading animation with African-inspired dots

2. **Terms & Conditions** (First time only)
   - African-themed design with warm colors
   - Clear, readable terms in French
   - Checkbox for acceptance
   - Accept/Decline buttons with confirmation dialogs

3. **Visitor Landing Page**
   - Welcome message with African hospitality
   - Featured products showcase with horizontal scroll
   - "Pourquoi Choisir VGK?" section with features
   - Three main action buttons:
     - "Parcourir les Produits" (Browse Products)
     - "Se Connecter" (Login)
     - "S'inscrire" (Register)

### Core Features for All User Types

1. **Product Browsing**
   - View product listings
   - Filter by category, price, condition
   - Search products
   - View product details

2. **User Authentication**
   - Login/Register
   - Profile management
   - Password reset

3. **Favorites**
   - Add/remove favorites
   - View favorite products

### Client-Specific Features

1. **Product Management**
   - Create new products
   - Edit existing products
   - Delete products
   - View my products

2. **Order Management**
   - View purchase history
   - View sales history
   - Track order status

3. **Chat System**
   - Chat with buyers/sellers
   - Send/receive messages
   - Image sharing

4. **Wallet & Payments**
   - View wallet balance
   - Transaction history
   - Add funds

5. **Loyalty Program**
   - View loyalty points
   - Loyalty level status
   - Rewards

### Admin-Specific Features

1. **Dashboard**
   - Analytics overview
   - User statistics
   - Revenue reports

2. **User Management**
   - View all users
   - Manage user accounts
   - User verification

3. **Product Moderation**
   - Approve/reject products
   - Manage categories
   - Content moderation

4. **System Management**
   - Pickup points management
   - Payment settings
   - System configuration

## Error Handling

### Common HTTP Status Codes

- `200` - Success
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (authentication required)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `500` - Server Error

### Error Response Format
```json
{
  "error": "Error message description",
  "details": {
    "field_name": ["Specific error for this field"]
  }
}
```

## African Theme Assets & Resources

### Required Assets
```
assets/
├── images/
│   ├── african-logo.png          # App logo with African design
│   ├── african-welcome.png       # Welcome illustration
│   ├── product1.jpg              # Sample product images
│   ├── product2.jpg
│   ├── product3.jpg
│   └── patterns/
│       ├── african-pattern-1.png # Geometric patterns
│       ├── african-pattern-2.png
│       └── tribal-motif.png
├── icons/
│   ├── african-market.svg        # Market icon
│   ├── african-phone.svg         # Phone icon
│   ├── african-bag.svg           # Shopping bag
│   └── african-payment.svg       # Payment icon
└── fonts/
    ├── Poppins-Bold.ttf          # Primary font
    ├── Poppins-Regular.ttf
    └── Poppins-Medium.ttf
```

### Design Resources
- **Color Palette**: African-inspired colors (orange, yellow, green, brown)
- **Typography**: Poppins font family for modern African feel
- **Patterns**: Geometric African patterns and tribal motifs
- **Icons**: Hand-drawn style with organic shapes
- **Images**: African marketplace scenes and local products

### Cultural Considerations
- **Language**: French primary, local languages support
- **Currency**: FCFA (Franc CFA)
- **Addresses**: Cameroonian city formats
- **Payment**: Local payment methods (Mobile Money, etc.)
- **Cultural Sensitivity**: Respect local customs and traditions

## Security Considerations

1. **HTTPS Only** - Use HTTPS in production
2. **Token Storage** - Store tokens securely (Keychain for iOS, Keystore for Android)
3. **Input Validation** - Validate all user inputs
4. **Rate Limiting** - Implement rate limiting for API calls
5. **Token Refresh** - Implement automatic token refresh

## App Navigation Flow

### Complete App Flow
```
Splash Screen (3-5s)
    ↓
Terms & Conditions (First time only)
    ↓
Visitor Landing Page
    ↓
┌─────────────────┬─────────────────┬─────────────────┐
│   Browse        │    Login        │   Register      │
│   Products      │                 │                 │
│   (Visitor)     │                 │                 │
└─────────────────┴─────────────────┴─────────────────┘
    ↓                    ↓                    ↓
Product List        Login Screen        Register Screen
    ↓                    ↓                    ↓
Product Detail      Dashboard           Dashboard
    ↓                    ↓                    ↓
[Visitor Mode]      [Client Mode]       [Client Mode]
```

### Navigation States
1. **Visitor State** (No Authentication)
   - Browse products
   - View product details
   - Search functionality
   - Access to login/register

2. **Client State** (Authenticated)
   - All visitor features
   - Personal dashboard
   - Product management
   - Order management
   - Chat system
   - Wallet & payments

3. **Admin State** (Admin Authentication)
   - All client features
   - Admin dashboard
   - User management
   - System configuration

## Testing

### API Testing
```bash
# Test health endpoint
curl http://localhost:8000/mobile/api/health/

# Test login
curl -X POST http://localhost:8000/mobile/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'
```

### Mobile App Testing
- Unit tests for API service
- Integration tests for authentication
- UI tests for critical flows
- Performance testing

## Deployment

### Backend Deployment
1. Deploy Django backend to production server
2. Configure CORS for mobile app domains
3. Set up SSL certificates
4. Configure environment variables

### Mobile App Deployment
1. **React Native**
   - Build APK: `cd android && ./gradlew assembleRelease`
   - Build iOS: Archive in Xcode
   - Submit to app stores

2. **Flutter**
   - Build APK: `flutter build apk --release`
   - Build iOS: `flutter build ios --release`
   - Submit to app stores

## Performance Optimization

1. **Image Optimization**
   - Use WebP format
   - Implement lazy loading
   - Cache images locally

2. **API Optimization**
   - Implement pagination
   - Use caching strategies
   - Optimize database queries

3. **App Performance**
   - Minimize bundle size
   - Implement code splitting
   - Use performance monitoring

## Monitoring & Analytics

1. **Backend Monitoring**
   - API response times
   - Error rates
   - User activity

2. **Mobile App Analytics**
   - User engagement
   - Feature usage
   - Crash reporting

## Support & Maintenance

1. **Documentation**
   - Keep API documentation updated
   - Maintain code comments
   - Update deployment guides

2. **Versioning**
   - API versioning strategy
   - Mobile app versioning
   - Backward compatibility

3. **Updates**
   - Regular security updates
   - Feature updates
   - Bug fixes

## Conclusion

This mobile development guide provides a comprehensive framework for building React Native and Flutter applications that integrate with the Vidé-Grenier Kamer Django backend. The API is designed to support all user types (Admin, Client, Visitor) with appropriate authentication and authorization mechanisms.

For additional support or questions, refer to the main project documentation or contact the development team. 