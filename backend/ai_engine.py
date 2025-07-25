# backend/ai_engine.py - AI RECOMMENDATION ENGINE FOR VGK
# Temporarily disable AI features to avoid dependency issues during development
try:
    import numpy as np
    import pandas as pd
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    AI_LIBRARIES_AVAILABLE = True
except ImportError:
    # Fallback for when AI libraries are not available
    AI_LIBRARIES_AVAILABLE = False
    np = None

from django.db.models import Count, Avg, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
import logging
import json
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

from .models import User, Product, Category, Order
from .models_advanced import (
    UserBehavior, UserPreference, ProductRecommendation,
    ShoppingCart, CartItem
)

logger = logging.getLogger(__name__)

class AIRecommendationEngine:
    """
    Advanced AI Recommendation Engine with multiple algorithms:
    - Collaborative Filtering (User-Based & Item-Based)
    - Content-Based Filtering
    - Hybrid Recommendations
    - Real-time Personalization
    """
    
    def __init__(self):
        self.min_interactions = 5  # Minimum interactions for recommendations
        self.similarity_threshold = 0.1
        self.recommendation_cache_hours = 6
        self.ai_available = AI_LIBRARIES_AVAILABLE
        
    def generate_recommendations_for_user(self, user: User, num_recommendations: int = 12) -> List[Dict]:
        """
        Generate comprehensive recommendations for a user
        """
        # Fallback when AI libraries are not available
        if not self.ai_available:
            return self._simple_recommendations(user, num_recommendations)
            
        try:
            # Check if we have cached recommendations
            cached_recs = self._get_cached_recommendations(user)
            if cached_recs.exists():
                return self._format_recommendations(cached_recs)
            
            # Generate new recommendations using multiple algorithms
            collaborative_recs = self._collaborative_filtering(user, num_recommendations // 3)
            content_based_recs = self._content_based_filtering(user, num_recommendations // 3)
            trending_recs = self._trending_recommendations(user, num_recommendations // 3)
            
            # Combine and rank recommendations
            all_recommendations = self._combine_recommendations([
                collaborative_recs,
                content_based_recs,
                trending_recs
            ])
            
            # Save recommendations to database
            self._save_recommendations(user, all_recommendations)
            
            return all_recommendations[:num_recommendations]
            
        except Exception as e:
            logger.error(f"Error generating recommendations for user {user.id}: {e}")
            return self._fallback_recommendations(user, num_recommendations)
    
    def _collaborative_filtering(self, user: User, num_recs: int) -> List[Dict]:
        """
        Collaborative filtering based on user behavior similarity
        """
        try:
            # Get user interaction matrix
            user_interactions = self._build_user_interaction_matrix()
            
            if user.id not in user_interactions:
                return []
            
            # Find similar users
            similar_users = self._find_similar_users(user, user_interactions)
            
            # Get products liked by similar users
            recommendations = []
            user_viewed_products = set(
                UserBehavior.objects.filter(user=user, action_type='VIEW')
                .values_list('product_id', flat=True)
            )
            
            for similar_user_id, similarity_score in similar_users[:10]:
                similar_user_products = UserBehavior.objects.filter(
                    user_id=similar_user_id,
                    action_type__in=['VIEW', 'LIKE', 'PURCHASE'],
                    product__status='ACTIVE'
                ).exclude(
                    product_id__in=user_viewed_products
                ).values_list('product_id', flat=True)
                
                for product_id in similar_user_products:
                    if len(recommendations) >= num_recs:
                        break
                    
                    try:
                        product = Product.objects.get(id=product_id, status='ACTIVE')
                        recommendations.append({
                            'product': product,
                            'score': similarity_score * 0.8,  # Collaborative weight
                            'type': 'COLLABORATIVE',
                            'reason': f"Users like you also viewed this product"
                        })
                    except Product.DoesNotExist:
                        continue
            
            return recommendations[:num_recs]
            
        except Exception as e:
            logger.error(f"Collaborative filtering error: {e}")
            return []
    
    def _content_based_filtering(self, user: User, num_recs: int) -> List[Dict]:
        """
        Content-based filtering using product and user preferences
        """
        try:
            # Get user preferences
            user_prefs = self._get_or_create_user_preferences(user)
            
            # Get user's interaction history
            user_categories = UserBehavior.objects.filter(
                user=user,
                action_type__in=['VIEW', 'LIKE', 'PURCHASE'],
                category__isnull=False
            ).values_list('category_id', flat=True)
            
            preferred_categories = list(set(user_categories))
            
            if not preferred_categories:
                return []
            
            # Get products from preferred categories
            candidate_products = Product.objects.filter(
                category_id__in=preferred_categories,
                status='ACTIVE'
            ).exclude(
                seller=user  # Don't recommend own products
            ).exclude(
                id__in=UserBehavior.objects.filter(
                    user=user, action_type='VIEW'
                ).values_list('product_id', flat=True)
            )
            
            # Score products based on content similarity
            recommendations = []
            for product in candidate_products[:num_recs * 2]:  # Get more for filtering
                score = self._calculate_content_similarity(user, product, user_prefs)
                if score > 0.3:  # Minimum similarity threshold
                    recommendations.append({
                        'product': product,
                        'score': score,
                        'type': 'CONTENT_BASED',
                        'reason': f"Based on your interest in {product.category.name}"
                    })
            
            # Sort by score and return top recommendations
            recommendations.sort(key=lambda x: x['score'], reverse=True)
            return recommendations[:num_recs]
            
        except Exception as e:
            logger.error(f"Content-based filtering error: {e}")
            return []
    
    def _trending_recommendations(self, user: User, num_recs: int) -> List[Dict]:
        """
        Trending products based on recent activity
        """
        try:
            # Calculate trending score based on recent views, likes, and purchases
            trending_products = Product.objects.filter(
                status='ACTIVE'
            ).exclude(
                seller=user
            ).annotate(
                recent_views=Count(
                    'userbehavior',
                    filter=Q(
                        userbehavior__action_type='VIEW',
                        userbehavior__created_at__gte=timezone.now() - timedelta(days=7)
                    )
                ),
                recent_likes=Count(
                    'userbehavior',
                    filter=Q(
                        userbehavior__action_type='LIKE',
                        userbehavior__created_at__gte=timezone.now() - timedelta(days=7)
                    )
                ),
                recent_purchases=Count(
                    'order',
                    filter=Q(
                        order__created_at__gte=timezone.now() - timedelta(days=7)
                    )
                )
            ).annotate(
                trending_score=F('recent_views') + F('recent_likes') * 3 + F('recent_purchases') * 5
            ).filter(
                trending_score__gt=0
            ).order_by('-trending_score')
            
            recommendations = []
            for product in trending_products[:num_recs]:
                recommendations.append({
                    'product': product,
                    'score': min(product.trending_score / 100.0, 1.0),  # Normalize score
                    'type': 'TRENDING',
                    'reason': "Trending now in your area"
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Trending recommendations error: {e}")
            return []
    
    def _build_user_interaction_matrix(self) -> Dict:
        """
        Build user-product interaction matrix for collaborative filtering
        """
        try:
            interactions = UserBehavior.objects.filter(
                action_type__in=['VIEW', 'LIKE', 'PURCHASE'],
                created_at__gte=timezone.now() - timedelta(days=90)
            ).values('user_id', 'product_id', 'action_type')
            
            user_matrix = defaultdict(lambda: defaultdict(float))
            
            # Weight different actions differently
            action_weights = {
                'VIEW': 1.0,
                'LIKE': 3.0,
                'PURCHASE': 5.0
            }
            
            for interaction in interactions:
                user_id = interaction['user_id']
                product_id = interaction['product_id']
                action = interaction['action_type']
                weight = action_weights.get(action, 1.0)
                
                user_matrix[user_id][product_id] += weight
            
            return dict(user_matrix)
            
        except Exception as e:
            logger.error(f"Error building interaction matrix: {e}")
            return {}
    
    def _find_similar_users(self, target_user: User, interaction_matrix: Dict) -> List[Tuple]:
        """
        Find users similar to the target user using cosine similarity
        """
        try:
            if target_user.id not in interaction_matrix:
                return []
            
            target_vector = interaction_matrix[target_user.id]
            similarities = []
            
            for user_id, user_vector in interaction_matrix.items():
                if user_id == target_user.id:
                    continue
                
                # Calculate cosine similarity
                similarity = self._cosine_similarity(target_vector, user_vector)
                if similarity > self.similarity_threshold:
                    similarities.append((user_id, similarity))
            
            # Sort by similarity descending
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities
            
        except Exception as e:
            logger.error(f"Error finding similar users: {e}")
            return []
    
    def _cosine_similarity(self, vec1: Dict, vec2: Dict) -> float:
        """
        Calculate cosine similarity between two sparse vectors
        """
        try:
            # Get common products
            common_products = set(vec1.keys()) & set(vec2.keys())
            
            if not common_products:
                return 0.0
            
            # Calculate dot product and magnitudes
            dot_product = sum(vec1[product] * vec2[product] for product in common_products)
            magnitude1 = sum(score ** 2 for score in vec1.values()) ** 0.5
            magnitude2 = sum(score ** 2 for score in vec2.values()) ** 0.5
            
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0
            
            return dot_product / (magnitude1 * magnitude2)
            
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def _calculate_content_similarity(self, user: User, product: Product, user_prefs: UserPreference) -> float:
        """
        Calculate content-based similarity score
        """
        try:
            score = 0.0
            
            # Category preference
            if user_prefs.preferred_categories:
                for cat_pref in user_prefs.preferred_categories:
                    if cat_pref.get('category_id') == str(product.category_id):
                        score += cat_pref.get('score', 0.5) * 0.4
            
            # Price range preference
            if user_prefs.price_range_min <= product.price <= user_prefs.price_range_max:
                score += 0.3
            
            # Condition preference
            if product.condition in user_prefs.preferred_conditions:
                score += 0.2
            
            # City preference
            if product.city in user_prefs.preferred_cities:
                score += 0.1
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating content similarity: {e}")
            return 0.0
    
    def _get_or_create_user_preferences(self, user: User) -> UserPreference:
        """
        Get or create user preferences based on behavior
        """
        try:
            prefs, created = UserPreference.objects.get_or_create(
                user=user,
                defaults={
                    'preferred_categories': [],
                    'price_range_min': 0,
                    'price_range_max': 100000,
                    'preferred_conditions': ['NEUF', 'EXCELLENT'],
                    'preferred_cities': [user.city] if user.city else [],
                    'shopping_patterns': {}
                }
            )
            
            if created or prefs.last_updated < timezone.now() - timedelta(days=7):
                # Update preferences based on recent behavior
                self._update_user_preferences(user, prefs)
            
            return prefs
            
        except Exception as e:
            logger.error(f"Error getting user preferences: {e}")
            return UserPreference()
    
    def _update_user_preferences(self, user: User, prefs: UserPreference):
        """
        Update user preferences based on recent behavior
        """
        try:
            # Analyze category preferences
            category_interactions = UserBehavior.objects.filter(
                user=user,
                action_type__in=['VIEW', 'LIKE', 'PURCHASE'],
                category__isnull=False,
                created_at__gte=timezone.now() - timedelta(days=30)
            ).values('category_id').annotate(
                count=Count('id'),
                avg_duration=Avg('duration')
            ).order_by('-count')
            
            preferred_categories = []
            total_interactions = sum(cat['count'] for cat in category_interactions)
            
            for cat in category_interactions:
                score = cat['count'] / total_interactions if total_interactions > 0 else 0
                preferred_categories.append({
                    'category_id': str(cat['category_id']),
                    'score': score
                })
            
            prefs.preferred_categories = preferred_categories
            
            # Analyze price preferences
            price_behaviors = UserBehavior.objects.filter(
                user=user,
                action_type__in=['VIEW', 'LIKE'],
                product__isnull=False,
                created_at__gte=timezone.now() - timedelta(days=30)
            ).values_list('product__price', flat=True)
            
            if price_behaviors:
                prices = list(price_behaviors)
                prefs.price_range_min = min(prices)
                prefs.price_range_max = max(prices)
            
            # Analyze condition preferences
            condition_behaviors = UserBehavior.objects.filter(
                user=user,
                action_type__in=['VIEW', 'LIKE'],
                product__isnull=False,
                created_at__gte=timezone.now() - timedelta(days=30)
            ).values_list('product__condition', flat=True)
            
            if condition_behaviors:
                prefs.preferred_conditions = list(set(condition_behaviors))
            
            prefs.last_updated = timezone.now()
            prefs.save()
            
        except Exception as e:
            logger.error(f"Error updating user preferences: {e}")
    
    def _combine_recommendations(self, recommendation_lists: List[List[Dict]]) -> List[Dict]:
        """
        Combine multiple recommendation lists with weighted scoring
        """
        try:
            combined = {}
            
            for rec_list in recommendation_lists:
                for rec in rec_list:
                    product_id = rec['product'].id
                    if product_id in combined:
                        # Combine scores (weighted average)
                        combined[product_id]['score'] = (
                            combined[product_id]['score'] + rec['score']
                        ) / 2
                        combined[product_id]['reason'] += f" | {rec['reason']}"
                    else:
                        combined[product_id] = rec
            
            # Sort by combined score
            sorted_recs = sorted(combined.values(), key=lambda x: x['score'], reverse=True)
            return sorted_recs
            
        except Exception as e:
            logger.error(f"Error combining recommendations: {e}")
            return []
    
    def _save_recommendations(self, user: User, recommendations: List[Dict]):
        """
        Save recommendations to database for caching
        """
        try:
            # Clear old recommendations
            ProductRecommendation.objects.filter(
                user=user,
                created_at__lt=timezone.now() - timedelta(hours=self.recommendation_cache_hours)
            ).delete()
            
            # Save new recommendations
            new_recs = []
            expires_at = timezone.now() + timedelta(hours=self.recommendation_cache_hours)
            
            for rec in recommendations:
                new_recs.append(
                    ProductRecommendation(
                        user=user,
                        product=rec['product'],
                        recommendation_type=rec['type'],
                        confidence_score=rec['score'],
                        reason=rec['reason'],
                        expires_at=expires_at
                    )
                )
            
            ProductRecommendation.objects.bulk_create(new_recs, ignore_conflicts=True)
            
        except Exception as e:
            logger.error(f"Error saving recommendations: {e}")
    
    def _get_cached_recommendations(self, user: User):
        """
        Get cached recommendations if available and fresh
        """
        return ProductRecommendation.objects.filter(
            user=user,
            expires_at__gt=timezone.now()
        ).select_related('product')
    
    def _format_recommendations(self, cached_recs):
        """
        Format cached recommendations
        """
        return [
            {
                'product': rec.product,
                'score': rec.confidence_score,
                'type': rec.recommendation_type,
                'reason': rec.reason
            }
            for rec in cached_recs
        ]
    
    def _fallback_recommendations(self, user: User, num_recs: int) -> List[Dict]:
        """
        Fallback recommendations when AI fails
        """
        try:
            # Return popular products from user's preferred categories or city
            popular_products = Product.objects.filter(
                status='ACTIVE'
            ).exclude(
                seller=user
            ).order_by('-views_count', '-created_at')
            
            if user.city:
                popular_products = popular_products.filter(city=user.city)
            
            recommendations = []
            for product in popular_products[:num_recs]:
                recommendations.append({
                    'product': product,
                    'score': 0.5,
                    'type': 'POPULAR',
                    'reason': "Popular products you might like"
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error in fallback recommendations: {e}")
            return []

    def track_user_behavior(self, user: User, action_type: str, product: Product = None, 
                          category: Category = None, session_id: str = None, 
                          duration: int = 0, metadata: Dict = None):
        """
        Track user behavior for improving recommendations
        """
        try:
            UserBehavior.objects.create(
                user=user,
                product=product,
                category=category,
                action_type=action_type,
                session_id=session_id or '',
                duration=duration,
                metadata=metadata or {}
            )
            
            # Update real-time preferences if significant action
            if action_type in ['PURCHASE', 'LIKE']:
                self._quick_preference_update(user, product, action_type)
                
        except Exception as e:
            logger.error(f"Error tracking user behavior: {e}")
    
    def _quick_preference_update(self, user: User, product: Product, action_type: str):
        """
        Quick preference update for real-time personalization
        """
        try:
            prefs = self._get_or_create_user_preferences(user)
            
            # Update category preference
            if product and product.category:
                category_found = False
                for cat_pref in prefs.preferred_categories:
                    if cat_pref.get('category_id') == str(product.category_id):
                        # Boost score based on action
                        boost = 0.1 if action_type == 'LIKE' else 0.2
                        cat_pref['score'] = min(cat_pref['score'] + boost, 1.0)
                        category_found = True
                        break
                
                if not category_found:
                    prefs.preferred_categories.append({
                        'category_id': str(product.category_id),
                        'score': 0.3 if action_type == 'LIKE' else 0.5
                    })
            
            prefs.save()
            
        except Exception as e:
            logger.error(f"Error in quick preference update: {e}")

    def _simple_recommendations(self, user: User, num_recommendations: int = 12) -> List[Dict]:
        """
        Simple recommendation fallback when AI libraries are not available
        """
        try:
            # Get user's order history to find preferred categories
            user_categories = Category.objects.filter(
                products__orders__user=user
            ).distinct()[:3] if hasattr(user, 'orders') else []
            
            # Get trending products from user's preferred categories
            recommendations = []
            if user_categories:
                for category in user_categories:
                    products = Product.objects.filter(
                        category=category,
                        status='ACTIVE'
                    ).exclude(
                        orders__user=user  # Exclude already purchased
                    ).order_by('-views_count', '-created_at')[:num_recommendations//3]
                    
                    for product in products:
                        recommendations.append({
                            'product_id': product.id,
                            'confidence_score': 0.7,
                            'reason': f'Popular in {category.name}',
                            'recommendation_type': 'TRENDING'
                        })
            
            # Fill remaining slots with overall trending products
            if len(recommendations) < num_recommendations:
                trending = Product.objects.filter(
                    status='ACTIVE'
                ).exclude(
                    id__in=[r['product_id'] for r in recommendations]
                ).order_by('-views_count', '-created_at')[:num_recommendations - len(recommendations)]
                
                for product in trending:
                    recommendations.append({
                        'product_id': product.id,
                        'confidence_score': 0.5,
                        'reason': 'Trending product',
                        'recommendation_type': 'TRENDING'
                    })
            
            return recommendations[:num_recommendations]
            
        except Exception as e:
            logger.error(f"Error in simple recommendations: {str(e)}")
            return []

# Singleton instance
ai_engine = AIRecommendationEngine() 