# kivy_app/main_enhanced.py - ENHANCED MOBILE APP FOR VGK
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.carousel import Carousel
from kivy.uix.modalview import ModalView
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.core.audio import SoundLoader
from kivy.clock import Clock
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, BooleanProperty
from kivy.storage.jsonstore import JsonStore
from kivy.network.urlrequest import UrlRequest
from kivy.utils import platform
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.animation import Animation
from kivy.effects import ScrollEffect
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recyclegridlayout import RecycleGridLayout

import json
import requests
import threading
import sqlite3
import os
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
import logging
from functools import partial

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============= DATABASE MANAGEMENT =============

class LocalDatabase:
    """Local SQLite database for offline functionality"""
    
    def __init__(self):
        self.db_path = os.path.join(os.path.expanduser('~'), '.vgk_mobile.db')
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                price REAL,
                category TEXT,
                seller_id TEXT,
                status TEXT,
                image_url TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # Cart table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cart_items (
                id TEXT PRIMARY KEY,
                product_id TEXT,
                quantity INTEGER,
                unit_price REAL,
                added_at TEXT,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        
        # User preferences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # Offline actions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS offline_actions (
                id TEXT PRIMARY KEY,
                action_type TEXT,
                data TEXT,
                created_at TEXT,
                synced INTEGER DEFAULT 0
            )
        ''')
        
        # Chat messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id TEXT PRIMARY KEY,
                chat_id TEXT,
                sender_id TEXT,
                content TEXT,
                message_type TEXT,
                created_at TEXT,
                is_read INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_product(self, product_data):
        """Save product to local database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO products 
            (id, title, description, price, category, seller_id, status, image_url, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            product_data['id'],
            product_data['title'],
            product_data['description'],
            product_data['price'],
            product_data['category'],
            product_data['seller_id'],
            product_data['status'],
            product_data.get('image_url', ''),
            product_data['created_at'],
            product_data['updated_at']
        ))
        
        conn.commit()
        conn.close()
    
    def get_products(self, category=None, search_query=None):
        """Get products from local database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM products WHERE status = 'ACTIVE'"
        params = []
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        if search_query:
            query += " AND (title LIKE ? OR description LIKE ?)"
            params.extend([f'%{search_query}%', f'%{search_query}%'])
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        products = cursor.fetchall()
        
        conn.close()
        
        return [
            {
                'id': p[0],
                'title': p[1],
                'description': p[2],
                'price': p[3],
                'category': p[4],
                'seller_id': p[5],
                'status': p[6],
                'image_url': p[7],
                'created_at': p[8],
                'updated_at': p[9]
            }
            for p in products
        ]
    
    def add_to_cart(self, product_id, quantity, unit_price):
        """Add item to cart"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if item already exists
        cursor.execute('SELECT id, quantity FROM cart_items WHERE product_id = ?', (product_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Update quantity
            new_quantity = existing[1] + quantity
            cursor.execute('UPDATE cart_items SET quantity = ? WHERE id = ?', (new_quantity, existing[0]))
        else:
            # Add new item
            cart_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO cart_items (id, product_id, quantity, unit_price, added_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (cart_id, product_id, quantity, unit_price, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_cart_items(self):
        """Get cart items"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.id, c.product_id, c.quantity, c.unit_price, c.added_at,
                   p.title, p.image_url
            FROM cart_items c
            JOIN products p ON c.product_id = p.id
        ''')
        
        items = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': item[0],
                'product_id': item[1],
                'quantity': item[2],
                'unit_price': item[3],
                'added_at': item[4],
                'title': item[5],
                'image_url': item[6]
            }
            for item in items
        ]
    
    def remove_from_cart(self, cart_item_id):
        """Remove item from cart"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM cart_items WHERE id = ?', (cart_item_id,))
        conn.commit()
        conn.close()
    
    def clear_cart(self):
        """Clear all cart items"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM cart_items')
        conn.commit()
        conn.close()
    
    def save_preference(self, key, value):
        """Save user preference"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('INSERT OR REPLACE INTO user_preferences (key, value) VALUES (?, ?)', (key, value))
        conn.commit()
        conn.close()
    
    def get_preference(self, key, default=None):
        """Get user preference"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT value FROM user_preferences WHERE key = ?', (key,))
        result = cursor.fetchone()
        
        conn.close()
        
        return result[0] if result else default
    
    def save_offline_action(self, action_type, data):
        """Save offline action for later sync"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        action_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO offline_actions (id, action_type, data, created_at)
            VALUES (?, ?, ?, ?)
        ''', (action_id, action_type, json.dumps(data), datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        return action_id
    
    def get_unsynced_actions(self):
        """Get unsynced offline actions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM offline_actions WHERE synced = 0 ORDER BY created_at')
        actions = cursor.fetchall()
        
        conn.close()
        
        return [
            {
                'id': action[0],
                'action_type': action[1],
                'data': json.loads(action[2]),
                'created_at': action[3]
            }
            for action in actions
        ]
    
    def mark_action_synced(self, action_id):
        """Mark action as synced"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE offline_actions SET synced = 1 WHERE id = ?', (action_id,))
        conn.commit()
        conn.close()

# ============= API CLIENT =============

class APIClient:
    """API client for server communication"""
    
    def __init__(self, base_url="https://vide-grenier-kamer.com/api"):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
    
    def set_auth_token(self, token):
        """Set authentication token"""
        self.auth_token = token
        self.session.headers.update({'Authorization': f'Bearer {token}'})
    
    def get_products(self, category=None, search=None, page=1):
        """Get products from API"""
        params = {'page': page}
        if category:
            params['category'] = category
        if search:
            params['search'] = search
        
        try:
            response = self.session.get(f"{self.base_url}/products/", params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching products: {e}")
            return None
    
    def get_product_detail(self, product_id):
        """Get product detail"""
        try:
            response = self.session.get(f"{self.base_url}/products/{product_id}/")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching product detail: {e}")
            return None
    
    def add_to_cart(self, product_id, quantity):
        """Add item to cart"""
        data = {
            'product_id': product_id,
            'quantity': quantity
        }
        
        try:
            response = self.session.post(f"{self.base_url}/cart/add/", json=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error adding to cart: {e}")
            return None
    
    def get_cart(self):
        """Get cart items"""
        try:
            response = self.session.get(f"{self.base_url}/cart/")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching cart: {e}")
            return None
    
    def login(self, username, password):
        """User login"""
        data = {
            'username': username,
            'password': password
        }
        
        try:
            response = self.session.post(f"{self.base_url}/auth/login/", json=data)
            response.raise_for_status()
            result = response.json()
            
            if result.get('success'):
                self.set_auth_token(result['token'])
            
            return result
        except requests.RequestException as e:
            logger.error(f"Error during login: {e}")
            return {'success': False, 'message': 'Erreur de connexion'}
    
    def register(self, user_data):
        """User registration"""
        try:
            response = self.session.post(f"{self.base_url}/auth/register/", json=user_data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error during registration: {e}")
            return {'success': False, 'message': 'Erreur d\'inscription'}
    
    def sync_offline_actions(self, actions):
        """Sync offline actions"""
        try:
            response = self.session.post(f"{self.base_url}/sync/", json={'actions': actions})
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error syncing offline actions: {e}")
            return None

# ============= CUSTOM WIDGETS =============

class ProductCard(ButtonBehavior, BoxLayout):
    """Product card widget"""
    
    def __init__(self, product_data, **kwargs):
        super().__init__(**kwargs)
        self.product_data = product_data
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(200)
        self.padding = dp(10)
        self.spacing = dp(5)
        
        # Product image
        self.image = Image(
            source=product_data.get('image_url', ''),
            size_hint=(1, 0.6),
            allow_stretch=True,
            keep_ratio=True
        )
        self.add_widget(self.image)
        
        # Product info
        info_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.4))
        
        # Title
        title = Label(
            text=product_data['title'][:30] + '...' if len(product_data['title']) > 30 else product_data['title'],
            size_hint=(1, 0.5),
            text_size=(None, None),
            halign='left',
            valign='middle'
        )
        info_layout.add_widget(title)
        
        # Price
        price = Label(
            text=f"{product_data['price']:,.0f} FCFA",
            size_hint=(1, 0.5),
            color=(0.2, 0.8, 0.2, 1),
            bold=True
        )
        info_layout.add_widget(price)
        
        self.add_widget(info_layout)
        
        # Add click binding
        self.bind(on_release=self.on_product_click)
    
    def on_product_click(self, instance):
        """Handle product click"""
        app = App.get_running_app()
        app.show_product_detail(self.product_data)

class CartItemWidget(BoxLayout):
    """Cart item widget"""
    
    def __init__(self, item_data, **kwargs):
        super().__init__(**kwargs)
        self.item_data = item_data
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(80)
        self.padding = dp(10)
        self.spacing = dp(10)
        
        # Product image
        image = Image(
            source=item_data.get('image_url', ''),
            size_hint=(None, 1),
            width=dp(60),
            allow_stretch=True,
            keep_ratio=True
        )
        self.add_widget(image)
        
        # Product info
        info_layout = BoxLayout(orientation='vertical', size_hint=(1, 1))
        
        # Title
        title = Label(
            text=item_data['title'],
            size_hint=(1, 0.5),
            text_size=(None, None),
            halign='left',
            valign='middle'
        )
        info_layout.add_widget(title)
        
        # Price and quantity
        price_qty_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.5))
        
        price = Label(
            text=f"{item_data['unit_price']:,.0f} FCFA",
            size_hint=(0.6, 1),
            color=(0.2, 0.8, 0.2, 1)
        )
        price_qty_layout.add_widget(price)
        
        qty = Label(
            text=f"Qté: {item_data['quantity']}",
            size_hint=(0.4, 1)
        )
        price_qty_layout.add_widget(qty)
        
        info_layout.add_widget(price_qty_layout)
        self.add_widget(info_layout)
        
        # Remove button
        remove_btn = Button(
            text='X',
            size_hint=(None, None),
            size=(dp(30), dp(30)),
            background_color=(0.8, 0.2, 0.2, 1)
        )
        remove_btn.bind(on_release=self.on_remove_click)
        self.add_widget(remove_btn)
    
    def on_remove_click(self, instance):
        """Handle remove click"""
        app = App.get_running_app()
        app.remove_from_cart(self.item_data['id'])

# ============= SCREENS =============

class SplashScreen(Screen):
    """Splash screen"""
    
    def on_enter(self):
        """Called when screen is entered"""
        Clock.schedule_once(self.load_main_screen, 2)
    
    def load_main_screen(self, dt):
        """Load main screen after delay"""
        app = App.get_running_app()
        app.root.current = 'main'

class MainScreen(Screen):
    """Main screen with bottom navigation"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup user interface"""
        layout = BoxLayout(orientation='vertical')
        
        # Content area
        self.content_area = BoxLayout(orientation='vertical')
        layout.add_widget(self.content_area)
        
        # Bottom navigation
        nav_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(60),
            padding=dp(10),
            spacing=dp(10)
        )
        
        # Navigation buttons
        home_btn = Button(
            text='Accueil',
            size_hint_x=0.25,
            background_color=(0.2, 0.6, 1, 1)
        )
        home_btn.bind(on_release=self.show_home)
        
        search_btn = Button(
            text='Recherche',
            size_hint_x=0.25,
            background_color=(0.2, 0.6, 1, 1)
        )
        search_btn.bind(on_release=self.show_search)
        
        cart_btn = Button(
            text='Panier',
            size_hint_x=0.25,
            background_color=(0.2, 0.6, 1, 1)
        )
        cart_btn.bind(on_release=self.show_cart)
        
        profile_btn = Button(
            text='Profil',
            size_hint_x=0.25,
            background_color=(0.2, 0.6, 1, 1)
        )
        profile_btn.bind(on_release=self.show_profile)
        
        nav_layout.add_widget(home_btn)
        nav_layout.add_widget(search_btn)
        nav_layout.add_widget(cart_btn)
        nav_layout.add_widget(profile_btn)
        
        layout.add_widget(nav_layout)
        self.add_widget(layout)
        
        # Show home by default
        self.show_home()
    
    def show_home(self, instance=None):
        """Show home screen"""
        self.content_area.clear_widgets()
        self.content_area.add_widget(HomeTab())
    
    def show_search(self, instance=None):
        """Show search screen"""
        self.content_area.clear_widgets()
        self.content_area.add_widget(SearchTab())
    
    def show_cart(self, instance=None):
        """Show cart screen"""
        self.content_area.clear_widgets()
        self.content_area.add_widget(CartTab())
    
    def show_profile(self, instance=None):
        """Show profile screen"""
        self.content_area.clear_widgets()
        self.content_area.add_widget(ProfileTab())

class HomeTab(BoxLayout):
    """Home tab content"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(10)
        self.spacing = dp(10)
        
        # Header
        header = Label(
            text='Vidé-Grenier Kamer',
            size_hint_y=None,
            height=dp(50),
            font_size=sp(20),
            bold=True
        )
        self.add_widget(header)
        
        # Search bar
        search_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40)
        )
        
        self.search_input = TextInput(
            hint_text='Rechercher un produit...',
            size_hint_x=0.8,
            multiline=False
        )
        search_layout.add_widget(self.search_input)
        
        search_btn = Button(
            text='🔍',
            size_hint_x=0.2
        )
        search_btn.bind(on_release=self.perform_search)
        search_layout.add_widget(search_btn)
        
        self.add_widget(search_layout)
        
        # Categories
        categories_label = Label(
            text='Catégories',
            size_hint_y=None,
            height=dp(30),
            bold=True
        )
        self.add_widget(categories_label)
        
        categories_layout = GridLayout(
            cols=3,
            size_hint_y=None,
            height=dp(120),
            spacing=dp(10)
        )
        
        categories = ['Électronique', 'Vêtements', 'Maison', 'Sport', 'Livres', 'Autres']
        for category in categories:
            cat_btn = Button(
                text=category,
                size_hint_y=None,
                height=dp(50)
            )
            cat_btn.bind(on_release=partial(self.show_category, category))
            categories_layout.add_widget(cat_btn)
        
        self.add_widget(categories_layout)
        
        # Featured products
        featured_label = Label(
            text='Produits en Vedette',
            size_hint_y=None,
            height=dp(30),
            bold=True
        )
        self.add_widget(featured_label)
        
        # Products grid
        self.products_layout = GridLayout(
            cols=2,
            size_hint_y=None,
            spacing=dp(10)
        )
        self.products_layout.bind(minimum_height=self.products_layout.setter('height'))
        
        # Scroll view for products
        scroll_view = ScrollView(size_hint=(1, 1))
        scroll_view.add_widget(self.products_layout)
        self.add_widget(scroll_view)
        
        # Load products
        self.load_products()
    
    def load_products(self):
        """Load products from API or local database"""
        app = App.get_running_app()
        
        # Try API first
        if app.api_client.auth_token:
            products = app.api_client.get_products()
            if products:
                self.display_products(products.get('results', []))
                return
        
        # Fallback to local database
        products = app.db.get_products()
        self.display_products(products)
    
    def display_products(self, products):
        """Display products in grid"""
        self.products_layout.clear_widgets()
        
        for product in products:
            card = ProductCard(product)
            self.products_layout.add_widget(card)
    
    def perform_search(self, instance):
        """Perform search"""
        query = self.search_input.text.strip()
        if query:
            app = App.get_running_app()
            products = app.db.get_products(search_query=query)
            self.display_products(products)
    
    def show_category(self, category, instance):
        """Show products by category"""
        app = App.get_running_app()
        products = app.db.get_products(category=category)
        self.display_products(products)

class SearchTab(BoxLayout):
    """Search tab content"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(10)
        self.spacing = dp(10)
        
        # Search header
        header = Label(
            text='Recherche Avancée',
            size_hint_y=None,
            height=dp(40),
            font_size=sp(18),
            bold=True
        )
        self.add_widget(header)
        
        # Search filters
        filters_layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(200),
            spacing=dp(10)
        )
        
        # Search input
        self.search_input = TextInput(
            hint_text='Rechercher un produit...',
            size_hint_y=None,
            height=dp(40),
            multiline=False
        )
        filters_layout.add_widget(self.search_input)
        
        # Category filter
        category_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        category_layout.add_widget(Label(text='Catégorie:', size_hint_x=0.3))
        
        self.category_spinner = Spinner(
            text='Toutes',
            values=['Toutes', 'Électronique', 'Vêtements', 'Maison', 'Sport', 'Livres', 'Autres'],
            size_hint_x=0.7
        )
        category_layout.add_widget(self.category_spinner)
        filters_layout.add_widget(category_layout)
        
        # Price range
        price_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        price_layout.add_widget(Label(text='Prix max:', size_hint_x=0.3))
        
        self.price_input = TextInput(
            hint_text='Prix maximum en FCFA',
            size_hint_x=0.7,
            multiline=False,
            input_filter='int'
        )
        price_layout.add_widget(self.price_input)
        filters_layout.add_widget(price_layout)
        
        # Search button
        search_btn = Button(
            text='Rechercher',
            size_hint_y=None,
            height=dp(40),
            background_color=(0.2, 0.8, 0.2, 1)
        )
        search_btn.bind(on_release=self.perform_search)
        filters_layout.add_widget(search_btn)
        
        self.add_widget(filters_layout)
        
        # Results
        results_label = Label(
            text='Résultats',
            size_hint_y=None,
            height=dp(30),
            bold=True
        )
        self.add_widget(results_label)
        
        # Results grid
        self.results_layout = GridLayout(
            cols=2,
            size_hint_y=None,
            spacing=dp(10)
        )
        self.results_layout.bind(minimum_height=self.results_layout.setter('height'))
        
        # Scroll view for results
        scroll_view = ScrollView(size_hint=(1, 1))
        scroll_view.add_widget(self.results_layout)
        self.add_widget(scroll_view)
    
    def perform_search(self, instance):
        """Perform advanced search"""
        query = self.search_input.text.strip()
        category = self.category_spinner.text
        max_price = self.price_input.text.strip()
        
        app = App.get_running_app()
        
        # Build search parameters
        search_params = {}
        if query:
            search_params['search_query'] = query
        if category and category != 'Toutes':
            search_params['category'] = category
        if max_price:
            search_params['max_price'] = float(max_price)
        
        # Search in local database
        products = app.db.get_products(**search_params)
        self.display_results(products)
    
    def display_results(self, products):
        """Display search results"""
        self.results_layout.clear_widgets()
        
        if not products:
            no_results = Label(
                text='Aucun produit trouvé',
                size_hint_y=None,
                height=dp(50)
            )
            self.results_layout.add_widget(no_results)
            return
        
        for product in products:
            card = ProductCard(product)
            self.results_layout.add_widget(card)

class CartTab(BoxLayout):
    """Cart tab content"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(10)
        self.spacing = dp(10)
        
        # Header
        header = Label(
            text='Mon Panier',
            size_hint_y=None,
            height=dp(40),
            font_size=sp(18),
            bold=True
        )
        self.add_widget(header)
        
        # Cart items
        self.cart_layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(10)
        )
        self.cart_layout.bind(minimum_height=self.cart_layout.setter('height'))
        
        # Scroll view for cart items
        scroll_view = ScrollView(size_hint=(1, 1))
        scroll_view.add_widget(self.cart_layout)
        self.add_widget(scroll_view)
        
        # Cart summary
        self.summary_layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(120),
            spacing=dp(5)
        )
        self.add_widget(self.summary_layout)
        
        # Load cart
        self.load_cart()
    
    def load_cart(self):
        """Load cart items"""
        app = App.get_running_app()
        cart_items = app.db.get_cart_items()
        self.display_cart_items(cart_items)
        self.update_summary(cart_items)
    
    def display_cart_items(self, cart_items):
        """Display cart items"""
        self.cart_layout.clear_widgets()
        
        if not cart_items:
            empty_label = Label(
                text='Votre panier est vide',
                size_hint_y=None,
                height=dp(50)
            )
            self.cart_layout.add_widget(empty_label)
            return
        
        for item in cart_items:
            item_widget = CartItemWidget(item)
            self.cart_layout.add_widget(item_widget)
    
    def update_summary(self, cart_items):
        """Update cart summary"""
        self.summary_layout.clear_widgets()
        
        if not cart_items:
            return
        
        # Calculate totals
        total_items = sum(item['quantity'] for item in cart_items)
        total_amount = sum(item['quantity'] * item['unit_price'] for item in cart_items)
        
        # Summary labels
        items_label = Label(
            text=f'Total articles: {total_items}',
            size_hint_y=None,
            height=dp(30)
        )
        self.summary_layout.add_widget(items_label)
        
        amount_label = Label(
            text=f'Montant total: {total_amount:,.0f} FCFA',
            size_hint_y=None,
            height=dp(30),
            bold=True,
            color=(0.2, 0.8, 0.2, 1)
        )
        self.summary_layout.add_widget(amount_label)
        
        # Checkout button
        checkout_btn = Button(
            text='Procéder au Paiement',
            size_hint_y=None,
            height=dp(40),
            background_color=(0.2, 0.8, 0.2, 1)
        )
        checkout_btn.bind(on_release=self.checkout)
        self.summary_layout.add_widget(checkout_btn)
    
    def checkout(self, instance):
        """Proceed to checkout"""
        app = App.get_running_app()
        app.show_checkout()

class ProfileTab(BoxLayout):
    """Profile tab content"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(10)
        self.spacing = dp(10)
        
        # Header
        header = Label(
            text='Mon Profil',
            size_hint_y=None,
            height=dp(40),
            font_size=sp(18),
            bold=True
        )
        self.add_widget(header)
        
        # Profile content
        self.profile_layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(10)
        )
        self.profile_layout.bind(minimum_height=self.profile_layout.setter('height'))
        
        # Scroll view
        scroll_view = ScrollView(size_hint=(1, 1))
        scroll_view.add_widget(self.profile_layout)
        self.add_widget(scroll_view)
        
        # Load profile
        self.load_profile()
    
    def load_profile(self):
        """Load profile content"""
        self.profile_layout.clear_widgets()
        
        app = App.get_running_app()
        
        if app.api_client.auth_token:
            # User is logged in
            self.show_logged_in_profile()
        else:
            # User is not logged in
            self.show_login_form()
    
    def show_login_form(self):
        """Show login form"""
        # Login section
        login_label = Label(
            text='Connexion',
            size_hint_y=None,
            height=dp(30),
            bold=True
        )
        self.profile_layout.add_widget(login_label)
        
        # Username
        self.username_input = TextInput(
            hint_text='Nom d\'utilisateur',
            size_hint_y=None,
            height=dp(40),
            multiline=False
        )
        self.profile_layout.add_widget(self.username_input)
        
        # Password
        self.password_input = TextInput(
            hint_text='Mot de passe',
            size_hint_y=None,
            height=dp(40),
            multiline=False,
            password=True
        )
        self.profile_layout.add_widget(self.password_input)
        
        # Login button
        login_btn = Button(
            text='Se Connecter',
            size_hint_y=None,
            height=dp(40),
            background_color=(0.2, 0.8, 0.2, 1)
        )
        login_btn.bind(on_release=self.login)
        self.profile_layout.add_widget(login_btn)
        
        # Register section
        register_label = Label(
            text='Nouveau compte',
            size_hint_y=None,
            height=dp(30),
            bold=True
        )
        self.profile_layout.add_widget(register_label)
        
        # Register button
        register_btn = Button(
            text='Créer un Compte',
            size_hint_y=None,
            height=dp(40),
            background_color=(0.2, 0.6, 1, 1)
        )
        register_btn.bind(on_release=self.show_register_form)
        self.profile_layout.add_widget(register_btn)
    
    def show_logged_in_profile(self):
        """Show logged in user profile"""
        # User info
        user_label = Label(
            text='Bienvenue!',
            size_hint_y=None,
            height=dp(30),
            bold=True
        )
        self.profile_layout.add_widget(user_label)
        
        # Menu options
        options = [
            ('Mes Commandes', self.show_orders),
            ('Mes Favoris', self.show_favorites),
            ('Paramètres', self.show_settings),
            ('Déconnexion', self.logout)
        ]
        
        for option_text, option_callback in options:
            option_btn = Button(
                text=option_text,
                size_hint_y=None,
                height=dp(40)
            )
            option_btn.bind(on_release=option_callback)
            self.profile_layout.add_widget(option_btn)
    
    def login(self, instance):
        """Handle login"""
        username = self.username_input.text.strip()
        password = self.password_input.text.strip()
        
        if not username or not password:
            self.show_message('Veuillez remplir tous les champs')
            return
        
        app = App.get_running_app()
        result = app.api_client.login(username, password)
        
        if result.get('success'):
            self.show_message('Connexion réussie!')
            self.load_profile()
        else:
            self.show_message(result.get('message', 'Erreur de connexion'))
    
    def logout(self, instance):
        """Handle logout"""
        app = App.get_running_app()
        app.api_client.set_auth_token(None)
        self.load_profile()
        self.show_message('Déconnexion réussie')
    
    def show_register_form(self, instance):
        """Show registration form"""
        # This would show a registration popup or navigate to register screen
        self.show_message('Fonctionnalité d\'inscription à venir')
    
    def show_orders(self, instance):
        """Show user orders"""
        self.show_message('Fonctionnalité des commandes à venir')
    
    def show_favorites(self, instance):
        """Show user favorites"""
        self.show_message('Fonctionnalité des favoris à venir')
    
    def show_settings(self, instance):
        """Show settings"""
        self.show_message('Fonctionnalité des paramètres à venir')
    
    def show_message(self, message):
        """Show popup message"""
        popup = Popup(
            title='Message',
            content=Label(text=message),
            size_hint=(None, None),
            size=(dp(300), dp(150))
        )
        popup.open()

# ============= MAIN APP =============

class VGKMobileApp(App):
    """Main mobile application"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = LocalDatabase()
        self.api_client = APIClient()
        
        # Load saved auth token
        saved_token = self.db.get_preference('auth_token')
        if saved_token:
            self.api_client.set_auth_token(saved_token)
    
    def build(self):
        """Build the application"""
        # Set window size for desktop testing
        if platform == 'desktop':
            Window.size = (400, 700)
        
        # Create screen manager
        sm = ScreenManager()
        
        # Add screens
        sm.add_widget(SplashScreen(name='splash'))
        sm.add_widget(MainScreen(name='main'))
        
        return sm
    
    def show_product_detail(self, product_data):
        """Show product detail screen"""
        # This would navigate to a product detail screen
        # For now, show a popup
        content = BoxLayout(orientation='vertical', padding=dp(20))
        
        # Product image
        image = Image(
            source=product_data.get('image_url', ''),
            size_hint=(1, 0.4),
            allow_stretch=True,
            keep_ratio=True
        )
        content.add_widget(image)
        
        # Product info
        title = Label(
            text=product_data['title'],
            size_hint_y=None,
            height=dp(40),
            bold=True
        )
        content.add_widget(title)
        
        price = Label(
            text=f"{product_data['price']:,.0f} FCFA",
            size_hint_y=None,
            height=dp(30),
            color=(0.2, 0.8, 0.2, 1),
            bold=True
        )
        content.add_widget(price)
        
        description = Label(
            text=product_data['description'],
            size_hint_y=None,
            height=dp(60),
            text_size=(None, None)
        )
        content.add_widget(description)
        
        # Add to cart button
        add_btn = Button(
            text='Ajouter au Panier',
            size_hint_y=None,
            height=dp(40),
            background_color=(0.2, 0.8, 0.2, 1)
        )
        add_btn.bind(on_release=lambda x: self.add_to_cart(product_data))
        content.add_widget(add_btn)
        
        popup = Popup(
            title='Détails du Produit',
            content=content,
            size_hint=(0.9, 0.8)
        )
        popup.open()
    
    def add_to_cart(self, product_data):
        """Add product to cart"""
        # Try API first
        if self.api_client.auth_token:
            result = self.api_client.add_to_cart(product_data['id'], 1)
            if result and result.get('success'):
                self.show_message('Produit ajouté au panier!')
                return
        
        # Fallback to local database
        self.db.add_to_cart(product_data['id'], 1, product_data['price'])
        self.show_message('Produit ajouté au panier!')
        
        # Save offline action
        self.db.save_offline_action('add_to_cart', {
            'product_id': product_data['id'],
            'quantity': 1
        })
    
    def remove_from_cart(self, cart_item_id):
        """Remove item from cart"""
        self.db.remove_from_cart(cart_item_id)
        self.show_message('Produit retiré du panier')
        
        # Refresh cart display
        main_screen = self.root.get_screen('main')
        cart_tab = main_screen.content_area.children[0]
        if isinstance(cart_tab, CartTab):
            cart_tab.load_cart()
    
    def show_checkout(self):
        """Show checkout screen"""
        self.show_message('Fonctionnalité de paiement à venir')
    
    def show_message(self, message):
        """Show popup message"""
        popup = Popup(
            title='Message',
            content=Label(text=message),
            size_hint=(None, None),
            size=(dp(300), dp(150))
        )
        popup.open()
    
    def sync_offline_data(self):
        """Sync offline data with server"""
        if not self.api_client.auth_token:
            return
        
        # Get unsynced actions
        actions = self.db.get_unsynced_actions()
        if not actions:
            return
        
        # Sync with server
        result = self.api_client.sync_offline_actions(actions)
        if result and result.get('success'):
            # Mark actions as synced
            for action in actions:
                self.db.mark_action_synced(action['id'])
    
    def on_stop(self):
        """Called when app is stopped"""
        # Save auth token
        if self.api_client.auth_token:
            self.db.save_preference('auth_token', self.api_client.auth_token)
        
        # Sync offline data
        self.sync_offline_data()

if __name__ == '__main__':
    VGKMobileApp().run() 