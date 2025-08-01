# React Native Integration Guide

This guide provides comprehensive instructions for integrating the mobile API with a React Native application, including setup, authentication, state management, and UI implementation.

## Project Setup

### 1. Create React Native Project
```bash
# Create new React Native project with TypeScript
npx react-native@latest init VidéGrenierMobile --template react-native-template-typescript

# Navigate to project
cd VidéGrenierMobile

# Install dependencies
npm install
```

### 2. Install Required Dependencies
```bash
# Navigation
npm install @react-navigation/native @react-navigation/stack @react-navigation/bottom-tabs
npm install react-native-screens react-native-safe-area-context

# State Management
npm install @reduxjs/toolkit react-redux
npm install redux-persist

# HTTP Client
npm install axios

# Storage
npm install @react-native-async-storage/async-storage
npm install react-native-keychain

# UI Components
npm install react-native-elements
npm install react-native-vector-icons

# Image Handling
npm install react-native-image-picker
npm install react-native-fast-image

# Forms
npm install react-hook-form
npm install yup @hookform/resolvers

# Notifications
npm install @react-native-firebase/messaging

# QR Code
npm install react-native-qrcode-scanner
npm install react-native-camera

# Date/Time
npm install moment

# Validation
npm install react-native-phone-number-input
```

### 3. Configure Environment
```bash
# Create environment files
touch .env.development
touch .env.production
```

```env
# .env.development
API_BASE_URL=http://localhost:8000/mobile/api
API_TIMEOUT=30000
ENVIRONMENT=development

# .env.production
API_BASE_URL=https://api.videgrenier-kamer.com/mobile/api
API_TIMEOUT=30000
ENVIRONMENT=production
```

## Project Structure

```
src/
├── api/
│   ├── client.ts
│   ├── auth.ts
│   ├── products.ts
│   ├── orders.ts
│   ├── user.ts
│   └── visitor.ts
├── components/
│   ├── common/
│   │   ├── AfricanButton.tsx
│   │   ├── AfricanCard.tsx
│   │   ├── LoadingSpinner.tsx
│   │   └── ErrorMessage.tsx
│   ├── forms/
│   │   ├── LoginForm.tsx
│   │   ├── RegisterForm.tsx
│   │   └── ProductForm.tsx
│   └── screens/
│       ├── SplashScreen.tsx
│       ├── TermsConditions.tsx
│       └── VisitorLanding.tsx
├── navigation/
│   ├── AppNavigator.tsx
│   ├── AuthNavigator.tsx
│   └── MainNavigator.tsx
├── store/
│   ├── index.ts
│   ├── authSlice.ts
│   ├── productSlice.ts
│   └── cartSlice.ts
├── theme/
│   ├── index.ts
│   ├── colors.ts
│   ├── typography.ts
│   └── spacing.ts
├── utils/
│   ├── storage.ts
│   ├── validation.ts
│   └── helpers.ts
└── types/
    ├── api.ts
    ├── auth.ts
    └── product.ts
```

## API Client Setup

### 1. API Client Configuration
```typescript
// src/api/client.ts
import axios, { AxiosInstance, AxiosResponse } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_BASE_URL, API_TIMEOUT } from '@env';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      async (config) => {
        const token = await AsyncStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response: AxiosResponse) => response,
      async (error) => {
        if (error.response?.status === 401) {
          // Token expired, try to refresh
          const refreshed = await this.refreshToken();
          if (refreshed) {
            // Retry original request
            return this.client.request(error.config);
          }
          // Redirect to login
          this.handleLogout();
        }
        return Promise.reject(error);
      }
    );
  }

  private async refreshToken(): Promise<boolean> {
    try {
      const refreshToken = await AsyncStorage.getItem('refresh_token');
      if (!refreshToken) return false;

      const response = await this.client.post('/auth/refresh/', {
        refresh_token: refreshToken,
      });

      if (response.data.success) {
        await AsyncStorage.setItem('access_token', response.data.access_token);
        return true;
      }
      return false;
    } catch (error) {
      return false;
    }
  }

  private async handleLogout() {
    await AsyncStorage.multiRemove(['access_token', 'refresh_token', 'user']);
    // Navigate to login screen
  }

  // Generic methods
  async get<T>(url: string, params?: any): Promise<T> {
    const response = await this.client.get(url, { params });
    return response.data;
  }

  async post<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.post(url, data);
    return response.data;
  }

  async put<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.put(url, data);
    return response.data;
  }

  async delete<T>(url: string): Promise<T> {
    const response = await this.client.delete(url);
    return response.data;
  }
}

export const apiClient = new ApiClient();
```

### 2. Authentication API
```typescript
// src/api/auth.ts
import { apiClient } from './client';
import { LoginRequest, RegisterRequest, AuthResponse, User } from '../types/auth';

export const authApi = {
  // Login
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    return apiClient.post<AuthResponse>('/auth/login/', credentials);
  },

  // Verify 2FA
  async verify2FA(email: string, code: string): Promise<AuthResponse> {
    return apiClient.post<AuthResponse>('/auth/verify_2fa/', { email, code });
  },

  // Register
  async register(userData: RegisterRequest): Promise<AuthResponse> {
    return apiClient.post<AuthResponse>('/auth/register/', userData);
  },

  // Verify phone
  async verifyPhone(userId: string, code: string): Promise<AuthResponse> {
    return apiClient.post<AuthResponse>('/auth/verify_phone/', { user_id: userId, code });
  },

  // Google OAuth
  async googleOAuth(accessToken: string): Promise<AuthResponse> {
    return apiClient.post<AuthResponse>('/auth/google_oauth/', { access_token: accessToken });
  },

  // Setup 2FA
  async setup2FA(enable: boolean): Promise<{ success: boolean; message: string }> {
    return apiClient.post('/user/setup_2fa/', { enable_2fa: enable });
  },
};
```

### 3. Products API
```typescript
// src/api/products.ts
import { apiClient } from './client';
import { Product, ProductListResponse, ProductFilters } from '../types/product';

export const productsApi = {
  // Get products with filters
  async getProducts(filters?: ProductFilters): Promise<ProductListResponse> {
    return apiClient.get<ProductListResponse>('/products/', filters);
  },

  // Get product details
  async getProduct(id: string): Promise<{ success: boolean; product: Product }> {
    return apiClient.get(`/products/${id}/`);
  },

  // Toggle favorite
  async toggleFavorite(productId: string): Promise<{ success: boolean; is_favorited: boolean }> {
    return apiClient.post(`/products/${productId}/favorite/`);
  },

  // Get trending products
  async getTrending(): Promise<{ success: boolean; products: Product[] }> {
    return apiClient.get('/products/trending/');
  },

  // Get recommended products
  async getRecommended(): Promise<{ success: boolean; products: Product[] }> {
    return apiClient.get('/products/recommended/');
  },

  // Create product
  async createProduct(productData: Partial<Product>): Promise<{ success: boolean; product: Product }> {
    return apiClient.post('/products/', productData);
  },

  // Update product
  async updateProduct(id: string, productData: Partial<Product>): Promise<{ success: boolean; product: Product }> {
    return apiClient.put(`/products/${id}/`, productData);
  },

  // Delete product
  async deleteProduct(id: string): Promise<{ success: boolean }> {
    return apiClient.delete(`/products/${id}/`);
  },
};
```

## State Management with Redux Toolkit

### 1. Store Configuration
```typescript
// src/store/index.ts
import { configureStore, combineReducers } from '@reduxjs/toolkit';
import { persistStore, persistReducer } from 'redux-persist';
import AsyncStorage from '@react-native-async-storage/async-storage';
import authReducer from './authSlice';
import productReducer from './productSlice';
import cartReducer from './cartSlice';

const persistConfig = {
  key: 'root',
  storage: AsyncStorage,
  whitelist: ['auth', 'cart'], // Only persist auth and cart
};

const rootReducer = combineReducers({
  auth: authReducer,
  products: productReducer,
  cart: cartReducer,
});

const persistedReducer = persistReducer(persistConfig, rootReducer);

export const store = configureStore({
  reducer: persistedReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
    }),
});

export const persistor = persistStore(store);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
```

### 2. Auth Slice
```typescript
// src/store/authSlice.ts
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { authApi } from '../api/auth';
import { LoginRequest, RegisterRequest, User } from '../types/auth';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface AuthState {
  user: User | null;
  tokens: {
    access_token: string | null;
    refresh_token: string | null;
  } | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  requires2FA: boolean;
  requiresPhoneVerification: boolean;
}

const initialState: AuthState = {
  user: null,
  tokens: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
  requires2FA: false,
  requiresPhoneVerification: false,
};

// Async thunks
export const login = createAsyncThunk(
  'auth/login',
  async (credentials: LoginRequest, { rejectWithValue }) => {
    try {
      const response = await authApi.login(credentials);
      
      if (response.requires_2fa) {
        return { requires2FA: true, message: response.message };
      }

      // Save tokens
      await AsyncStorage.setItem('access_token', response.tokens.access_token);
      await AsyncStorage.setItem('refresh_token', response.tokens.refresh_token);
      await AsyncStorage.setItem('user', JSON.stringify(response.user));

      return response;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error || 'Login failed');
    }
  }
);

export const verify2FA = createAsyncThunk(
  'auth/verify2FA',
  async ({ email, code }: { email: string; code: string }, { rejectWithValue }) => {
    try {
      const response = await authApi.verify2FA(email, code);
      
      // Save tokens
      await AsyncStorage.setItem('access_token', response.tokens.access_token);
      await AsyncStorage.setItem('refresh_token', response.tokens.refresh_token);
      await AsyncStorage.setItem('user', JSON.stringify(response.user));

      return response;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error || '2FA verification failed');
    }
  }
);

export const register = createAsyncThunk(
  'auth/register',
  async (userData: RegisterRequest, { rejectWithValue }) => {
    try {
      const response = await authApi.register(userData);
      
      if (response.requires_phone_verification) {
        return { requiresPhoneVerification: true, userId: response.user_id };
      }

      return response;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error || 'Registration failed');
    }
  }
);

export const logout = createAsyncThunk(
  'auth/logout',
  async () => {
    await AsyncStorage.multiRemove(['access_token', 'refresh_token', 'user']);
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    setRequires2FA: (state, action: PayloadAction<boolean>) => {
      state.requires2FA = action.payload;
    },
    setRequiresPhoneVerification: (state, action: PayloadAction<boolean>) => {
      state.requiresPhoneVerification = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      // Login
      .addCase(login.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.isLoading = false;
        if (action.payload.requires2FA) {
          state.requires2FA = true;
        } else {
          state.user = action.payload.user;
          state.tokens = action.payload.tokens;
          state.isAuthenticated = true;
        }
      })
      .addCase(login.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Verify 2FA
      .addCase(verify2FA.fulfilled, (state, action) => {
        state.user = action.payload.user;
        state.tokens = action.payload.tokens;
        state.isAuthenticated = true;
        state.requires2FA = false;
      })
      // Register
      .addCase(register.fulfilled, (state, action) => {
        if (action.payload.requiresPhoneVerification) {
          state.requiresPhoneVerification = true;
        } else {
          state.user = action.payload.user;
          state.tokens = action.payload.tokens;
          state.isAuthenticated = true;
        }
      })
      // Logout
      .addCase(logout.fulfilled, (state) => {
        state.user = null;
        state.tokens = null;
        state.isAuthenticated = false;
        state.requires2FA = false;
        state.requiresPhoneVerification = false;
      });
  },
});

export const { clearError, setRequires2FA, setRequiresPhoneVerification } = authSlice.actions;
export default authSlice.reducer;
```

### 3. Product Slice
```typescript
// src/store/productSlice.ts
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { productsApi } from '../api/products';
import { Product, ProductFilters } from '../types/product';

interface ProductState {
  products: Product[];
  currentProduct: Product | null;
  favorites: string[];
  isLoading: boolean;
  error: string | null;
  hasMore: boolean;
  currentPage: number;
}

const initialState: ProductState = {
  products: [],
  currentProduct: null,
  favorites: [],
  isLoading: false,
  error: null,
  hasMore: true,
  currentPage: 1,
};

export const fetchProducts = createAsyncThunk(
  'products/fetchProducts',
  async (filters?: ProductFilters, { getState, rejectWithValue }) => {
    try {
      const state = getState() as any;
      const page = filters?.page || state.products.currentPage;
      
      const response = await productsApi.getProducts({ ...filters, page });
      
      return {
        products: response.results,
        hasMore: !!response.next,
        currentPage: page,
        isRefresh: page === 1,
      };
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error || 'Failed to fetch products');
    }
  }
);

export const fetchProductDetails = createAsyncThunk(
  'products/fetchProductDetails',
  async (productId: string, { rejectWithValue }) => {
    try {
      const response = await productsApi.getProduct(productId);
      return response.product;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error || 'Failed to fetch product details');
    }
  }
);

export const toggleFavorite = createAsyncThunk(
  'products/toggleFavorite',
  async (productId: string, { getState, rejectWithValue }) => {
    try {
      const response = await productsApi.toggleFavorite(productId);
      return { productId, isFavorited: response.is_favorited };
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error || 'Failed to toggle favorite');
    }
  }
);

const productSlice = createSlice({
  name: 'products',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    clearProducts: (state) => {
      state.products = [];
      state.currentPage = 1;
      state.hasMore = true;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch products
      .addCase(fetchProducts.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchProducts.fulfilled, (state, action) => {
        state.isLoading = false;
        if (action.payload.isRefresh) {
          state.products = action.payload.products;
        } else {
          state.products = [...state.products, ...action.payload.products];
        }
        state.hasMore = action.payload.hasMore;
        state.currentPage = action.payload.currentPage;
      })
      .addCase(fetchProducts.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Fetch product details
      .addCase(fetchProductDetails.fulfilled, (state, action) => {
        state.currentProduct = action.payload;
      })
      // Toggle favorite
      .addCase(toggleFavorite.fulfilled, (state, action) => {
        const { productId, isFavorited } = action.payload;
        if (isFavorited) {
          state.favorites.push(productId);
        } else {
          state.favorites = state.favorites.filter(id => id !== productId);
        }
      });
  },
});

export const { clearError, clearProducts } = productSlice.actions;
export default productSlice.reducer;
```

## Navigation Setup

### 1. App Navigator
```typescript
// src/navigation/AppNavigator.tsx
import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { useSelector } from 'react-redux';
import { RootState } from '../store';
import AuthNavigator from './AuthNavigator';
import MainNavigator from './MainNavigator';
import SplashScreen from '../components/screens/SplashScreen';

const AppNavigator: React.FC = () => {
  const { isAuthenticated, isLoading } = useSelector((state: RootState) => state.auth);

  if (isLoading) {
    return <SplashScreen />;
  }

  return (
    <NavigationContainer>
      {isAuthenticated ? <MainNavigator /> : <AuthNavigator />}
    </NavigationContainer>
  );
};

export default AppNavigator;
```

### 2. Auth Navigator
```typescript
// src/navigation/AuthNavigator.tsx
import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import { useSelector } from 'react-redux';
import { RootState } from '../store';
import TermsConditionsScreen from '../components/screens/TermsConditionsScreen';
import VisitorLandingScreen from '../components/screens/VisitorLandingScreen';
import LoginScreen from '../components/screens/LoginScreen';
import RegisterScreen from '../components/screens/RegisterScreen';
import TwoFactorScreen from '../components/screens/TwoFactorScreen';
import PhoneVerificationScreen from '../components/screens/PhoneVerificationScreen';

const Stack = createStackNavigator();

const AuthNavigator: React.FC = () => {
  const { requires2FA, requiresPhoneVerification } = useSelector(
    (state: RootState) => state.auth
  );

  return (
    <Stack.Navigator
      initialRouteName="TermsConditions"
      screenOptions={{
        headerShown: false,
      }}
    >
      <Stack.Screen name="TermsConditions" component={TermsConditionsScreen} />
      <Stack.Screen name="VisitorLanding" component={VisitorLandingScreen} />
      <Stack.Screen name="Login" component={LoginScreen} />
      <Stack.Screen name="Register" component={RegisterScreen} />
      {requires2FA && <Stack.Screen name="TwoFactor" component={TwoFactorScreen} />}
      {requiresPhoneVerification && (
        <Stack.Screen name="PhoneVerification" component={PhoneVerificationScreen} />
      )}
    </Stack.Navigator>
  );
};

export default AuthNavigator;
```

### 3. Main Navigator
```typescript
// src/navigation/MainNavigator.tsx
import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { useSelector } from 'react-redux';
import { RootState } from '../store';
import HomeScreen from '../components/screens/HomeScreen';
import SearchScreen from '../components/screens/SearchScreen';
import CartScreen from '../components/screens/CartScreen';
import ProfileScreen from '../components/screens/ProfileScreen';
import AdminScreen from '../components/screens/AdminScreen';
import Icon from 'react-native-vector-icons/MaterialIcons';

const Tab = createBottomTabNavigator();

const MainNavigator: React.FC = () => {
  const { user } = useSelector((state: RootState) => state.auth);
  const isAdmin = user?.user_type === 'ADMIN';

  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: string;

          switch (route.name) {
            case 'Home':
              iconName = 'home';
              break;
            case 'Search':
              iconName = 'search';
              break;
            case 'Cart':
              iconName = 'shopping-cart';
              break;
            case 'Profile':
              iconName = 'person';
              break;
            case 'Admin':
              iconName = 'admin-panel-settings';
              break;
            default:
              iconName = 'help';
          }

          return <Icon name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#FF6B35',
        tabBarInactiveTintColor: 'gray',
      })}
    >
      <Tab.Screen name="Home" component={HomeScreen} />
      <Tab.Screen name="Search" component={SearchScreen} />
      <Tab.Screen name="Cart" component={CartScreen} />
      <Tab.Screen name="Profile" component={ProfileScreen} />
      {isAdmin && <Tab.Screen name="Admin" component={AdminScreen} />}
    </Tab.Navigator>
  );
};

export default MainNavigator;
```

## Theme Configuration

### 1. Colors
```typescript
// src/theme/colors.ts
export const colors = {
  // Primary Colors - African Heritage
  primaryOrange: '#FF6B35',      // African Sunset
  primaryYellow: '#FFD23F',      // African Gold
  primaryGreen: '#2E8B57',       // African Forest
  primaryBrown: '#8B4513',       // African Soil
  primaryRed: '#DC143C',         // African Ruby

  // Secondary Colors
  secondaryOrange: '#FF8C42',    // Lighter Orange
  secondaryYellow: '#FFE066',    // Lighter Yellow
  secondaryGreen: '#4CAF50',     // Lighter Green
  secondaryBrown: '#A0522D',     // Lighter Brown
  secondaryRed: '#E74C3C',       // Lighter Red

  // Accent Colors
  accentPurple: '#9B59B6',       // African Violet
  accentBlue: '#3498DB',         // African Sky
  accentTeal: '#1ABC9C',         // African Turquoise
  accentPink: '#E91E63',         // African Rose
  accentGold: '#F39C12',         // African Gold

  // Neutral Colors
  white: '#FFFFFF',
  black: '#000000',
  gray: '#808080',
  lightGray: '#F5F5F5',
  darkGray: '#333333',

  // Status Colors
  success: '#27AE60',
  warning: '#F39C12',
  error: '#E74C3C',
  info: '#3498DB',

  // Background Colors
  background: '#FAFAFA',
  surface: '#FFFFFF',
  card: '#FFFFFF',
  border: '#E0E0E0',
};
```

### 2. Typography
```typescript
// src/theme/typography.ts
import { Platform } from 'react-native';

export const fonts = {
  // Font Families
  primary: Platform.select({
    ios: 'Poppins-Regular',
    android: 'Poppins-Regular',
  }),
  primaryBold: Platform.select({
    ios: 'Poppins-Bold',
    android: 'Poppins-Bold',
  }),
  primaryMedium: Platform.select({
    ios: 'Poppins-Medium',
    android: 'Poppins-Medium',
  }),
  secondary: Platform.select({
    ios: 'Roboto-Regular',
    android: 'Roboto-Regular',
  }),
  accent: Platform.select({
    ios: 'PlayfairDisplay-Regular',
    android: 'PlayfairDisplay-Regular',
  }),
};

export const fontSizes = {
  // Font Sizes
  xs: 12,
  sm: 14,
  base: 16,
  lg: 18,
  xl: 20,
  '2xl': 24,
  '3xl': 30,
  '4xl': 36,
  '5xl': 48,
  '6xl': 60,
};

export const fontWeights = {
  // Font Weights
  light: '300',
  normal: '400',
  medium: '500',
  semibold: '600',
  bold: '700',
  extrabold: '800',
};

export const lineHeights = {
  // Line Heights
  tight: 1.25,
  normal: 1.5,
  relaxed: 1.75,
};
```

### 3. Spacing
```typescript
// src/theme/spacing.ts
export const spacing = {
  // Spacing Scale
  xs: 4,
  sm: 8,
  base: 16,
  lg: 24,
  xl: 32,
  '2xl': 48,
  '3xl': 64,
  '4xl': 96,
  '5xl': 128,
};

export const borderRadius = {
  // Border Radius
  none: 0,
  sm: 4,
  base: 8,
  lg: 12,
  xl: 16,
  '2xl': 24,
  full: 9999,
};

export const shadows = {
  // Shadows
  sm: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  base: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  lg: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 6,
  },
};
```

## Component Examples

### 1. African Button Component
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
import { colors, fonts, fontSizes, fontWeights, spacing, borderRadius } from '../../theme';

interface AfricanButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  disabled?: boolean;
  style?: ViewStyle;
  textStyle?: TextStyle;
}

const AfricanButton: React.FC<AfricanButtonProps> = ({
  title,
  onPress,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  style,
  textStyle,
}) => {
  const buttonStyle = [
    styles.base,
    styles[variant],
    styles[size],
    disabled && styles.disabled,
    style,
  ];

  const textStyleComputed = [
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
          color={variant === 'primary' ? colors.white : colors.primaryOrange}
          size="small"
        />
      ) : (
        <Text style={textStyleComputed}>{title}</Text>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  base: {
    borderRadius: borderRadius.lg,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
  },
  // Variants
  primary: {
    backgroundColor: colors.primaryOrange,
  },
  secondary: {
    backgroundColor: colors.primaryYellow,
  },
  outline: {
    backgroundColor: 'transparent',
    borderWidth: 2,
    borderColor: colors.primaryOrange,
  },
  ghost: {
    backgroundColor: 'transparent',
  },
  // Sizes
  sm: {
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.base,
    minHeight: 36,
  },
  md: {
    paddingVertical: spacing.base,
    paddingHorizontal: spacing.lg,
    minHeight: 48,
  },
  lg: {
    paddingVertical: spacing.lg,
    paddingHorizontal: spacing.xl,
    minHeight: 56,
  },
  // Text styles
  text: {
    fontFamily: fonts.primaryMedium,
    textAlign: 'center',
  },
  primaryText: {
    color: colors.white,
  },
  secondaryText: {
    color: colors.black,
  },
  outlineText: {
    color: colors.primaryOrange,
  },
  ghostText: {
    color: colors.primaryOrange,
  },
  smText: {
    fontSize: fontSizes.sm,
  },
  mdText: {
    fontSize: fontSizes.base,
  },
  lgText: {
    fontSize: fontSizes.lg,
  },
  // States
  disabled: {
    opacity: 0.5,
  },
  disabledText: {
    opacity: 0.7,
  },
});

export default AfricanButton;
```

### 2. Product Card Component
```typescript
// src/components/common/ProductCard.tsx
import React from 'react';
import {
  View,
  Text,
  Image,
  StyleSheet,
  TouchableOpacity,
  Dimensions,
} from 'react-native';
import { colors, fonts, fontSizes, fontWeights, spacing, borderRadius, shadows } from '../../theme';
import { Product } from '../../types/product';
import Icon from 'react-native-vector-icons/MaterialIcons';

interface ProductCardProps {
  product: Product;
  onPress: (product: Product) => void;
  onFavoritePress: (productId: string) => void;
  isFavorited: boolean;
}

const { width } = Dimensions.get('window');
const cardWidth = (width - spacing.base * 3) / 2;

const ProductCard: React.FC<ProductCardProps> = ({
  product,
  onPress,
  onFavoritePress,
  isFavorited,
}) => {
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'XAF',
    }).format(price);
  };

  return (
    <TouchableOpacity
      style={styles.container}
      onPress={() => onPress(product)}
      activeOpacity={0.8}
    >
      <View style={styles.imageContainer}>
        <Image
          source={{ uri: product.main_image || 'https://via.placeholder.com/200' }}
          style={styles.image}
          resizeMode="cover"
        />
        <TouchableOpacity
          style={styles.favoriteButton}
          onPress={() => onFavoritePress(product.id)}
        >
          <Icon
            name={isFavorited ? 'favorite' : 'favorite-border'}
            size={20}
            color={isFavorited ? colors.error : colors.white}
          />
        </TouchableOpacity>
        {product.is_negotiable && (
          <View style={styles.negotiableBadge}>
            <Text style={styles.negotiableText}>Négociable</Text>
          </View>
        )}
      </View>
      
      <View style={styles.content}>
        <Text style={styles.title} numberOfLines={2}>
          {product.title}
        </Text>
        <Text style={styles.price}>{formatPrice(product.price)}</Text>
        <View style={styles.meta}>
          <Text style={styles.condition}>{product.condition}</Text>
          <Text style={styles.city}>{product.city}</Text>
        </View>
        <View style={styles.stats}>
          <View style={styles.stat}>
            <Icon name="visibility" size={14} color={colors.gray} />
            <Text style={styles.statText}>{product.views_count}</Text>
          </View>
          <View style={styles.stat}>
            <Icon name="favorite" size={14} color={colors.gray} />
            <Text style={styles.statText}>{product.likes_count}</Text>
          </View>
        </View>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    width: cardWidth,
    backgroundColor: colors.white,
    borderRadius: borderRadius.lg,
    marginBottom: spacing.base,
    ...shadows.base,
  },
  imageContainer: {
    position: 'relative',
    height: cardWidth * 0.8,
  },
  image: {
    width: '100%',
    height: '100%',
    borderTopLeftRadius: borderRadius.lg,
    borderTopRightRadius: borderRadius.lg,
  },
  favoriteButton: {
    position: 'absolute',
    top: spacing.sm,
    right: spacing.sm,
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
    borderRadius: borderRadius.full,
    padding: spacing.xs,
  },
  negotiableBadge: {
    position: 'absolute',
    bottom: spacing.sm,
    left: spacing.sm,
    backgroundColor: colors.primaryGreen,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.sm,
  },
  negotiableText: {
    color: colors.white,
    fontSize: fontSizes.xs,
    fontFamily: fonts.primaryMedium,
  },
  content: {
    padding: spacing.base,
  },
  title: {
    fontSize: fontSizes.sm,
    fontFamily: fonts.primaryMedium,
    color: colors.black,
    marginBottom: spacing.xs,
    lineHeight: fontSizes.sm * 1.3,
  },
  price: {
    fontSize: fontSizes.lg,
    fontFamily: fonts.primaryBold,
    color: colors.primaryOrange,
    marginBottom: spacing.xs,
  },
  meta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: spacing.xs,
  },
  condition: {
    fontSize: fontSizes.xs,
    fontFamily: fonts.primary,
    color: colors.gray,
    backgroundColor: colors.lightGray,
    paddingHorizontal: spacing.xs,
    paddingVertical: 2,
    borderRadius: borderRadius.sm,
  },
  city: {
    fontSize: fontSizes.xs,
    fontFamily: fonts.primary,
    color: colors.gray,
  },
  stats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  stat: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statText: {
    fontSize: fontSizes.xs,
    fontFamily: fonts.primary,
    color: colors.gray,
    marginLeft: spacing.xs,
  },
});

export default ProductCard;
```

## App Entry Point

### 1. App.tsx
```typescript
// App.tsx
import React from 'react';
import { Provider } from 'react-redux';
import { PersistGate } from 'redux-persist/integration/react';
import { store, persistor } from './src/store';
import AppNavigator from './src/navigation/AppNavigator';
import { SafeAreaProvider } from 'react-native-safe-area-context';

const App: React.FC = () => {
  return (
    <Provider store={store}>
      <PersistGate loading={null} persistor={persistor}>
        <SafeAreaProvider>
          <AppNavigator />
        </SafeAreaProvider>
      </PersistGate>
    </Provider>
  );
};

export default App;
```

This integration guide provides a complete foundation for building a React Native app that communicates with the mobile API. The implementation includes proper state management, navigation, theming, and component architecture that follows React Native best practices. 