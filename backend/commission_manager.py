# backend/commission_manager.py - Commission Management System

from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta
import logging
from .models import Order, Payment, User, Product
from .email_service import email_service

logger = logging.getLogger(__name__)

class CommissionManager:
    """
    Comprehensive commission management system
    """
    
    def __init__(self):
        self.default_commission_rate = Decimal('0.05')  # 5%
        self.minimum_commission = Decimal('100')  # 100 XAF
        self.maximum_commission = Decimal('5000')  # 5000 XAF
        self.payout_threshold = Decimal('1000')  # 1000 XAF minimum for payout
    
    def calculate_commission(self, order: Order) -> Dict:
        """
        Calculate commission for an order
        """
        try:
            # Get order details
            total_amount = order.total_amount
            seller = order.items.first().product.seller if order.items.exists() else None
            
            if not seller:
                return self.get_default_commission_result()
            
            # Get commission rate for seller
            commission_rate = self.get_seller_commission_rate(seller)
            
            # Calculate commission amount
            commission_amount = total_amount * commission_rate
            
            # Apply minimum and maximum limits
            commission_amount = max(commission_amount, self.minimum_commission)
            commission_amount = min(commission_amount, self.maximum_commission)
            
            # Calculate net amount for seller
            net_amount = total_amount - commission_amount
            
            return {
                'order_id': order.id,
                'order_number': order.order_number,
                'seller_id': seller.id,
                'seller_name': seller.get_full_name(),
                'total_amount': total_amount,
                'commission_rate': commission_rate,
                'commission_amount': commission_amount,
                'net_amount': net_amount,
                'calculation_date': timezone.now(),
                'status': 'calculated'
            }
            
        except Exception as e:
            logger.error(f"Error calculating commission for order {order.id}: {e}")
            return self.get_default_commission_result()
    
    def calculate_seller_commissions(self, seller: User, start_date: datetime = None, end_date: datetime = None) -> Dict:
        """
        Calculate total commissions for a seller in a date range
        """
        try:
            if not start_date:
                start_date = timezone.now() - timedelta(days=30)
            if not end_date:
                end_date = timezone.now()
            
            # Get orders for seller in date range
            orders = Order.objects.filter(
                items__product__seller=seller,
                created_at__range=(start_date, end_date),
                status__in=['CONFIRMED', 'PROCESSING', 'SHIPPED', 'DELIVERED'],
                payment_status='COMPLETED'
            ).distinct()
            
            total_orders = orders.count()
            total_sales = orders.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
            
            # Calculate commissions
            total_commission = Decimal('0')
            commission_details = []
            
            for order in orders:
                commission_info = self.calculate_commission(order)
                total_commission += commission_info['commission_amount']
                commission_details.append(commission_info)
            
            # Calculate average commission rate
            avg_commission_rate = (total_commission / total_sales * 100) if total_sales > 0 else 0
            
            return {
                'seller_id': seller.id,
                'seller_name': seller.get_full_name(),
                'period_start': start_date,
                'period_end': end_date,
                'total_orders': total_orders,
                'total_sales': total_sales,
                'total_commission': total_commission,
                'average_commission_rate': avg_commission_rate,
                'commission_details': commission_details,
                'payout_eligible': total_commission >= self.payout_threshold,
                'calculation_date': timezone.now()
            }
            
        except Exception as e:
            logger.error(f"Error calculating seller commissions: {e}")
            return self.get_default_seller_commission_result(seller)
    
    def calculate_all_commissions(self, start_date: datetime = None, end_date: datetime = None) -> Dict:
        """
        Calculate commissions for all sellers
        """
        try:
            if not start_date:
                start_date = timezone.now() - timedelta(days=30)
            if not end_date:
                end_date = timezone.now()
            
            # Get all sellers with orders in date range
            sellers = User.objects.filter(
                products__order_items__order__created_at__range=(start_date, end_date),
                products__order_items__order__status__in=['CONFIRMED', 'PROCESSING', 'SHIPPED', 'DELIVERED'],
                products__order_items__order__payment_status='COMPLETED'
            ).distinct()
            
            total_commission = Decimal('0')
            seller_commissions = []
            
            for seller in sellers:
                seller_commission = self.calculate_seller_commissions(seller, start_date, end_date)
                total_commission += seller_commission['total_commission']
                seller_commissions.append(seller_commission)
            
            # Sort by commission amount
            seller_commissions.sort(key=lambda x: x['total_commission'], reverse=True)
            
            return {
                'period_start': start_date,
                'period_end': end_date,
                'total_sellers': len(sellers),
                'total_commission': total_commission,
                'seller_commissions': seller_commissions,
                'calculation_date': timezone.now()
            }
            
        except Exception as e:
            logger.error(f"Error calculating all commissions: {e}")
            return self.get_default_all_commissions_result()
    
    def process_commission_payout(self, seller: User, amount: Decimal, payment_method: str = 'bank_transfer') -> Dict:
        """
        Process commission payout for a seller
        """
        try:
            # Verify seller has sufficient commission balance
            available_commission = self.get_seller_commission_balance(seller)
            
            if available_commission < amount:
                return {
                    'success': False,
                    'error': f'Insufficient commission balance. Available: {available_commission}, Requested: {amount}'
                }
            
            # Create payout record
            payout_record = self.create_payout_record(seller, amount, payment_method)
            
            # Update seller's commission balance
            self.update_seller_commission_balance(seller, amount)
            
            # Send payout notification
            self.send_payout_notification(seller, amount, payment_method)
            
            return {
                'success': True,
                'payout_id': payout_record['id'],
                'amount': amount,
                'payment_method': payment_method,
                'processed_date': timezone.now()
            }
            
        except Exception as e:
            logger.error(f"Error processing commission payout: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_commission_statistics(self, period_days: int = 30) -> Dict:
        """
        Get commission statistics for the specified period
        """
        try:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=period_days)
            
            # Get commission data
            commission_data = self.calculate_all_commissions(start_date, end_date)
            
            # Calculate additional statistics
            total_orders = sum(sc['total_orders'] for sc in commission_data['seller_commissions'])
            total_sales = sum(sc['total_sales'] for sc in commission_data['seller_commissions'])
            
            # Top performers
            top_performers = commission_data['seller_commissions'][:5]
            
            # Commission distribution
            commission_ranges = self.calculate_commission_distribution(commission_data['seller_commissions'])
            
            # Growth analysis
            growth_data = self.calculate_commission_growth(period_days)
            
            return {
                'period_days': period_days,
                'period_start': start_date,
                'period_end': end_date,
                'total_commission': commission_data['total_commission'],
                'total_sellers': commission_data['total_sellers'],
                'total_orders': total_orders,
                'total_sales': total_sales,
                'average_commission_per_seller': commission_data['total_commission'] / commission_data['total_sellers'] if commission_data['total_sellers'] > 0 else 0,
                'top_performers': top_performers,
                'commission_distribution': commission_ranges,
                'growth_data': growth_data,
                'payout_eligible_sellers': len([sc for sc in commission_data['seller_commissions'] if sc['payout_eligible']])
            }
            
        except Exception as e:
            logger.error(f"Error getting commission statistics: {e}")
            return self.get_default_commission_statistics()
    
    def generate_commission_report(self, start_date: datetime, end_date: datetime, format: str = 'json') -> Dict:
        """
        Generate comprehensive commission report
        """
        try:
            # Get commission data
            commission_data = self.calculate_all_commissions(start_date, end_date)
            
            # Generate report sections
            report = {
                'report_info': {
                    'generated_date': timezone.now(),
                    'period_start': start_date,
                    'period_end': end_date,
                    'format': format
                },
                'summary': {
                    'total_commission': commission_data['total_commission'],
                    'total_sellers': commission_data['total_sellers'],
                    'average_commission': commission_data['total_commission'] / commission_data['total_sellers'] if commission_data['total_sellers'] > 0 else 0
                },
                'seller_details': commission_data['seller_commissions'],
                'top_performers': commission_data['seller_commissions'][:10],
                'payout_recommendations': self.generate_payout_recommendations(commission_data['seller_commissions'])
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating commission report: {e}")
            return {'error': str(e)}
    
    def get_seller_commission_rate(self, seller: User) -> Decimal:
        """
        Get commission rate for a seller
        """
        try:
            # Check if seller has custom commission rate
            if hasattr(seller, 'commission_rate') and seller.commission_rate:
                return seller.commission_rate
            
            # Check seller tier for commission rate
            if hasattr(seller, 'loyalty_tier'):
                tier_rates = {
                    'bronze': Decimal('0.06'),  # 6%
                    'silver': Decimal('0.05'),  # 5%
                    'gold': Decimal('0.04'),    # 4%
                    'platinum': Decimal('0.03') # 3%
                }
                return tier_rates.get(seller.loyalty_tier, self.default_commission_rate)
            
            return self.default_commission_rate
            
        except Exception as e:
            logger.error(f"Error getting seller commission rate: {e}")
            return self.default_commission_rate
    
    def get_seller_commission_balance(self, seller: User) -> Decimal:
        """
        Get current commission balance for a seller
        """
        try:
            # Calculate total earned commissions
            total_earned = self.calculate_seller_commissions(seller)['total_commission']
            
            # Calculate total paid out (implement payout tracking)
            total_paid = self.get_total_payouts(seller)
            
            return total_earned - total_paid
            
        except Exception as e:
            logger.error(f"Error getting seller commission balance: {e}")
            return Decimal('0')
    
    def create_payout_record(self, seller: User, amount: Decimal, payment_method: str) -> Dict:
        """
        Create payout record (implement payout model)
        """
        try:
            # This would typically create a record in a Payout model
            # For now, return a mock record
            return {
                'id': f"payout_{seller.id}_{int(timezone.now().timestamp())}",
                'seller_id': seller.id,
                'amount': amount,
                'payment_method': payment_method,
                'status': 'pending',
                'created_at': timezone.now()
            }
            
        except Exception as e:
            logger.error(f"Error creating payout record: {e}")
            return {}
    
    def update_seller_commission_balance(self, seller: User, payout_amount: Decimal):
        """
        Update seller's commission balance after payout
        """
        try:
            # This would typically update a commission balance field
            # For now, just log the update
            logger.info(f"Updated commission balance for seller {seller.id}: -{payout_amount}")
            
        except Exception as e:
            logger.error(f"Error updating seller commission balance: {e}")
    
    def send_payout_notification(self, seller: User, amount: Decimal, payment_method: str):
        """
        Send payout notification to seller
        """
        try:
            email_service.send_commission_notification_email(
                user=seller,
                commission_amount=amount,
                period=f"Paiement {payment_method}"
            )
            
        except Exception as e:
            logger.error(f"Error sending payout notification: {e}")
    
    def get_total_payouts(self, seller: User) -> Decimal:
        """
        Get total payouts for a seller
        """
        try:
            # This would typically query a Payout model
            # For now, return 0
            return Decimal('0')
            
        except Exception as e:
            logger.error(f"Error getting total payouts: {e}")
            return Decimal('0')
    
    def calculate_commission_distribution(self, seller_commissions: List[Dict]) -> Dict:
        """
        Calculate commission distribution across ranges
        """
        try:
            ranges = {
                '0-1000': 0,
                '1000-5000': 0,
                '5000-10000': 0,
                '10000-25000': 0,
                '25000+': 0
            }
            
            for sc in seller_commissions:
                commission = sc['total_commission']
                if commission <= 1000:
                    ranges['0-1000'] += 1
                elif commission <= 5000:
                    ranges['1000-5000'] += 1
                elif commission <= 10000:
                    ranges['5000-10000'] += 1
                elif commission <= 25000:
                    ranges['10000-25000'] += 1
                else:
                    ranges['25000+'] += 1
            
            return ranges
            
        except Exception as e:
            logger.error(f"Error calculating commission distribution: {e}")
            return {}
    
    def calculate_commission_growth(self, period_days: int) -> Dict:
        """
        Calculate commission growth over time
        """
        try:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=period_days)
            
            # Calculate weekly growth
            weekly_data = []
            for i in range(0, period_days, 7):
                week_start = start_date + timedelta(days=i)
                week_end = min(week_start + timedelta(days=7), end_date)
                
                week_commission = self.calculate_all_commissions(week_start, week_end)['total_commission']
                weekly_data.append({
                    'week': week_start.strftime('%Y-%m-%d'),
                    'commission': week_commission
                })
            
            return {
                'weekly_data': weekly_data,
                'growth_rate': self.calculate_growth_rate(weekly_data)
            }
            
        except Exception as e:
            logger.error(f"Error calculating commission growth: {e}")
            return {'weekly_data': [], 'growth_rate': 0}
    
    def calculate_growth_rate(self, weekly_data: List[Dict]) -> float:
        """
        Calculate growth rate from weekly data
        """
        try:
            if len(weekly_data) < 2:
                return 0.0
            
            first_week = weekly_data[0]['commission']
            last_week = weekly_data[-1]['commission']
            
            if first_week == 0:
                return 0.0
            
            return ((last_week - first_week) / first_week) * 100
            
        except Exception as e:
            logger.error(f"Error calculating growth rate: {e}")
            return 0.0
    
    def generate_payout_recommendations(self, seller_commissions: List[Dict]) -> List[Dict]:
        """
        Generate payout recommendations
        """
        try:
            recommendations = []
            
            for sc in seller_commissions:
                if sc['payout_eligible']:
                    recommendations.append({
                        'seller_id': sc['seller_id'],
                        'seller_name': sc['seller_name'],
                        'recommended_amount': sc['total_commission'],
                        'reason': 'Above payout threshold',
                        'priority': 'high' if sc['total_commission'] > 5000 else 'medium'
                    })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating payout recommendations: {e}")
            return []
    
    # Default return methods
    def get_default_commission_result(self) -> Dict:
        """Get default commission result"""
        return {
            'order_id': None,
            'order_number': None,
            'seller_id': None,
            'seller_name': None,
            'total_amount': Decimal('0'),
            'commission_rate': self.default_commission_rate,
            'commission_amount': Decimal('0'),
            'net_amount': Decimal('0'),
            'calculation_date': timezone.now(),
            'status': 'error'
        }
    
    def get_default_seller_commission_result(self, seller: User) -> Dict:
        """Get default seller commission result"""
        return {
            'seller_id': seller.id,
            'seller_name': seller.get_full_name(),
            'period_start': timezone.now() - timedelta(days=30),
            'period_end': timezone.now(),
            'total_orders': 0,
            'total_sales': Decimal('0'),
            'total_commission': Decimal('0'),
            'average_commission_rate': 0,
            'commission_details': [],
            'payout_eligible': False,
            'calculation_date': timezone.now()
        }
    
    def get_default_all_commissions_result(self) -> Dict:
        """Get default all commissions result"""
        return {
            'period_start': timezone.now() - timedelta(days=30),
            'period_end': timezone.now(),
            'total_sellers': 0,
            'total_commission': Decimal('0'),
            'seller_commissions': [],
            'calculation_date': timezone.now()
        }
    
    def get_default_commission_statistics(self) -> Dict:
        """Get default commission statistics"""
        return {
            'period_days': 30,
            'period_start': timezone.now() - timedelta(days=30),
            'period_end': timezone.now(),
            'total_commission': Decimal('0'),
            'total_sellers': 0,
            'total_orders': 0,
            'total_sales': Decimal('0'),
            'average_commission_per_seller': Decimal('0'),
            'top_performers': [],
            'commission_distribution': {},
            'growth_data': {'weekly_data': [], 'growth_rate': 0},
            'payout_eligible_sellers': 0
        }


# Global commission manager instance
commission_manager = CommissionManager() 