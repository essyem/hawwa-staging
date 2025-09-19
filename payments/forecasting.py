import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
import pandas as pd
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q
from decimal import Decimal
from datetime import timedelta, date
import json
import logging

from .models import (
    FinancialForecast, Subscription, RecurringBilling, Currency
)
from bookings.models import Booking
from financial.models import Invoice

logger = logging.getLogger(__name__)

class FinancialForecastingService:
    """Advanced financial forecasting with machine learning models"""
    
    def __init__(self):
        self.confidence_thresholds = {
            'high': 90,
            'medium': 70,
            'low': 50,
            'experimental': 0
        }
    
    def generate_revenue_forecast(self, forecast_months=6):
        """Generate comprehensive revenue forecast using multiple models"""
        try:
            # Collect historical revenue data
            historical_data = self._collect_revenue_data(months_back=12)
            
            if len(historical_data) < 3:
                return self._create_basic_forecast('revenue', forecast_months)
            
            # Convert to pandas DataFrame for analysis
            df = pd.DataFrame(historical_data)
            df['month_numeric'] = range(len(df))
            
            # Apply multiple forecasting models
            linear_forecast = self._linear_regression_forecast(df, forecast_months)
            polynomial_forecast = self._polynomial_regression_forecast(df, forecast_months)
            moving_average_forecast = self._moving_average_forecast(df, forecast_months)
            seasonal_forecast = self._seasonal_forecast(df, forecast_months)
            
            # Ensemble forecast (weighted average of models)
            ensemble_forecast = self._create_ensemble_forecast([
                (linear_forecast, 0.3),
                (polynomial_forecast, 0.25),
                (moving_average_forecast, 0.25),
                (seasonal_forecast, 0.2)
            ])
            
            # Calculate confidence score based on model agreement
            confidence = self._calculate_forecast_confidence([
                linear_forecast, polynomial_forecast, moving_average_forecast, seasonal_forecast
            ])
            
            # Identify risk factors
            risk_factors = self._identify_revenue_risks(df)
            
            # Create forecast record
            forecast = FinancialForecast.objects.create(
                forecast_type='revenue',
                title=f'{forecast_months}-Month Revenue Forecast',
                description='Advanced revenue prediction using ensemble machine learning models',
                forecast_period_start=timezone.now().date(),
                forecast_period_end=(timezone.now() + timedelta(days=30 * forecast_months)).date(),
                historical_data={
                    'monthly_revenue': [float(row['revenue']) for row in historical_data],
                    'months': [row['month'] for row in historical_data],
                    'data_points': len(historical_data)
                },
                forecast_data={
                    'linear_model': linear_forecast,
                    'polynomial_model': polynomial_forecast,
                    'moving_average': moving_average_forecast,
                    'seasonal_model': seasonal_forecast,
                    'ensemble_forecast': ensemble_forecast,
                    'monthly_predictions': ensemble_forecast['monthly_values']
                },
                confidence_score=Decimal(str(confidence)),
                accuracy_level=self._get_accuracy_level(confidence),
                predicted_revenue=Decimal(str(sum(ensemble_forecast['monthly_values']))),
                predicted_growth_rate=Decimal(str(ensemble_forecast.get('growth_rate', 0))),
                risk_factors=risk_factors,
                algorithm_used='Ensemble ML (Linear, Polynomial, MA, Seasonal)',
                data_points_used=len(historical_data)
            )
            
            return forecast
            
        except Exception as e:
            logger.error(f"Failed to generate revenue forecast: {str(e)}")
            return self._create_basic_forecast('revenue', forecast_months)
    
    def generate_cash_flow_forecast(self, forecast_months=3):
        """Generate cash flow forecast including receivables and payables"""
        try:
            # Collect cash flow data
            cash_flow_data = self._collect_cash_flow_data(months_back=6)
            
            # Predict future cash flows
            inflow_forecast = self._forecast_cash_inflows(cash_flow_data, forecast_months)
            outflow_forecast = self._forecast_cash_outflows(cash_flow_data, forecast_months)
            
            # Calculate net cash flow
            net_cash_flow = []
            for i in range(forecast_months):
                net_flow = inflow_forecast[i] - outflow_forecast[i]
                net_cash_flow.append(net_flow)
            
            # Identify cash flow risks
            risk_factors = []
            if any(flow < 0 for flow in net_cash_flow):
                risk_factors.append("Negative cash flow periods predicted")
            if max(net_cash_flow) - min(net_cash_flow) > sum(net_cash_flow) * 0.5:
                risk_factors.append("High cash flow volatility")
            
            confidence = 75.0  # Base confidence for cash flow forecasts
            
            forecast = FinancialForecast.objects.create(
                forecast_type='cash_flow',
                title=f'{forecast_months}-Month Cash Flow Forecast',
                description='Predicted cash inflows and outflows based on historical patterns',
                forecast_period_start=timezone.now().date(),
                forecast_period_end=(timezone.now() + timedelta(days=30 * forecast_months)).date(),
                historical_data=cash_flow_data,
                forecast_data={
                    'inflow_forecast': inflow_forecast,
                    'outflow_forecast': outflow_forecast,
                    'net_cash_flow': net_cash_flow,
                    'total_net_flow': sum(net_cash_flow)
                },
                confidence_score=Decimal(str(confidence)),
                accuracy_level=self._get_accuracy_level(confidence),
                risk_factors=risk_factors,
                algorithm_used='Cash Flow Pattern Analysis',
                data_points_used=len(cash_flow_data.get('monthly_data', []))
            )
            
            return forecast
            
        except Exception as e:
            logger.error(f"Failed to generate cash flow forecast: {str(e)}")
            return None
    
    def generate_subscription_growth_forecast(self, forecast_months=12):
        """Forecast subscription growth and churn patterns"""
        try:
            # Collect subscription metrics
            subscription_data = self._collect_subscription_metrics(months_back=12)
            
            if not subscription_data:
                return self._create_basic_forecast('subscription_growth', forecast_months)
            
            # Analyze growth patterns
            growth_analysis = self._analyze_subscription_growth(subscription_data)
            churn_analysis = self._analyze_churn_patterns(subscription_data)
            
            # Forecast future subscription numbers
            future_subscriptions = []
            current_subscriptions = subscription_data[-1]['active_subscriptions']
            monthly_growth_rate = growth_analysis['average_growth_rate']
            monthly_churn_rate = churn_analysis['average_churn_rate']
            
            for month in range(forecast_months):
                # Apply growth and churn
                new_subs = int(current_subscriptions * (monthly_growth_rate / 100))
                churned_subs = int(current_subscriptions * (monthly_churn_rate / 100))
                current_subscriptions = current_subscriptions + new_subs - churned_subs
                future_subscriptions.append(max(0, current_subscriptions))
            
            # Calculate revenue impact
            avg_subscription_value = subscription_data[-1].get('avg_subscription_value', 0)
            predicted_revenue = sum(subs * avg_subscription_value for subs in future_subscriptions)
            
            # Identify growth risks
            risk_factors = []
            if monthly_churn_rate > 5:
                risk_factors.append("High churn rate detected")
            if monthly_growth_rate < 0:
                risk_factors.append("Negative growth trend")
            if len(subscription_data) < 6:
                risk_factors.append("Limited historical data")
            
            confidence = max(50, 80 - (monthly_churn_rate * 2))  # Lower confidence with higher churn
            
            forecast = FinancialForecast.objects.create(
                forecast_type='subscription_growth',
                title=f'{forecast_months}-Month Subscription Growth Forecast',
                description='Predicted subscription growth based on historical trends and churn analysis',
                forecast_period_start=timezone.now().date(),
                forecast_period_end=(timezone.now() + timedelta(days=30 * forecast_months)).date(),
                historical_data={
                    'subscription_metrics': subscription_data,
                    'growth_analysis': growth_analysis,
                    'churn_analysis': churn_analysis
                },
                forecast_data={
                    'monthly_subscriptions': future_subscriptions,
                    'total_predicted_subscriptions': future_subscriptions[-1],
                    'predicted_revenue_impact': predicted_revenue,
                    'growth_rate': monthly_growth_rate,
                    'churn_rate': monthly_churn_rate
                },
                confidence_score=Decimal(str(confidence)),
                accuracy_level=self._get_accuracy_level(confidence),
                predicted_revenue=Decimal(str(predicted_revenue)) if predicted_revenue else None,
                predicted_growth_rate=Decimal(str(monthly_growth_rate)),
                risk_factors=risk_factors,
                algorithm_used='Growth & Churn Analysis',
                data_points_used=len(subscription_data)
            )
            
            return forecast
            
        except Exception as e:
            logger.error(f"Failed to generate subscription growth forecast: {str(e)}")
            return None
    
    def generate_churn_prediction(self, prediction_months=3):
        """Predict customer churn using behavioral analysis"""
        try:
            # Analyze historical churn patterns
            churn_data = self._analyze_detailed_churn_patterns()
            
            # Identify high-risk customers
            at_risk_customers = self._identify_at_risk_customers()
            
            # Predict future churn
            churn_predictions = []
            for month in range(prediction_months):
                predicted_churn = self._predict_monthly_churn(churn_data, month)
                churn_predictions.append(predicted_churn)
            
            # Calculate financial impact
            avg_customer_value = self._calculate_average_customer_value()
            predicted_revenue_loss = sum(pred['count'] * avg_customer_value for pred in churn_predictions)
            
            # Identify churn risk factors
            risk_factors = [
                "Payment failures",
                "Low service engagement",
                "Support ticket volume",
                "Subscription downgrades",
                "Infrequent platform usage"
            ]
            
            confidence = 72.0  # Base confidence for churn prediction
            
            forecast = FinancialForecast.objects.create(
                forecast_type='churn_prediction',
                title=f'{prediction_months}-Month Churn Prediction',
                description='Predicted customer churn based on behavioral analysis and historical patterns',
                forecast_period_start=timezone.now().date(),
                forecast_period_end=(timezone.now() + timedelta(days=30 * prediction_months)).date(),
                historical_data={
                    'churn_patterns': churn_data,
                    'at_risk_customers': len(at_risk_customers),
                    'avg_customer_value': avg_customer_value
                },
                forecast_data={
                    'monthly_churn_predictions': churn_predictions,
                    'total_predicted_churn': sum(pred['count'] for pred in churn_predictions),
                    'at_risk_customer_ids': [customer['id'] for customer in at_risk_customers[:50]],
                    'predicted_revenue_loss': predicted_revenue_loss
                },
                confidence_score=Decimal(str(confidence)),
                accuracy_level=self._get_accuracy_level(confidence),
                risk_factors=risk_factors,
                algorithm_used='Behavioral Churn Analysis',
                data_points_used=len(churn_data.get('monthly_churn', []))
            )
            
            return forecast
            
        except Exception as e:
            logger.error(f"Failed to generate churn prediction: {str(e)}")
            return None
    
    def generate_seasonal_trends_forecast(self, forecast_months=12):
        """Analyze and forecast seasonal business trends"""
        try:
            # Collect seasonal data
            seasonal_data = self._collect_seasonal_data()
            
            # Analyze seasonal patterns
            seasonal_patterns = self._analyze_seasonal_patterns(seasonal_data)
            
            # Generate seasonal forecast
            seasonal_forecast = self._generate_seasonal_predictions(seasonal_patterns, forecast_months)
            
            # Identify seasonal risks and opportunities
            risk_factors = []
            opportunities = []
            
            for month_data in seasonal_forecast['monthly_predictions']:
                if month_data['variance'] < -20:
                    risk_factors.append(f"Low season in {month_data['month']}")
                elif month_data['variance'] > 20:
                    opportunities.append(f"High season in {month_data['month']}")
            
            confidence = 65.0  # Seasonal forecasts have medium confidence
            
            forecast = FinancialForecast.objects.create(
                forecast_type='seasonal_trends',
                title=f'{forecast_months}-Month Seasonal Trends Forecast',
                description='Seasonal business patterns and revenue predictions',
                forecast_period_start=timezone.now().date(),
                forecast_period_end=(timezone.now() + timedelta(days=30 * forecast_months)).date(),
                historical_data=seasonal_data,
                forecast_data={
                    'seasonal_patterns': seasonal_patterns,
                    'seasonal_forecast': seasonal_forecast,
                    'opportunities': opportunities
                },
                confidence_score=Decimal(str(confidence)),
                accuracy_level=self._get_accuracy_level(confidence),
                risk_factors=risk_factors,
                algorithm_used='Seasonal Pattern Analysis',
                data_points_used=len(seasonal_data.get('monthly_data', []))
            )
            
            return forecast
            
        except Exception as e:
            logger.error(f"Failed to generate seasonal trends forecast: {str(e)}")
            return None
    
    # Helper methods for data collection and analysis
    
    def _collect_revenue_data(self, months_back=12):
        """Collect historical revenue data"""
        data = []
        current_date = timezone.now().replace(day=1)
        
        for i in range(months_back):
            month_start = current_date - timedelta(days=30 * i)
            month_end = month_start + timedelta(days=30)
            
            # Revenue from completed billing
            billing_revenue = RecurringBilling.objects.filter(
                status='completed',
                processed_at__gte=month_start,
                processed_at__lt=month_end
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            # Revenue from invoices
            invoice_revenue = Invoice.objects.filter(
                status='paid',
                paid_date__gte=month_start,
                paid_date__lt=month_end
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            total_revenue = float(billing_revenue) + float(invoice_revenue)
            
            data.append({
                'month': month_start.strftime('%Y-%m'),
                'revenue': total_revenue,
                'billing_revenue': float(billing_revenue),
                'invoice_revenue': float(invoice_revenue)
            })
        
        return list(reversed(data))  # Chronological order
    
    def _linear_regression_forecast(self, df, forecast_months):
        """Generate linear regression forecast"""
        if len(df) < 2:
            return {'monthly_values': [0] * forecast_months, 'growth_rate': 0}
        
        X = df[['month_numeric']].values
        y = df['revenue'].values
        
        model = LinearRegression()
        model.fit(X, y)
        
        # Predict future months
        future_months = range(len(df), len(df) + forecast_months)
        future_X = np.array(future_months).reshape(-1, 1)
        predictions = model.predict(future_X)
        
        # Calculate growth rate
        if len(y) > 1:
            growth_rate = ((y[-1] - y[0]) / y[0] * 100) if y[0] != 0 else 0
        else:
            growth_rate = 0
        
        return {
            'monthly_values': [max(0, pred) for pred in predictions],
            'growth_rate': growth_rate,
            'r_squared': model.score(X, y) if len(X) > 1 else 0
        }
    
    def _polynomial_regression_forecast(self, df, forecast_months):
        """Generate polynomial regression forecast"""
        if len(df) < 3:
            return self._linear_regression_forecast(df, forecast_months)
        
        X = df[['month_numeric']].values
        y = df['revenue'].values
        
        # Use degree 2 polynomial
        poly_features = PolynomialFeatures(degree=2)
        X_poly = poly_features.fit_transform(X)
        
        model = LinearRegression()
        model.fit(X_poly, y)
        
        # Predict future months
        future_months = range(len(df), len(df) + forecast_months)
        future_X = np.array(future_months).reshape(-1, 1)
        future_X_poly = poly_features.transform(future_X)
        predictions = model.predict(future_X_poly)
        
        return {
            'monthly_values': [max(0, pred) for pred in predictions],
            'r_squared': model.score(X_poly, y)
        }
    
    def _moving_average_forecast(self, df, forecast_months):
        """Generate moving average forecast"""
        if len(df) < 3:
            avg_revenue = df['revenue'].mean() if len(df) > 0 else 0
            return {'monthly_values': [avg_revenue] * forecast_months}
        
        # Use 3-month moving average
        window_size = min(3, len(df))
        recent_avg = df['revenue'].tail(window_size).mean()
        
        return {'monthly_values': [recent_avg] * forecast_months}
    
    def _seasonal_forecast(self, df, forecast_months):
        """Generate seasonal forecast based on monthly patterns"""
        if len(df) < 12:
            return self._moving_average_forecast(df, forecast_months)
        
        # Calculate monthly seasonal factors
        monthly_factors = {}
        for _, row in df.iterrows():
            month = pd.to_datetime(row['month']).month
            if month not in monthly_factors:
                monthly_factors[month] = []
            monthly_factors[month].append(row['revenue'])
        
        # Calculate average for each month
        for month in monthly_factors:
            monthly_factors[month] = np.mean(monthly_factors[month])
        
        # Generate forecast
        base_revenue = df['revenue'].mean()
        predictions = []
        current_month = timezone.now().month
        
        for i in range(forecast_months):
            month = ((current_month + i - 1) % 12) + 1
            seasonal_factor = monthly_factors.get(month, 1)
            prediction = base_revenue * (seasonal_factor / base_revenue) if base_revenue != 0 else 0
            predictions.append(max(0, prediction))
        
        return {'monthly_values': predictions}
    
    def _create_ensemble_forecast(self, model_forecasts):
        """Create weighted ensemble forecast"""
        total_weight = sum(weight for _, weight in model_forecasts)
        ensemble_values = []
        
        # Get the length of predictions (assuming all models have same length)
        forecast_length = len(model_forecasts[0][0]['monthly_values'])
        
        for i in range(forecast_length):
            weighted_sum = 0
            for forecast, weight in model_forecasts:
                if i < len(forecast['monthly_values']):
                    weighted_sum += forecast['monthly_values'][i] * weight
            
            ensemble_values.append(weighted_sum / total_weight)
        
        # Calculate ensemble growth rate
        growth_rates = [forecast.get('growth_rate', 0) for forecast, _ in model_forecasts if 'growth_rate' in forecast]
        avg_growth_rate = np.mean(growth_rates) if growth_rates else 0
        
        return {
            'monthly_values': ensemble_values,
            'growth_rate': avg_growth_rate
        }
    
    def _calculate_forecast_confidence(self, forecasts):
        """Calculate confidence based on model agreement"""
        if len(forecasts) < 2:
            return 60.0
        
        # Calculate variance between models
        all_predictions = [f['monthly_values'] for f in forecasts if 'monthly_values' in f]
        if not all_predictions:
            return 50.0
        
        # Calculate coefficient of variation for each month
        variations = []
        min_length = min(len(pred) for pred in all_predictions)
        
        for i in range(min_length):
            month_predictions = [pred[i] for pred in all_predictions]
            if len(month_predictions) > 1:
                std_dev = np.std(month_predictions)
                mean_pred = np.mean(month_predictions)
                cv = (std_dev / mean_pred) if mean_pred != 0 else 1
                variations.append(cv)
        
        # Convert variation to confidence (lower variation = higher confidence)
        avg_variation = np.mean(variations) if variations else 0.5
        confidence = max(50, 90 - (avg_variation * 100))
        
        return min(95, confidence)
    
    def _get_accuracy_level(self, confidence):
        """Convert confidence score to accuracy level"""
        if confidence >= 90:
            return 'high'
        elif confidence >= 70:
            return 'medium'
        elif confidence >= 50:
            return 'low'
        else:
            return 'experimental'
    
    def _identify_revenue_risks(self, df):
        """Identify potential revenue risks"""
        risks = []
        
        if len(df) < 3:
            risks.append("Insufficient historical data")
            return risks
        
        # Check for declining trend
        recent_revenue = df['revenue'].tail(3).mean()
        earlier_revenue = df['revenue'].head(3).mean()
        
        if recent_revenue < earlier_revenue * 0.9:
            risks.append("Declining revenue trend")
        
        # Check for high volatility
        cv = df['revenue'].std() / df['revenue'].mean() if df['revenue'].mean() != 0 else 0
        if cv > 0.3:
            risks.append("High revenue volatility")
        
        # Check for seasonal dependency
        if len(df) >= 12:
            monthly_std = df.groupby(df.index % 12)['revenue'].std().mean()
            if monthly_std > df['revenue'].mean() * 0.2:
                risks.append("High seasonal dependency")
        
        return risks
    
    def _create_basic_forecast(self, forecast_type, forecast_months):
        """Create basic forecast when insufficient data"""
        # Get current metrics as baseline
        current_subscriptions = Subscription.objects.filter(status__in=['active', 'trial']).count()
        avg_subscription_value = Subscription.objects.filter(
            status__in=['active', 'trial']
        ).aggregate(avg=Avg('base_price'))['avg'] or Decimal('0')
        
        basic_monthly_revenue = float(current_subscriptions * avg_subscription_value)
        
        forecast = FinancialForecast.objects.create(
            forecast_type=forecast_type,
            title=f'Basic {forecast_type.replace("_", " ").title()} Forecast',
            description='Basic forecast due to limited historical data',
            forecast_period_start=timezone.now().date(),
            forecast_period_end=(timezone.now() + timedelta(days=30 * forecast_months)).date(),
            historical_data={'note': 'Insufficient data for advanced modeling'},
            forecast_data={
                'monthly_values': [basic_monthly_revenue] * forecast_months,
                'total_predicted': basic_monthly_revenue * forecast_months
            },
            confidence_score=Decimal('45.00'),
            accuracy_level='experimental',
            predicted_revenue=Decimal(str(basic_monthly_revenue * forecast_months)),
            risk_factors=['Limited historical data', 'Basic projection model'],
            algorithm_used='Basic Linear Projection',
            data_points_used=1
        )
        
        return forecast
    
    # Placeholder methods for additional forecasting features
    
    def _collect_cash_flow_data(self, months_back):
        """Placeholder for cash flow data collection"""
        return {'monthly_data': [], 'note': 'Cash flow analysis placeholder'}
    
    def _forecast_cash_inflows(self, data, months):
        """Placeholder for cash inflow forecasting"""
        return [1000] * months  # Mock data
    
    def _forecast_cash_outflows(self, data, months):
        """Placeholder for cash outflow forecasting"""
        return [800] * months  # Mock data
    
    def _collect_subscription_metrics(self, months_back):
        """Collect subscription growth metrics"""
        data = []
        current_date = timezone.now().replace(day=1)
        
        for i in range(months_back):
            month_start = current_date - timedelta(days=30 * i)
            month_end = month_start + timedelta(days=30)
            
            active_subs = Subscription.objects.filter(
                created_at__lt=month_end,
                status__in=['active', 'trial']
            ).count()
            
            new_subs = Subscription.objects.filter(
                created_at__gte=month_start,
                created_at__lt=month_end
            ).count()
            
            cancelled_subs = Subscription.objects.filter(
                updated_at__gte=month_start,
                updated_at__lt=month_end,
                status='cancelled'
            ).count()
            
            avg_value = Subscription.objects.filter(
                created_at__lt=month_end,
                status__in=['active', 'trial']
            ).aggregate(avg=Avg('base_price'))['avg'] or Decimal('0')
            
            data.append({
                'month': month_start.strftime('%Y-%m'),
                'active_subscriptions': active_subs,
                'new_subscriptions': new_subs,
                'cancelled_subscriptions': cancelled_subs,
                'avg_subscription_value': float(avg_value)
            })
        
        return list(reversed(data))
    
    def _analyze_subscription_growth(self, data):
        """Analyze subscription growth patterns"""
        if len(data) < 2:
            return {'average_growth_rate': 0}
        
        growth_rates = []
        for i in range(1, len(data)):
            prev_subs = data[i-1]['active_subscriptions']
            curr_subs = data[i]['active_subscriptions']
            
            if prev_subs > 0:
                growth_rate = ((curr_subs - prev_subs) / prev_subs) * 100
                growth_rates.append(growth_rate)
        
        return {
            'average_growth_rate': np.mean(growth_rates) if growth_rates else 0,
            'growth_rates': growth_rates
        }
    
    def _analyze_churn_patterns(self, data):
        """Analyze subscription churn patterns"""
        if len(data) < 2:
            return {'average_churn_rate': 0}
        
        churn_rates = []
        for month_data in data:
            active = month_data['active_subscriptions']
            cancelled = month_data['cancelled_subscriptions']
            
            if active > 0:
                churn_rate = (cancelled / active) * 100
                churn_rates.append(churn_rate)
        
        return {
            'average_churn_rate': np.mean(churn_rates) if churn_rates else 0,
            'churn_rates': churn_rates
        }
    
    def _analyze_detailed_churn_patterns(self):
        """Placeholder for detailed churn analysis"""
        return {'monthly_churn': [], 'churn_reasons': {}}
    
    def _identify_at_risk_customers(self):
        """Placeholder for at-risk customer identification"""
        return []
    
    def _predict_monthly_churn(self, churn_data, month_offset):
        """Placeholder for monthly churn prediction"""
        return {'count': 2, 'reasons': ['payment_failure', 'dissatisfaction']}
    
    def _calculate_average_customer_value(self):
        """Calculate average customer lifetime value"""
        avg_subscription = Subscription.objects.filter(
            status__in=['active', 'trial']
        ).aggregate(avg=Avg('base_price'))['avg'] or Decimal('0')
        
        return float(avg_subscription) * 12  # Assume 12-month lifetime
    
    def _collect_seasonal_data(self):
        """Placeholder for seasonal data collection"""
        return {'monthly_data': [], 'seasonal_factors': {}}
    
    def _analyze_seasonal_patterns(self, data):
        """Placeholder for seasonal pattern analysis"""
        return {'monthly_factors': {}}
    
    def _generate_seasonal_predictions(self, patterns, months):
        """Placeholder for seasonal predictions"""
        return {
            'monthly_predictions': [
                {'month': f'Month {i+1}', 'variance': 0} 
                for i in range(months)
            ]
        }