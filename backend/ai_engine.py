"""
AI Recommendation Engine for Vidé-Grenier Kamer
Provides personalized product recommendations based on user behavior and product similarities
Uses Google Gemini for AI features and TensorFlow Serving for custom ML models
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
import requests
import os

# Import Gemini AI
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

# Import TensorFlow Serving
try:
    import tensorflow as tf
    import tensorflow_serving.apis.predict_pb2 as predict_pb2
    import tensorflow_serving.apis.prediction_service_pb2_grpc as prediction_service_pb2_grpc
    import grpc
    TF_SERVING_AVAILABLE = True
except ImportError:
    TF_SERVING_AVAILABLE = False
    tf = None

logger = logging.getLogger(__name__)

class GeminiAIEngine:
    """Google Gemini AI integration for VGK"""
    
    def __init__(self):
        if not GEMINI_AVAILABLE:
            logger.warning("Google Generative AI not available. Install with: pip install google-generativeai")
            return
        
        # Configure Gemini
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            logger.warning("GEMINI_API_KEY not found in environment variables")
            return
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(os.environ.get('GEMINI_MODEL', 'gemini-1.5-flash'))
        
    def generate_product_description(self, product_data):
        """Generate enhanced product description using Gemini"""
        if not GEMINI_AVAILABLE or not self.model:
            return product_data.get('description', '')
        
        try:
            prompt = f"""
            Améliorez la description de ce produit pour un marketplace camerounais:
            
            Titre: {product_data.get('title', '')}
            Description actuelle: {product_data.get('description', '')}
            Catégorie: {product_data.get('category', '')}
            État: {product_data.get('condition', '')}
            Prix: {product_data.get('price', '')} FCFA
            Ville: {product_data.get('city', '')}
            
            Créez une description améliorée qui:
            1. Est attrayante et professionnelle
            2. Met en valeur les points forts du produit
            3. Inclut des détails pertinents pour le marché camerounais
            4. Utilise un langage clair et accessible
            5. Respecte la limite de 500 mots
            
            Description améliorée:
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error generating product description with Gemini: {e}")
            return product_data.get('description', '')
    
    def analyze_sentiment(self, text):
        """Analyze sentiment of user reviews and feedback"""
        if not GEMINI_AVAILABLE or not self.model:
            return {'sentiment': 'neutral', 'score': 0.5}
        
        try:
            prompt = f"""
            Analysez le sentiment de ce texte et donnez une réponse au format JSON:
            
            Texte: "{text}"
            
            Répondez avec un JSON contenant:
            - sentiment: "positive", "negative", ou "neutral"
            - score: un nombre entre 0 et 1 (0 = très négatif, 1 = très positif)
            - confidence: un nombre entre 0 et 1 indiquant la confiance de l'analyse
            """
            
            response = self.model.generate_content(prompt)
            result = json.loads(response.text.strip())
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment with Gemini: {e}")
            return {'sentiment': 'neutral', 'score': 0.5, 'confidence': 0.0}
    
    def generate_recommendation_explanation(self, user_preferences, recommended_product):
        """Generate personalized explanation for product recommendations"""
        if not GEMINI_AVAILABLE or not self.model:
            return "Produit recommandé par notre algorithme"
        
        try:
            prompt = f"""
            Expliquez pourquoi ce produit est recommandé à cet utilisateur:
            
            Préférences utilisateur:
            - Catégories préférées: {user_preferences.get('categories', [])}
            - Fourchette de prix: {user_preferences.get('price_range', {})}
            - État préféré: {user_preferences.get('conditions', [])}
            - Ville: {user_preferences.get('cities', [])}
            
            Produit recommandé:
            - Titre: {recommended_product.get('title', '')}
            - Catégorie: {recommended_product.get('category', '')}
            - Prix: {recommended_product.get('price', '')} FCFA
            - État: {recommended_product.get('condition', '')}
            - Ville: {recommended_product.get('city', '')}
            
            Donnez une explication courte et personnalisée (max 100 mots) en français.
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error generating recommendation explanation with Gemini: {e}")
            return "Produit recommandé par notre algorithme"
    
    def moderate_content(self, content, content_type='product'):
        """Moderate user-generated content using AI"""
        if not GEMINI_AVAILABLE or not self.model:
            return {'approved': True, 'reason': 'AI moderation not available'}
        
        try:
            prompt = f"""
            Modérez ce contenu pour un marketplace camerounais:
            
            Type de contenu: {content_type}
            Contenu: "{content}"
            
            Vérifiez si le contenu:
            1. Respecte les règles de la communauté
            2. N'est pas inapproprié ou offensant
            3. Est pertinent pour un marketplace
            4. Ne contient pas de spam ou de contenu commercial non autorisé
            
            Répondez avec un JSON:
            - approved: true/false
            - reason: explication courte
            - confidence: niveau de confiance (0-1)
            """
            
            response = self.model.generate_content(prompt)
            result = json.loads(response.text.strip())
            return result
            
        except Exception as e:
            logger.error(f"Error moderating content with Gemini: {e}")
            return {'approved': True, 'reason': 'AI moderation error', 'confidence': 0.0}

class TensorFlowServingClient:
    """Client for TensorFlow Serving models"""
    
    def __init__(self):
        self.tf_serving_url = os.environ.get('TF_SERVING_URL', 'http://localhost:8501')
        self.enabled = os.environ.get('TF_SERVING_ENABLED', 'False').lower() == 'true'
        
        if not self.enabled:
            logger.info("TensorFlow Serving is disabled")
            return
        
        if not TF_SERVING_AVAILABLE:
            logger.warning("TensorFlow Serving not available. Install with: pip install tensorflow tensorflow-serving-api")
            return
    
    def get_recommendations(self, user_features, model_name='recommendation_model'):
        """Get recommendations from TensorFlow Serving model"""
        if not self.enabled or not TF_SERVING_AVAILABLE:
            return []
        
        try:
            # Prepare request
            request = predict_pb2.PredictRequest()
            request.model_spec.name = model_name
            request.model_spec.signature_name = 'serving_default'
            
            # Convert features to tensor
            features_tensor = tf.make_tensor_proto(user_features, dtype=tf.float32)
            request.inputs['features'].CopyFrom(features_tensor)
            
            # Make prediction
            channel = grpc.insecure_channel(self.tf_serving_url)
            stub = prediction_service_pb2_grpc.PredictionServiceStub(channel)
            response = stub.Predict(request, timeout=10.0)
            
            # Process response
            predictions = tf.make_ndarray(response.outputs['predictions'])
            return predictions.tolist()
            
        except Exception as e:
            logger.error(f"Error getting recommendations from TensorFlow Serving: {e}")
            return []
    
    def predict_user_behavior(self, user_data, model_name='behavior_model'):
        """Predict user behavior using TensorFlow Serving"""
        if not self.enabled or not TF_SERVING_AVAILABLE:
            return {}
        
        try:
            # Prepare request
            request = predict_pb2.PredictRequest()
            request.model_spec.name = model_name
            request.model_spec.signature_name = 'serving_default'
            
            # Convert user data to tensor
            user_tensor = tf.make_tensor_proto(user_data, dtype=tf.float32)
            request.inputs['user_data'].CopyFrom(user_tensor)
            
            # Make prediction
            channel = grpc.insecure_channel(self.tf_serving_url)
            stub = prediction_service_pb2_grpc.PredictionServiceStub(channel)
            response = stub.Predict(request, timeout=10.0)
            
            # Process response
            predictions = tf.make_ndarray(response.outputs['predictions'])
            return {
                'purchase_probability': float(predictions[0][0]),
                'churn_probability': float(predictions[0][1]),
                'lifetime_value': float(predictions[0][2])
            }
            
        except Exception as e:
            logger.error(f"Error predicting user behavior from TensorFlow Serving: {e}")
            return {}

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
        
        # Initialize AI components
        self.gemini_ai = GeminiAIEngine()
        self.tf_serving = TensorFlowServingClient()
        
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
        
        # Try TensorFlow Serving first if available
        if self.tf_serving.enabled and user_id:
            tf_recommendations = self._get_tf_serving_recommendations(user_id, preferences, limit)
            if tf_recommendations:
                return tf_recommendations
        
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
    
    def _get_tf_serving_recommendations(self, user_id, preferences, limit):
        """Get recommendations from TensorFlow Serving"""
        try:
            # Prepare user features for TensorFlow model
            user_features = self._prepare_user_features_for_tf(user_id, preferences)
            
            # Get recommendations from TensorFlow Serving
            tf_predictions = self.tf_serving.get_recommendations(user_features)
            
            if tf_predictions:
                # Convert predictions to product IDs and fetch products
                from .models import Product
                product_ids = [int(pid) for pid in tf_predictions[:limit]]
                products = Product.objects.filter(
                    id__in=product_ids,
                    status='ACTIVE'
                ).order_by('?')[:limit]
                
                return products
            
        except Exception as e:
            logger.error(f"Error getting TensorFlow Serving recommendations: {e}")
        
        return []
    
    def _prepare_user_features_for_tf(self, user_id, preferences):
        """Prepare user features for TensorFlow model"""
        # This is a simplified feature vector - in production, you'd have a more sophisticated feature engineering
        features = []
        
        # Category preferences (one-hot encoded)
        for i in range(10):  # Assuming 10 categories
            features.append(preferences.get('categories', {}).get(i, 0))
        
        # Price range features
        price_range = preferences.get('price_range', {'min': 0, 'max': 100000})
        features.append(price_range['min'] / 100000)  # Normalize
        features.append(price_range['max'] / 100000)  # Normalize
        
        # Condition preferences
        conditions = ['NEUF', 'EXCELLENT', 'BON', 'CORRECT', 'USAGE']
        for condition in conditions:
            features.append(preferences.get('conditions', {}).get(condition, 0))
        
        # City preferences
        cities = ['DOUALA', 'YAOUNDE', 'BAFOUSSAM', 'GAROUA', 'BAMENDA']
        for city in cities:
            features.append(preferences.get('cities', {}).get(city, 0))
        
        return features
    
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
        """Get explanation for why a product is recommended using Gemini AI"""
        from .models import Product
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return "Produit non trouvé"
        
        preferences = self.analyze_user_behavior(user_id, session_key)
        
        # Use Gemini AI for explanation if available
        if self.gemini_ai:
            product_data = {
                'title': product.title,
                'category': product.category.name,
                'price': product.price,
                'condition': product.get_condition_display(),
                'city': product.city
            }
            return self.gemini_ai.generate_recommendation_explanation(preferences, product_data)
        
        # Fallback to rule-based explanation
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
gemini_ai = GeminiAIEngine()
tf_serving = TensorFlowServingClient()


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


def generate_product_description(product_data):
    """Generate enhanced product description using Gemini AI"""
    return gemini_ai.generate_product_description(product_data) if gemini_ai else product_data.get('description', '')


def analyze_sentiment(text):
    """Analyze sentiment of text using Gemini AI"""
    return gemini_ai.analyze_sentiment(text) if gemini_ai else {'sentiment': 'neutral', 'score': 0.5}


def moderate_content(content, content_type='product'):
    """Moderate content using Gemini AI"""
    return gemini_ai.moderate_content(content, content_type) if gemini_ai else {'approved': True, 'reason': 'AI moderation not available'}


def predict_user_behavior(user_data):
    """Predict user behavior using TensorFlow Serving"""
    return tf_serving.predict_user_behavior(user_data) if tf_serving else {} 