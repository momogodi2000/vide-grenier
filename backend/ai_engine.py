"""
AI Recommendation Engine for Vidé-Grenier Kamer
Provides personalized product recommendations based on user behavior and product similarities
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import NMF
from collections import defaultdict, Counter
import pandas as pd
from django.db.models import Q, Count, Avg, F
from django.core.cache import cache
from django.conf import settings
import logging
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class AIRecommendationEngine:
    """AI-powered recommendation engine for product suggestions"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.nmf_model = None
        self.product_features = None
        self.user_preferences = {}
        
    def analyze_user_behavior(self, user_id=None, session_key=None):
        """Analyze user behavior to build preference profile"""
        from .models import UserBehavior, Product, Category
        
        # Get user behaviors
        if user_id:
            behaviors = UserBehavior.objects.filter(user_id=user_id)
        elif session_key:
            behaviors = UserBehavior.objects.filter(session_key=session_key)
        else:
            return {}
        
        # Build preference profile
        preferences = {
            'categories': Counter(),
            'price_range': {'min': float('inf'), 'max': 0},
            'conditions': Counter(),
            'cities': Counter(),
            'viewed_products': set(),
            'liked_products': set(),
            'purchased_products': set(),
        }
        
        for behavior in behaviors:
            if behavior.product:
                # Category preferences
                if behavior.product.category:
                    weight = self._get_behavior_weight(behavior.action_type)
                    preferences['categories'][behavior.product.category.id] += weight
                
                # Price range
                price = float(behavior.product.price)
                preferences['price_range']['min'] = min(preferences['price_range']['min'], price)
                preferences['price_range']['max'] = max(preferences['price_range']['max'], price)
                
                # Condition preferences
                preferences['conditions'][behavior.product.condition] += weight
                
                # City preferences
                preferences['cities'][behavior.product.city] += weight
                
                # Product interactions
                if behavior.action_type == 'VIEW':
                    preferences['viewed_products'].add(behavior.product.id)
                elif behavior.action_type == 'LIKE':
                    preferences['liked_products'].add(behavior.product.id)
                elif behavior.action_type == 'PURCHASE':
                    preferences['purchased_products'].add(behavior.product.id)
        
        # Normalize preferences
        if preferences['price_range']['min'] == float('inf'):
            preferences['price_range'] = {'min': 0, 'max': 100000}
        
        return preferences
    
    def _get_behavior_weight(self, action_type):
        """Get weight for different behavior types"""
        weights = {
            'VIEW': 1,
            'LIKE': 3,
            'PURCHASE': 5,
            'CART_ADD': 2,
            'SHARE': 2,
            'CONTACT_SELLER': 4,
        }
        return weights.get(action_type, 1)
    
    def build_product_similarity_matrix(self):
        """Build product similarity matrix using TF-IDF and cosine similarity"""
        from .models import Product
        
        # Get all active products
        products = Product.objects.filter(status='ACTIVE').select_related('category', 'seller')
        
        if not products:
            return {}
        
        # Prepare product features
        product_features = []
        product_ids = []
        
        for product in products:
            # Combine product features
            features = f"{product.title} {product.description} {product.category.name} {product.condition} {product.city}"
            product_features.append(features)
            product_ids.append(str(product.id))
        
        # Create TF-IDF matrix
        tfidf_matrix = self.vectorizer.fit_transform(product_features)
        
        # Calculate cosine similarity
        similarity_matrix = cosine_similarity(tfidf_matrix)
        
        # Create similarity dictionary
        similarity_dict = {}
        for i, product_id in enumerate(product_ids):
            similarities = []
            for j, other_id in enumerate(product_ids):
                if i != j:
                    similarities.append((other_id, similarity_matrix[i][j]))
            
            # Sort by similarity and keep top 10
            similarities.sort(key=lambda x: x[1], reverse=True)
            similarity_dict[product_id] = similarities[:10]
        
        return similarity_dict
    
    def get_content_based_recommendations(self, product_id, limit=10):
        """Get content-based recommendations for a specific product"""
        cache_key = f'product_similarities_{product_id}'
        similarity_dict = cache.get(cache_key)
        
        if not similarity_dict:
            similarity_dict = self.build_product_similarity_matrix()
            cache.set(cache_key, similarity_dict, 3600)  # Cache for 1 hour
        
        if str(product_id) in similarity_dict:
            similar_products = similarity_dict[str(product_id)]
            product_ids = [pid for pid, score in similar_products]
            
            from .models import Product
            return Product.objects.filter(
                id__in=product_ids,
                status='ACTIVE'
            ).order_by('?')[:limit]
        
        return []
    
    def get_collaborative_recommendations(self, user_id=None, session_key=None, limit=10):
        """Get collaborative filtering recommendations"""
        from .models import Product, UserBehavior, Order
        
        # Get similar users based on behavior
        similar_users = self._find_similar_users(user_id, session_key)
        
        if not similar_users:
            return self._get_popular_products(limit)
        
        # Get products liked/purchased by similar users
        recommended_products = set()
        
        for similar_user_id in similar_users:
            if similar_user_id:
                # Get products from similar user
                user_products = UserBehavior.objects.filter(
                    user_id=similar_user_id,
                    action_type__in=['LIKE', 'PURCHASE']
                ).values_list('product_id', flat=True)
                
                recommended_products.update(user_products)
            else:
                # Session-based recommendations
                session_products = UserBehavior.objects.filter(
                    session_key=session_key,
                    action_type__in=['LIKE', 'PURCHASE']
                ).values_list('product_id', flat=True)
                
                recommended_products.update(session_products)
        
        # Filter and return products
        from .models import Product
        products = Product.objects.filter(
            id__in=recommended_products,
            status='ACTIVE'
        ).exclude(
            id__in=self._get_user_interacted_products(user_id, session_key)
        ).order_by('-views_count')[:limit]
        
        return products
    
    def _find_similar_users(self, user_id=None, session_key=None):
        """Find users with similar behavior patterns"""
        from .models import UserBehavior
        
        if user_id:
            # Get user's behavior patterns
            user_behaviors = UserBehavior.objects.filter(user_id=user_id)
            user_categories = set(user_behaviors.values_list('product__category_id', flat=True))
            
            # Find users with similar category preferences
            similar_users = UserBehavior.objects.filter(
                product__category_id__in=user_categories
            ).exclude(user_id=user_id).values_list('user_id', flat=True).distinct()
            
            return list(similar_users)[:5]
        
        return []
    
    def _get_user_interacted_products(self, user_id=None, session_key=None):
        """Get products user has already interacted with"""
        from .models import UserBehavior
        
        if user_id:
            return set(UserBehavior.objects.filter(user_id=user_id).values_list('product_id', flat=True))
        elif session_key:
            return set(UserBehavior.objects.filter(session_key=session_key).values_list('product_id', flat=True))
        
        return set()
    
    def _get_popular_products(self, limit=10):
        """Get popular products as fallback"""
        from .models import Product
        
        return Product.objects.filter(
            status='ACTIVE'
        ).order_by('-views_count', '-created_at')[:limit]
    
    def get_personalized_recommendations(self, user_id=None, session_key=None, limit=10):
        """Get personalized recommendations combining multiple approaches"""
        from .models import Product
        
        # Get user preferences
        preferences = self.analyze_user_behavior(user_id, session_key)
        
        # Build query based on preferences
        query = Q(status='ACTIVE')
        
        if preferences.get('categories'):
            top_categories = [cat_id for cat_id, _ in preferences['categories'].most_common(3)]
            query &= Q(category_id__in=top_categories)
        
        if preferences.get('price_range'):
            price_min = preferences['price_range']['min'] * 0.7
            price_max = preferences['price_range']['max'] * 1.3
            query &= Q(price__gte=price_min, price__lte=price_max)
        
        if preferences.get('conditions'):
            top_conditions = [cond for cond, _ in preferences['conditions'].most_common(2)]
            query &= Q(condition__in=top_conditions)
        
        if preferences.get('cities'):
            top_cities = [city for city, _ in preferences['cities'].most_common(2)]
            query &= Q(city__in=top_cities)
        
        # Exclude already interacted products
        interacted_products = self._get_user_interacted_products(user_id, session_key)
        if interacted_products:
            query &= ~Q(id__in=interacted_products)
        
        # Get recommendations
        recommendations = Product.objects.filter(query).order_by('-views_count', '-created_at')[:limit]
        
        # If not enough recommendations, add popular products
        if len(recommendations) < limit:
            remaining = limit - len(recommendations)
            popular_products = self._get_popular_products(remaining)
            recommendations = list(recommendations) + list(popular_products)
        
        return recommendations[:limit]
    
    def get_trending_products(self, days=7, limit=10):
        """Get trending products based on recent activity"""
        from .models import Product, UserBehavior
        
        # Get recent behaviors
        recent_date = datetime.now() - timedelta(days=days)
        
        trending_products = UserBehavior.objects.filter(
            created_at__gte=recent_date,
            action_type__in=['VIEW', 'LIKE', 'PURCHASE']
        ).values('product_id').annotate(
            activity_count=Count('id')
        ).order_by('-activity_count')[:limit]
        
        product_ids = [item['product_id'] for item in trending_products]
        
        return Product.objects.filter(
            id__in=product_ids,
            status='ACTIVE'
        ).order_by('?')[:limit]
    
    def get_cross_sell_recommendations(self, product_id, limit=5):
        """Get cross-sell recommendations for a product"""
        from .models import Product, Order
        
        # Find products frequently bought together
        product_orders = Order.objects.filter(
            product_id=product_id,
            status__in=['PAID', 'DELIVERED']
        ).values_list('buyer_id', flat=True)
        
        if not product_orders:
            return self.get_content_based_recommendations(product_id, limit)
        
        # Get other products bought by same buyers
        cross_sell_products = Order.objects.filter(
            buyer_id__in=product_orders,
            status__in=['PAID', 'DELIVERED']
        ).exclude(
            product_id=product_id
        ).values('product_id').annotate(
            frequency=Count('id')
        ).order_by('-frequency')[:limit]
        
        product_ids = [item['product_id'] for item in cross_sell_products]
        
        return Product.objects.filter(
            id__in=product_ids,
            status='ACTIVE'
        ).order_by('?')[:limit]
    
    def update_user_preferences(self, user_id=None, session_key=None, product_id=None, action_type=None):
        """Update user preferences based on new behavior"""
        from .models import UserBehavior, Product
        
        if not product_id:
            return
        
        # Create behavior record
        behavior_data = {
            'action_type': action_type,
            'product_id': product_id,
        }
        
        if user_id:
            behavior_data['user_id'] = user_id
        elif session_key:
            behavior_data['session_key'] = session_key
        
        UserBehavior.objects.create(**behavior_data)
        
        # Clear cache for this user
        cache_key = f'user_preferences_{user_id or session_key}'
        cache.delete(cache_key)
    
    def get_recommendation_explanation(self, product_id, user_id=None, session_key=None):
        """Get explanation for why a product is recommended"""
        from .models import Product
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return "Produit non trouvé"
        
        preferences = self.analyze_user_behavior(user_id, session_key)
        
        explanations = []
        
        # Category-based explanation
        if preferences.get('categories') and product.category_id in preferences['categories']:
            category_score = preferences['categories'][product.category_id]
            if category_score > 2:
                explanations.append(f"Vous aimez les produits de la catégorie {product.category.name}")
        
        # Price-based explanation
        if preferences.get('price_range'):
            user_avg_price = (preferences['price_range']['min'] + preferences['price_range']['max']) / 2
            if abs(float(product.price) - user_avg_price) / user_avg_price < 0.3:
                explanations.append("Prix similaire à vos préférences")
        
        # Condition-based explanation
        if preferences.get('conditions') and product.condition in preferences['conditions']:
            explanations.append(f"Vous préférez les produits en état {product.get_condition_display()}")
        
        # Location-based explanation
        if preferences.get('cities') and product.city in preferences['cities']:
            explanations.append(f"Produit disponible dans votre ville préférée")
        
        # Popularity explanation
        if product.views_count > 100:
            explanations.append("Produit très populaire")
        
        if explanations:
            return " • ".join(explanations)
        else:
            return "Produit recommandé par notre algorithme"


class ProductSimilarityEngine:
    """Engine for finding similar products"""
    
    def __init__(self):
        self.similarity_cache = {}
    
    def get_similar_products(self, product_id, limit=6):
        """Get similar products based on multiple criteria"""
        from .models import Product
        
        try:
            product = Product.objects.get(id=product_id, status='ACTIVE')
        except Product.DoesNotExist:
            return []
        
        # Build similarity query
        similar_products = Product.objects.filter(
            status='ACTIVE'
        ).exclude(id=product_id)
        
        # Same category products
        category_products = similar_products.filter(category=product.category)
        
        # Same condition products
        condition_products = similar_products.filter(condition=product.condition)
        
        # Same city products
        city_products = similar_products.filter(city=product.city)
        
        # Price range products (±30%)
        price_min = float(product.price) * 0.7
        price_max = float(product.price) * 1.3
        price_products = similar_products.filter(price__gte=price_min, price__lte=price_max)
        
        # Combine and rank
        all_similar = list(category_products) + list(condition_products) + list(city_products) + list(price_products)
        
        # Remove duplicates and rank by relevance
        seen = set()
        ranked_products = []
        
        for p in all_similar:
            if p.id not in seen:
                seen.add(p.id)
                score = self._calculate_similarity_score(product, p)
                ranked_products.append((p, score))
        
        # Sort by score and return top results
        ranked_products.sort(key=lambda x: x[1], reverse=True)
        return [p for p, score in ranked_products[:limit]]
    
    def _calculate_similarity_score(self, product1, product2):
        """Calculate similarity score between two products"""
        score = 0
        
        # Category similarity (weight: 3)
        if product1.category == product2.category:
            score += 3
        
        # Condition similarity (weight: 2)
        if product1.condition == product2.condition:
            score += 2
        
        # City similarity (weight: 1)
        if product1.city == product2.city:
            score += 1
        
        # Price similarity (weight: 2)
        price_diff = abs(float(product1.price) - float(product2.price)) / max(float(product1.price), float(product2.price))
        if price_diff < 0.3:
            score += 2 * (1 - price_diff)
        
        # Seller similarity (weight: 1)
        if product1.seller == product2.seller:
            score += 1
        
        return score


# Global instances
ai_engine = AIRecommendationEngine()
similarity_engine = ProductSimilarityEngine()


def get_recommendations_for_user(user_id=None, session_key=None, limit=10):
    """Get recommendations for a user or session"""
    return ai_engine.get_personalized_recommendations(user_id, session_key, limit)


def get_similar_products(product_id, limit=6):
    """Get similar products for a given product"""
    return similarity_engine.get_similar_products(product_id, limit)


def get_trending_products(days=7, limit=10):
    """Get trending products"""
    return ai_engine.get_trending_products(days, limit)


def update_user_behavior(user_id=None, session_key=None, product_id=None, action_type='VIEW'):
    """Update user behavior for recommendations"""
    ai_engine.update_user_preferences(user_id, session_key, product_id, action_type) 