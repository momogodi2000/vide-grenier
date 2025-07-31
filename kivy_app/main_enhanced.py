"""
Enhanced Kivy Mobile App for Vidé-Grenier Kamer
Features offline mode, splash screen, and proper mobile configuration
"""

import kivy
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.webview import WebView
from kivy.uix.progressbar import ProgressBar
from kivy.core.window import Window
from kivy.utils import platform
from kivy.clock import Clock
from kivy.properties import StringProperty, BooleanProperty
from kivy.network.urlrequest import UrlRequest
from kivy.storage.jsonstore import JsonStore
import os
import json
import requests
from datetime import datetime, timedelta

kivy.require('2.2.1')

class SplashScreen(Screen):
    """Splash screen with loading animation"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Create splash layout
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        
        # App logo
        logo = Image(
            source='assets/logo.png',
            size_hint=(None, None),
            size=(200, 200),
            pos_hint={'center_x': 0.5}
        )
        layout.add_widget(logo)
        
        # App title
        title = Label(
            text='Vidé-Grenier Kamer',
            font_size='24sp',
            bold=True,
            color=(0.2, 0.6, 0.8, 1)
        )
        layout.add_widget(title)
        
        # Loading text
        self.loading_label = Label(
            text='Chargement...',
            font_size='16sp',
            color=(0.5, 0.5, 0.5, 1)
        )
        layout.add_widget(self.loading_label)
        
        # Progress bar
        self.progress = ProgressBar(max=100)
        layout.add_widget(self.progress)
        
        # Version info
        version_label = Label(
            text='Version 1.0.0',
            font_size='12sp',
            color=(0.7, 0.7, 0.7, 1)
        )
        layout.add_widget(version_label)
        
        self.add_widget(layout)
    
    def update_loading_text(self, text):
        """Update loading text"""
        self.loading_label.text = text
    
    def update_progress(self, value):
        """Update progress bar"""
        self.progress.value = value

class OfflineScreen(Screen):
    """Offline mode screen"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        
        # Offline icon
        offline_icon = Label(
            text='📱',
            font_size='80sp'
        )
        layout.add_widget(offline_icon)
        
        # Offline message
        offline_label = Label(
            text='Mode Hors Ligne',
            font_size='20sp',
            bold=True,
            color=(0.8, 0.4, 0.2, 1)
        )
        layout.add_widget(offline_label)
        
        # Description
        desc_label = Label(
            text='Vous pouvez naviguer dans les pages de base.\nLa connexion est requise pour les fonctionnalités avancées.',
            font_size='14sp',
            color=(0.5, 0.5, 0.5, 1),
            text_size=(Window.width - 40, None),
            size_hint_y=None,
            height=60
        )
        layout.add_widget(desc_label)
        
        # Continue button
        continue_btn = Button(
            text='Continuer en Mode Hors Ligne',
            size_hint=(None, None),
            size=(250, 50),
            pos_hint={'center_x': 0.5},
            background_color=(0.2, 0.6, 0.8, 1)
        )
        continue_btn.bind(on_press=self.continue_offline)
        layout.add_widget(continue_btn)
        
        # Retry connection button
        retry_btn = Button(
            text='Réessayer la Connexion',
            size_hint=(None, None),
            size=(250, 50),
            pos_hint={'center_x': 0.5},
            background_color=(0.8, 0.4, 0.2, 1)
        )
        retry_btn.bind(on_press=self.retry_connection)
        layout.add_widget(retry_btn)
        
        self.add_widget(layout)
    
    def continue_offline(self, instance):
        """Continue in offline mode"""
        app = App.get_running_app()
        app.switch_to_offline_mode()
    
    def retry_connection(self, instance):
        """Retry connection"""
        app = App.get_running_app()
        app.check_connection()

class MainWebView(Screen):
    """Main web view screen"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.webview = WebView(
            url='http://localhost:8000',
            size_hint=(1, 1)
        )
        self.add_widget(self.webview)
    
    def load_url(self, url):
        """Load URL in webview"""
        self.webview.url = url

class ConnectionManager:
    """Manages connection status and offline mode"""
    
    def __init__(self):
        self.store = JsonStore('connection_status.json')
        self.is_online = False
        self.last_check = None
        self.check_interval = 30  # Check every 30 seconds
        
        # Load cached status
        self.load_cached_status()
    
    def load_cached_status(self):
        """Load cached connection status"""
        try:
            if self.store.exists('status'):
                data = self.store.get('status')
                self.is_online = data.get('is_online', False)
                self.last_check = data.get('last_check')
        except Exception as e:
            print(f"Error loading cached status: {e}")
    
    def save_cached_status(self):
        """Save connection status to cache"""
        try:
            self.store.put('status', {
                'is_online': self.is_online,
                'last_check': datetime.now().isoformat()
            })
        except Exception as e:
            print(f"Error saving cached status: {e}")
    
    def check_connection(self, callback=None):
        """Check internet connection"""
        try:
            # Try to connect to the server
            response = requests.get(
                'http://localhost:8000/api/health/',
                timeout=5
            )
            
            self.is_online = response.status_code == 200
            self.last_check = datetime.now()
            self.save_cached_status()
            
            if callback:
                callback(self.is_online)
                
        except Exception as e:
            print(f"Connection check failed: {e}")
            self.is_online = False
            self.last_check = datetime.now()
            self.save_cached_status()
            
            if callback:
                callback(False)
    
    def is_connection_required(self, feature):
        """Check if connection is required for a specific feature"""
        connection_required_features = [
            'chat', 'orders', 'payments', 'user_profile',
            'notifications', 'reviews', 'favorites'
        ]
        
        return feature in connection_required_features
    
    def get_offline_pages(self):
        """Get list of pages available offline"""
        return [
            'visitor_home',
            'visitor_products', 
            'visitor_categories',
            'visitor_product_detail',
            'visitor_about',
            'visitor_contact'
        ]

class VGKEnhancedApp(App):
    """Enhanced VGK Mobile App"""
    
    title = 'Vidé-Grenier Kamer'
    version = '1.0.0'
    build_number = '1'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Initialize components
        self.connection_manager = ConnectionManager()
        self.screen_manager = ScreenManager()
        
        # App configuration
        self.base_url = 'http://localhost:8000'
        self.offline_mode = False
        
        # Set window size for desktop testing
        if platform == 'desktop':
            Window.size = (400, 700)
    
    def build(self):
        """Build the app"""
        # Add screens
        self.splash_screen = SplashScreen(name='splash')
        self.offline_screen = OfflineScreen(name='offline')
        self.main_screen = MainWebView(name='main')
        
        self.screen_manager.add_widget(self.splash_screen)
        self.screen_manager.add_widget(self.offline_screen)
        self.screen_manager.add_widget(self.main_screen)
        
        # Start with splash screen
        self.screen_manager.current = 'splash'
        
        # Start initialization
        Clock.schedule_once(self.initialize_app, 1)
        
        return self.screen_manager
    
    def initialize_app(self, dt):
        """Initialize the app"""
        self.splash_screen.update_loading_text('Vérification de la connexion...')
        self.splash_screen.update_progress(20)
        
        # Check connection
        self.connection_manager.check_connection(self.on_connection_check)
    
    def on_connection_check(self, is_online):
        """Handle connection check result"""
        if is_online:
            self.splash_screen.update_loading_text('Connexion établie...')
            self.splash_screen.update_progress(60)
            
            # Load main app
            Clock.schedule_once(self.load_main_app, 1)
        else:
            self.splash_screen.update_loading_text('Mode hors ligne...')
            self.splash_screen.update_progress(80)
            
            # Show offline screen
            Clock.schedule_once(self.show_offline_screen, 1)
    
    def load_main_app(self, dt):
        """Load main app"""
        self.splash_screen.update_loading_text('Chargement de l\'application...')
        self.splash_screen.update_progress(90)
        
        # Switch to main screen
        Clock.schedule_once(lambda dt: self.switch_to_main(), 1)
    
    def switch_to_main(self):
        """Switch to main screen"""
        self.screen_manager.current = 'main'
        self.splash_screen.update_progress(100)
    
    def show_offline_screen(self, dt):
        """Show offline screen"""
        self.screen_manager.current = 'offline'
    
    def switch_to_offline_mode(self):
        """Switch to offline mode"""
        self.offline_mode = True
        self.main_screen.load_url(f'{self.base_url}/visitor/home/')
        self.screen_manager.current = 'main'
    
    def check_connection(self):
        """Check connection and update status"""
        self.connection_manager.check_connection(self.on_connection_update)
    
    def on_connection_update(self, is_online):
        """Handle connection update"""
        if is_online and self.offline_mode:
            # Connection restored
            self.offline_mode = False
            self.main_screen.load_url(f'{self.base_url}/')
    
    def on_pause(self):
        """Handle app pause"""
        # Save app state
        return True
    
    def on_resume(self):
        """Handle app resume"""
        # Check connection when resuming
        self.check_connection()
    
    def on_stop(self):
        """Handle app stop"""
        # Clean up resources
        pass

class MobileConfig:
    """Mobile app configuration"""
    
    @staticmethod
    def get_app_config():
        """Get app configuration"""
        return {
            'app_name': 'Vidé-Grenier Kamer',
            'package_name': 'com.videgrenierkamer.app',
            'version': '1.0.0',
            'build_number': '1',
            'min_sdk': 21,
            'target_sdk': 33,
            'permissions': [
                'android.permission.INTERNET',
                'android.permission.ACCESS_NETWORK_STATE',
                'android.permission.WRITE_EXTERNAL_STORAGE',
                'android.permission.READ_EXTERNAL_STORAGE',
                'android.permission.CAMERA',
                'android.permission.ACCESS_FINE_LOCATION',
                'android.permission.ACCESS_COARSE_LOCATION'
            ],
            'features': [
                'android.hardware.camera',
                'android.hardware.location',
                'android.hardware.wifi'
            ],
            'activities': [
                {
                    'name': 'MainActivity',
                    'launch_mode': 'singleTask',
                    'screen_orientation': 'portrait'
                }
            ],
            'offline_pages': [
                'visitor_home',
                'visitor_products',
                'visitor_categories',
                'visitor_product_detail',
                'visitor_about',
                'visitor_contact'
            ],
            'connection_required_features': [
                'chat',
                'orders',
                'payments',
                'user_profile',
                'notifications',
                'reviews',
                'favorites'
            ]
        }
    
    @staticmethod
    def get_buildozer_config():
        """Get buildozer configuration for APK generation"""
        return {
            'app': {
                'title': 'Vidé-Grenier Kamer',
                'package.name': 'com.videgrenierkamer.app',
                'package.domain': 'com.videgrenierkamer',
                'source.dir': '.',
                'source.include_exts': 'py,png,jpg,kv,atlas,json',
                'version': '1.0.0',
                'requirements': 'kivy,requests,urllib3,certifi,charset-normalizer,idna',
                'orientation': 'portrait',
                'fullscreen': 0,
                'android.permissions': [
                    'INTERNET',
                    'ACCESS_NETWORK_STATE',
                    'WRITE_EXTERNAL_STORAGE',
                    'READ_EXTERNAL_STORAGE',
                    'CAMERA',
                    'ACCESS_FINE_LOCATION',
                    'ACCESS_COARSE_LOCATION'
                ],
                'android.api': 33,
                'android.minapi': 21,
                'android.sdk': 33,
                'android.ndk': 25,
                'android.arch': 'arm64-v8a',
                'android.allow_backup': True,
                'android.icon.filename': 'assets/icon.png',
                'android.presplash.filename': 'assets/splash.png',
                'android.services': 'org.kivy.android.PythonService',
                'android.private_storage': True,
                'android.accept_sdk_license': True
            },
            'buildozer': {
                'log_level': 2,
                'warn_on_root': 1
            }
        }

if __name__ == '__main__':
    VGKEnhancedApp().run() 