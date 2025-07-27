# backend/stock_calculator.py - Advanced Stock Calculation Algorithms

from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from django.db.models import Q, F, Sum, Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta
import logging
from .models import Product, Order, AdminStock, Category
import math

logger = logging.getLogger(__name__)

class StockCalculator:
    """
    Advanced stock calculation and monitoring system
    """
    
    def __init__(self):
        self.alert_thresholds = {
            'critical': 0.1,  # 10% of average daily sales
            'low': 0.3,       # 30% of average daily sales
            'medium': 0.5,    # 50% of average daily sales
            'high': 0.8       # 80% of average daily sales
        }
    
    def calculate_stock_status(self, product: Product) -> Dict:
        """
        Calculate comprehensive stock status for a product
        """
        try:
            # Get basic stock information
            current_stock = product.stock_quantity or 0
            threshold = product.stock_threshold or 5
            
            # Calculate sales metrics
            sales_metrics = self.calculate_sales_metrics(product)
            
            # Calculate demand forecast
            demand_forecast = self.calculate_demand_forecast(product)
            
            # Calculate stock health score
            health_score = self.calculate_health_score(current_stock, threshold, sales_metrics)
            
            # Determine stock status
            status = self.determine_stock_status(current_stock, threshold, health_score)
            
            # Calculate reorder recommendations
            reorder_info = self.calculate_reorder_recommendations(product, current_stock, demand_forecast)
            
            return {
                'product_id': product.id,
                'product_name': product.title,
                'current_stock': current_stock,
                'threshold': threshold,
                'status': status,
                'health_score': health_score,
                'sales_metrics': sales_metrics,
                'demand_forecast': demand_forecast,
                'reorder_info': reorder_info,
                'last_updated': timezone.now(),
                'alerts': self.generate_stock_alerts(product, current_stock, threshold, health_score)
            }
            
        except Exception as e:
            logger.error(f"Error calculating stock status for product {product.id}: {e}")
            return self.get_default_stock_status(product)
    
    def calculate_sales_metrics(self, product: Product) -> Dict:
        """
        Calculate sales metrics for stock analysis
        """
        try:
            # Get date ranges
            now = timezone.now()
            last_30_days = now - timedelta(days=30)
            last_7_days = now - timedelta(days=7)
            last_24_hours = now - timedelta(hours=24)
            
            # Calculate daily sales
            daily_sales_30 = self.get_daily_sales(product, last_30_days, now)
            daily_sales_7 = self.get_daily_sales(product, last_7_days, now)
            daily_sales_24 = self.get_daily_sales(product, last_24_hours, now)
            
            # Calculate trends
            trend_7d = self.calculate_trend(daily_sales_7)
            trend_30d = self.calculate_trend(daily_sales_30)
            
            # Calculate seasonality
            seasonality = self.calculate_seasonality(product)
            
            return {
                'daily_sales_30d': daily_sales_30,
                'daily_sales_7d': daily_sales_7,
                'daily_sales_24h': daily_sales_24,
                'trend_7d': trend_7d,
                'trend_30d': trend_30d,
                'seasonality': seasonality,
                'avg_daily_sales': sum(daily_sales_30) / len(daily_sales_30) if daily_sales_30 else 0,
                'peak_day': self.find_peak_day(daily_sales_30),
                'low_day': self.find_low_day(daily_sales_30)
            }
            
        except Exception as e:
            logger.error(f"Error calculating sales metrics: {e}")
            return self.get_default_sales_metrics()
    
    def calculate_demand_forecast(self, product: Product) -> Dict:
        """
        Calculate demand forecast using multiple algorithms
        """
        try:
            # Get historical data
            historical_data = self.get_historical_sales_data(product)
            
            if not historical_data:
                return self.get_default_demand_forecast()
            
            # Simple moving average
            sma_forecast = self.simple_moving_average(historical_data, window=7)
            
            # Exponential smoothing
            es_forecast = self.exponential_smoothing(historical_data, alpha=0.3)
            
            # Linear regression
            lr_forecast = self.linear_regression_forecast(historical_data, days=7)
            
            # Weighted average of forecasts
            weighted_forecast = self.weighted_forecast_average([
                (sma_forecast, 0.3),
                (es_forecast, 0.4),
                (lr_forecast, 0.3)
            ])
            
            return {
                'next_7_days': weighted_forecast,
                'next_30_days': self.extend_forecast(weighted_forecast, 30),
                'confidence_interval': self.calculate_confidence_interval(historical_data),
                'seasonal_adjustment': self.calculate_seasonal_adjustment(product),
                'trend_direction': self.determine_trend_direction(historical_data)
            }
            
        except Exception as e:
            logger.error(f"Error calculating demand forecast: {e}")
            return self.get_default_demand_forecast()
    
    def calculate_health_score(self, current_stock: int, threshold: int, sales_metrics: Dict) -> float:
        """
        Calculate stock health score (0-100)
        """
        try:
            score = 0
            max_score = 100
            
            # Stock level score (40 points)
            if current_stock > threshold * 2:
                score += 40  # Excellent stock level
            elif current_stock > threshold:
                score += 30  # Good stock level
            elif current_stock > threshold * 0.5:
                score += 20  # Moderate stock level
            elif current_stock > 0:
                score += 10  # Low stock level
            else:
                score += 0   # Out of stock
            
            # Sales trend score (30 points)
            trend_7d = sales_metrics.get('trend_7d', 0)
            if trend_7d > 0.1:
                score += 30  # Growing demand
            elif trend_7d > -0.1:
                score += 20  # Stable demand
            elif trend_7d > -0.3:
                score += 10  # Declining demand
            else:
                score += 0   # Sharp decline
            
            # Stock turnover score (20 points)
            avg_daily_sales = sales_metrics.get('avg_daily_sales', 0)
            if avg_daily_sales > 0:
                days_of_stock = current_stock / avg_daily_sales
                if 7 <= days_of_stock <= 30:
                    score += 20  # Optimal turnover
                elif 3 <= days_of_stock <= 60:
                    score += 15  # Good turnover
                elif days_of_stock > 60:
                    score += 5   # Slow turnover
                else:
                    score += 0   # Very fast turnover
            
            # Seasonality score (10 points)
            seasonality = sales_metrics.get('seasonality', 1.0)
            if 0.8 <= seasonality <= 1.2:
                score += 10  # Normal seasonality
            elif 0.6 <= seasonality <= 1.4:
                score += 5   # Moderate seasonality
            else:
                score += 0   # High seasonality
            
            return min(score, max_score)
            
        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            return 50.0  # Default neutral score
    
    def determine_stock_status(self, current_stock: int, threshold: int, health_score: float) -> str:
        """
        Determine stock status based on current stock and health score
        """
        try:
            if current_stock == 0:
                return 'out_of_stock'
            elif current_stock <= threshold * 0.2:
                return 'critical'
            elif current_stock <= threshold * 0.5:
                return 'low'
            elif current_stock <= threshold:
                return 'moderate'
            elif health_score < 30:
                return 'poor_health'
            elif health_score < 60:
                return 'fair_health'
            else:
                return 'good_health'
                
        except Exception as e:
            logger.error(f"Error determining stock status: {e}")
            return 'unknown'
    
    def calculate_reorder_recommendations(self, product: Product, current_stock: int, demand_forecast: Dict) -> Dict:
        """
        Calculate reorder recommendations
        """
        try:
            next_7_days_demand = sum(demand_forecast.get('next_7_days', [0]))
            next_30_days_demand = sum(demand_forecast.get('next_30_days', [0]))
            
            # Safety stock calculation
            safety_stock = self.calculate_safety_stock(product)
            
            # Reorder point calculation
            reorder_point = safety_stock + (next_7_days_demand * 0.5)  # 50% of next week's demand
            
            # Economic order quantity
            eoq = self.calculate_economic_order_quantity(product)
            
            # Recommended order quantity
            recommended_quantity = max(
                eoq,
                next_30_days_demand - current_stock + safety_stock
            )
            
            return {
                'reorder_point': int(reorder_point),
                'economic_order_quantity': int(eoq),
                'recommended_quantity': int(recommended_quantity),
                'safety_stock': int(safety_stock),
                'days_until_reorder': self.calculate_days_until_reorder(current_stock, next_7_days_demand),
                'urgency_level': self.calculate_urgency_level(current_stock, reorder_point)
            }
            
        except Exception as e:
            logger.error(f"Error calculating reorder recommendations: {e}")
            return self.get_default_reorder_info()
    
    def generate_stock_alerts(self, product: Product, current_stock: int, threshold: int, health_score: float) -> List[Dict]:
        """
        Generate stock alerts based on various criteria
        """
        alerts = []
        
        try:
            # Out of stock alert
            if current_stock == 0:
                alerts.append({
                    'type': 'critical',
                    'message': f'Produit "{product.title}" en rupture de stock',
                    'priority': 'high',
                    'action_required': True
                })
            
            # Low stock alert
            elif current_stock <= threshold * 0.2:
                alerts.append({
                    'type': 'critical',
                    'message': f'Stock critique pour "{product.title}" ({current_stock} restant)',
                    'priority': 'high',
                    'action_required': True
                })
            
            elif current_stock <= threshold * 0.5:
                alerts.append({
                    'type': 'warning',
                    'message': f'Stock faible pour "{product.title}" ({current_stock} restant)',
                    'priority': 'medium',
                    'action_required': True
                })
            
            # Health score alerts
            if health_score < 30:
                alerts.append({
                    'type': 'health',
                    'message': f'Santé du stock dégradée pour "{product.title}" (score: {health_score:.1f})',
                    'priority': 'medium',
                    'action_required': False
                })
            
            # Overstock alert
            if current_stock > threshold * 3:
                alerts.append({
                    'type': 'overstock',
                    'message': f'Stock élevé pour "{product.title}" ({current_stock} en stock)',
                    'priority': 'low',
                    'action_required': False
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error generating stock alerts: {e}")
            return []
    
    # Helper methods for calculations
    def get_daily_sales(self, product: Product, start_date: datetime, end_date: datetime) -> List[int]:
        """Get daily sales for a product"""
        try:
            orders = Order.objects.filter(
                items__product=product,
                created_at__range=(start_date, end_date),
                status__in=['CONFIRMED', 'PROCESSING', 'SHIPPED', 'DELIVERED']
            )
            
            daily_sales = {}
            for order in orders:
                date = order.created_at.date()
                quantity = order.items.filter(product=product).aggregate(
                    total=Sum('quantity')
                )['total'] or 0
                daily_sales[date] = daily_sales.get(date, 0) + quantity
            
            return list(daily_sales.values())
            
        except Exception as e:
            logger.error(f"Error getting daily sales: {e}")
            return []
    
    def calculate_trend(self, data: List[int]) -> float:
        """Calculate trend in data"""
        if len(data) < 2:
            return 0.0
        
        try:
            n = len(data)
            x_sum = sum(range(n))
            y_sum = sum(data)
            xy_sum = sum(i * val for i, val in enumerate(data))
            x2_sum = sum(i * i for i in range(n))
            
            slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
            return slope
            
        except Exception as e:
            logger.error(f"Error calculating trend: {e}")
            return 0.0
    
    def calculate_seasonality(self, product: Product) -> float:
        """Calculate seasonality factor"""
        try:
            # Simple seasonality calculation based on day of week
            now = timezone.now()
            start_date = now - timedelta(days=30)
            
            daily_sales = self.get_daily_sales(product, start_date, now)
            if not daily_sales:
                return 1.0
            
            avg_sales = sum(daily_sales) / len(daily_sales)
            if avg_sales == 0:
                return 1.0
            
            # Calculate current day's average
            current_day_sales = daily_sales[-7:]  # Last 7 days
            current_avg = sum(current_day_sales) / len(current_day_sales)
            
            return current_avg / avg_sales if avg_sales > 0 else 1.0
            
        except Exception as e:
            logger.error(f"Error calculating seasonality: {e}")
            return 1.0
    
    def simple_moving_average(self, data: List[int], window: int = 7) -> List[float]:
        """Calculate simple moving average"""
        if len(data) < window:
            return [sum(data) / len(data)] * window
        
        result = []
        for i in range(window):
            start_idx = max(0, len(data) - window + i)
            window_data = data[start_idx:start_idx + window]
            result.append(sum(window_data) / len(window_data))
        
        return result
    
    def exponential_smoothing(self, data: List[int], alpha: float = 0.3) -> List[float]:
        """Calculate exponential smoothing forecast"""
        if not data:
            return []
        
        forecast = [data[0]]
        for i in range(1, len(data)):
            forecast.append(alpha * data[i] + (1 - alpha) * forecast[i-1])
        
        # Extend forecast for next 7 days
        for _ in range(7):
            forecast.append(alpha * data[-1] + (1 - alpha) * forecast[-1])
        
        return forecast[-7:]
    
    def linear_regression_forecast(self, data: List[int], days: int = 7) -> List[float]:
        """Calculate linear regression forecast"""
        if len(data) < 2:
            return [data[0] if data else 0] * days
        
        try:
            n = len(data)
            x_sum = sum(range(n))
            y_sum = sum(data)
            xy_sum = sum(i * val for i, val in enumerate(data))
            x2_sum = sum(i * i for i in range(n))
            
            slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
            intercept = (y_sum - slope * x_sum) / n
            
            forecast = []
            for i in range(n, n + days):
                forecast.append(slope * i + intercept)
            
            return forecast
            
        except Exception as e:
            logger.error(f"Error in linear regression forecast: {e}")
            return [data[-1] if data else 0] * days
    
    def weighted_forecast_average(self, forecasts: List[Tuple[List[float], float]]) -> List[float]:
        """Calculate weighted average of multiple forecasts"""
        if not forecasts:
            return []
        
        # Normalize weights
        total_weight = sum(weight for _, weight in forecasts)
        if total_weight == 0:
            return []
        
        # Calculate weighted average
        result = []
        max_length = max(len(forecast) for forecast, _ in forecasts)
        
        for i in range(max_length):
            weighted_sum = 0
            for forecast, weight in forecasts:
                if i < len(forecast):
                    weighted_sum += forecast[i] * (weight / total_weight)
            result.append(weighted_sum)
        
        return result
    
    def calculate_safety_stock(self, product: Product) -> float:
        """Calculate safety stock level"""
        try:
            # Get historical demand variability
            historical_data = self.get_historical_sales_data(product)
            if not historical_data:
                return product.stock_threshold or 5
            
            # Calculate standard deviation
            mean_demand = sum(historical_data) / len(historical_data)
            variance = sum((x - mean_demand) ** 2 for x in historical_data) / len(historical_data)
            std_dev = math.sqrt(variance)
            
            # Safety stock = Z * std_dev * sqrt(lead_time)
            # Using 95% service level (Z = 1.645) and 7-day lead time
            safety_stock = 1.645 * std_dev * math.sqrt(7)
            
            return max(safety_stock, 1)  # Minimum safety stock of 1
            
        except Exception as e:
            logger.error(f"Error calculating safety stock: {e}")
            return product.stock_threshold or 5
    
    def calculate_economic_order_quantity(self, product: Product) -> float:
        """Calculate Economic Order Quantity"""
        try:
            # EOQ = sqrt((2 * D * S) / H)
            # D = Annual demand
            # S = Ordering cost
            # H = Holding cost per unit per year
            
            # Estimate annual demand
            historical_data = self.get_historical_sales_data(product)
            if not historical_data:
                return product.stock_threshold or 5
            
            annual_demand = sum(historical_data) * (365 / len(historical_data))
            
            # Default costs (should be configurable)
            ordering_cost = 1000  # XAF per order
            holding_cost = product.price * 0.2  # 20% of product cost per year
            
            if holding_cost <= 0:
                return product.stock_threshold or 5
            
            eoq = math.sqrt((2 * annual_demand * ordering_cost) / holding_cost)
            return max(eoq, 1)
            
        except Exception as e:
            logger.error(f"Error calculating EOQ: {e}")
            return product.stock_threshold or 5
    
    # Utility methods
    def get_historical_sales_data(self, product: Product) -> List[int]:
        """Get historical sales data for forecasting"""
        try:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=90)  # 3 months of data
            
            return self.get_daily_sales(product, start_date, end_date)
            
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return []
    
    def find_peak_day(self, daily_sales: List[int]) -> int:
        """Find day with peak sales"""
        if not daily_sales:
            return 0
        return daily_sales.index(max(daily_sales))
    
    def find_low_day(self, daily_sales: List[int]) -> int:
        """Find day with lowest sales"""
        if not daily_sales:
            return 0
        return daily_sales.index(min(daily_sales))
    
    def calculate_confidence_interval(self, data: List[int]) -> Tuple[float, float]:
        """Calculate confidence interval for forecast"""
        if not data:
            return (0, 0)
        
        try:
            mean = sum(data) / len(data)
            variance = sum((x - mean) ** 2 for x in data) / len(data)
            std_error = math.sqrt(variance / len(data))
            
            # 95% confidence interval
            margin = 1.96 * std_error
            return (mean - margin, mean + margin)
            
        except Exception as e:
            logger.error(f"Error calculating confidence interval: {e}")
            return (0, 0)
    
    def calculate_seasonal_adjustment(self, product: Product) -> float:
        """Calculate seasonal adjustment factor"""
        # This would typically use more sophisticated seasonal analysis
        # For now, return a simple factor based on current month
        current_month = timezone.now().month
        
        # Simple seasonal factors (should be based on historical data)
        seasonal_factors = {
            1: 0.8, 2: 0.9, 3: 1.0, 4: 1.1, 5: 1.2, 6: 1.1,
            7: 1.0, 8: 0.9, 9: 1.0, 10: 1.1, 11: 1.2, 12: 1.3
        }
        
        return seasonal_factors.get(current_month, 1.0)
    
    def determine_trend_direction(self, data: List[int]) -> str:
        """Determine trend direction"""
        if len(data) < 2:
            return 'stable'
        
        trend = self.calculate_trend(data)
        
        if trend > 0.1:
            return 'increasing'
        elif trend < -0.1:
            return 'decreasing'
        else:
            return 'stable'
    
    def extend_forecast(self, short_forecast: List[float], days: int) -> List[float]:
        """Extend short-term forecast to longer period"""
        if not short_forecast:
            return []
        
        # Simple extension using the last value
        last_value = short_forecast[-1]
        extension = [last_value] * (days - len(short_forecast))
        
        return short_forecast + extension
    
    def calculate_days_until_reorder(self, current_stock: int, weekly_demand: float) -> int:
        """Calculate days until reorder point is reached"""
        if weekly_demand <= 0:
            return 999  # No demand, no reorder needed
        
        daily_demand = weekly_demand / 7
        if daily_demand <= 0:
            return 999
        
        return int(current_stock / daily_demand)
    
    def calculate_urgency_level(self, current_stock: int, reorder_point: float) -> str:
        """Calculate urgency level for reordering"""
        if current_stock <= reorder_point * 0.5:
            return 'critical'
        elif current_stock <= reorder_point:
            return 'urgent'
        elif current_stock <= reorder_point * 1.5:
            return 'soon'
        else:
            return 'normal'
    
    # Default return methods
    def get_default_stock_status(self, product: Product) -> Dict:
        """Get default stock status"""
        return {
            'product_id': product.id,
            'product_name': product.title,
            'current_stock': product.stock_quantity or 0,
            'threshold': product.stock_threshold or 5,
            'status': 'unknown',
            'health_score': 50.0,
            'sales_metrics': self.get_default_sales_metrics(),
            'demand_forecast': self.get_default_demand_forecast(),
            'reorder_info': self.get_default_reorder_info(),
            'last_updated': timezone.now(),
            'alerts': []
        }
    
    def get_default_sales_metrics(self) -> Dict:
        """Get default sales metrics"""
        return {
            'daily_sales_30d': [],
            'daily_sales_7d': [],
            'daily_sales_24h': [],
            'trend_7d': 0.0,
            'trend_30d': 0.0,
            'seasonality': 1.0,
            'avg_daily_sales': 0.0,
            'peak_day': 0,
            'low_day': 0
        }
    
    def get_default_demand_forecast(self) -> Dict:
        """Get default demand forecast"""
        return {
            'next_7_days': [0] * 7,
            'next_30_days': [0] * 30,
            'confidence_interval': (0, 0),
            'seasonal_adjustment': 1.0,
            'trend_direction': 'stable'
        }
    
    def get_default_reorder_info(self) -> Dict:
        """Get default reorder information"""
        return {
            'reorder_point': 5,
            'economic_order_quantity': 10,
            'recommended_quantity': 10,
            'safety_stock': 2,
            'days_until_reorder': 999,
            'urgency_level': 'normal'
        }


# Global stock calculator instance
stock_calculator = StockCalculator() 