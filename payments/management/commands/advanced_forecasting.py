from django.core.management.base import BaseCommand
from django.utils import timezone
from payments.forecasting import FinancialForecastingService
from payments.models import FinancialForecast

class Command(BaseCommand):
    help = 'Generate advanced financial forecasts using machine learning models'

    def add_arguments(self, parser):
        parser.add_argument(
            '--revenue-forecast',
            action='store_true',
            help='Generate revenue forecast'
        )
        
        parser.add_argument(
            '--cash-flow-forecast',
            action='store_true',
            help='Generate cash flow forecast'
        )
        
        parser.add_argument(
            '--subscription-growth',
            action='store_true',
            help='Generate subscription growth forecast'
        )
        
        parser.add_argument(
            '--churn-prediction',
            action='store_true',
            help='Generate churn prediction'
        )
        
        parser.add_argument(
            '--seasonal-trends',
            action='store_true',
            help='Generate seasonal trends forecast'
        )
        
        parser.add_argument(
            '--all-forecasts',
            action='store_true',
            help='Generate all types of forecasts'
        )
        
        parser.add_argument(
            '--forecast-summary',
            action='store_true',
            help='Display summary of existing forecasts'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('=== Advanced Financial Forecasting ===')
        )
        
        service = FinancialForecastingService()
        
        if options['revenue_forecast'] or options['all_forecasts']:
            self.generate_revenue_forecast(service)
        
        if options['cash_flow_forecast'] or options['all_forecasts']:
            self.generate_cash_flow_forecast(service)
        
        if options['subscription_growth'] or options['all_forecasts']:
            self.generate_subscription_growth_forecast(service)
        
        if options['churn_prediction'] or options['all_forecasts']:
            self.generate_churn_prediction(service)
        
        if options['seasonal_trends'] or options['all_forecasts']:
            self.generate_seasonal_trends_forecast(service)
        
        if options['forecast_summary']:
            self.display_forecast_summary()
        
        if not any(options.values()):
            self.display_help()

    def generate_revenue_forecast(self, service):
        self.stdout.write("Generating revenue forecast...")
        
        try:
            forecast = service.generate_revenue_forecast(forecast_months=6)
            if forecast:
                self.stdout.write(f"  ✓ Revenue forecast created: {forecast.title}")
                self.stdout.write(f"     Confidence: {forecast.confidence_score}% ({forecast.accuracy_level})")
                self.stdout.write(f"     Predicted revenue: QAR {forecast.predicted_revenue:,.2f}")
                self.stdout.write(f"     Growth rate: {forecast.predicted_growth_rate}%")
                
                if forecast.risk_factors:
                    self.stdout.write(f"     Risk factors: {', '.join(forecast.risk_factors)}")
            else:
                self.stdout.write(self.style.ERROR("  ❌ Failed to generate revenue forecast"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ❌ Error: {str(e)}"))

    def generate_cash_flow_forecast(self, service):
        self.stdout.write("Generating cash flow forecast...")
        
        try:
            forecast = service.generate_cash_flow_forecast(forecast_months=3)
            if forecast:
                self.stdout.write(f"  ✓ Cash flow forecast created: {forecast.title}")
                self.stdout.write(f"     Confidence: {forecast.confidence_score}% ({forecast.accuracy_level})")
                
                forecast_data = forecast.forecast_data
                net_flow = forecast_data.get('total_net_flow', 0)
                self.stdout.write(f"     Predicted net cash flow: QAR {net_flow:,.2f}")
                
                if forecast.risk_factors:
                    self.stdout.write(f"     Risk factors: {', '.join(forecast.risk_factors)}")
            else:
                self.stdout.write(self.style.ERROR("  ❌ Failed to generate cash flow forecast"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ❌ Error: {str(e)}"))

    def generate_subscription_growth_forecast(self, service):
        self.stdout.write("Generating subscription growth forecast...")
        
        try:
            forecast = service.generate_subscription_growth_forecast(forecast_months=12)
            if forecast:
                self.stdout.write(f"  ✓ Subscription growth forecast created: {forecast.title}")
                self.stdout.write(f"     Confidence: {forecast.confidence_score}% ({forecast.accuracy_level})")
                self.stdout.write(f"     Growth rate: {forecast.predicted_growth_rate}%")
                
                forecast_data = forecast.forecast_data
                final_subs = forecast_data.get('total_predicted_subscriptions', 0)
                self.stdout.write(f"     Predicted subscriptions (12 months): {final_subs}")
                
                if forecast.risk_factors:
                    self.stdout.write(f"     Risk factors: {', '.join(forecast.risk_factors)}")
            else:
                self.stdout.write(self.style.ERROR("  ❌ Failed to generate subscription growth forecast"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ❌ Error: {str(e)}"))

    def generate_churn_prediction(self, service):
        self.stdout.write("Generating churn prediction...")
        
        try:
            forecast = service.generate_churn_prediction(prediction_months=3)
            if forecast:
                self.stdout.write(f"  ✓ Churn prediction created: {forecast.title}")
                self.stdout.write(f"     Confidence: {forecast.confidence_score}% ({forecast.accuracy_level})")
                
                forecast_data = forecast.forecast_data
                total_churn = forecast_data.get('total_predicted_churn', 0)
                at_risk = forecast_data.get('at_risk_customer_ids', [])
                revenue_loss = forecast_data.get('predicted_revenue_loss', 0)
                
                self.stdout.write(f"     Predicted churn (3 months): {total_churn} customers")
                self.stdout.write(f"     At-risk customers: {len(at_risk)}")
                self.stdout.write(f"     Predicted revenue loss: QAR {revenue_loss:,.2f}")
                
                if forecast.risk_factors:
                    self.stdout.write(f"     Risk factors: {', '.join(forecast.risk_factors)}")
            else:
                self.stdout.write(self.style.ERROR("  ❌ Failed to generate churn prediction"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ❌ Error: {str(e)}"))

    def generate_seasonal_trends_forecast(self, service):
        self.stdout.write("Generating seasonal trends forecast...")
        
        try:
            forecast = service.generate_seasonal_trends_forecast(forecast_months=12)
            if forecast:
                self.stdout.write(f"  ✓ Seasonal trends forecast created: {forecast.title}")
                self.stdout.write(f"     Confidence: {forecast.confidence_score}% ({forecast.accuracy_level})")
                
                forecast_data = forecast.forecast_data
                opportunities = forecast_data.get('opportunities', [])
                
                if opportunities:
                    self.stdout.write(f"     Opportunities: {', '.join(opportunities)}")
                
                if forecast.risk_factors:
                    self.stdout.write(f"     Risk factors: {', '.join(forecast.risk_factors)}")
            else:
                self.stdout.write(self.style.ERROR("  ❌ Failed to generate seasonal trends forecast"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ❌ Error: {str(e)}"))

    def display_forecast_summary(self):
        self.stdout.write("Financial forecast summary...")
        
        forecasts = FinancialForecast.objects.filter(is_active=True).order_by('-generated_date')
        
        if not forecasts:
            self.stdout.write("  No active forecasts found.")
            return
        
        self.stdout.write(f"\n  📊 Active Forecasts ({forecasts.count()}):")
        
        for forecast in forecasts:
            status_icon = "🟢" if forecast.accuracy_level == 'high' else "🟡" if forecast.accuracy_level == 'medium' else "🔴"
            
            self.stdout.write(f"     {status_icon} {forecast.title}")
            self.stdout.write(f"        Type: {forecast.get_forecast_type_display()}")
            self.stdout.write(f"        Confidence: {forecast.confidence_score}% ({forecast.accuracy_level})")
            self.stdout.write(f"        Period: {forecast.forecast_period_start} to {forecast.forecast_period_end}")
            self.stdout.write(f"        Generated: {forecast.generated_date.strftime('%Y-%m-%d %H:%M')}")
            
            if forecast.predicted_revenue:
                self.stdout.write(f"        Predicted Revenue: QAR {forecast.predicted_revenue:,.2f}")
            
            if forecast.predicted_growth_rate:
                self.stdout.write(f"        Growth Rate: {forecast.predicted_growth_rate}%")
            
            self.stdout.write("")  # Empty line for readability
        
        # Summary statistics
        high_confidence = forecasts.filter(accuracy_level='high').count()
        medium_confidence = forecasts.filter(accuracy_level='medium').count()
        low_confidence = forecasts.filter(accuracy_level='low').count()
        experimental = forecasts.filter(accuracy_level='experimental').count()
        
        self.stdout.write(f"  📈 Forecast Quality Distribution:")
        self.stdout.write(f"     High confidence: {high_confidence}")
        self.stdout.write(f"     Medium confidence: {medium_confidence}")
        self.stdout.write(f"     Low confidence: {low_confidence}")
        self.stdout.write(f"     Experimental: {experimental}")

    def display_help(self):
        self.stdout.write("\n Available commands:")
        self.stdout.write("  --revenue-forecast       Generate revenue forecast")
        self.stdout.write("  --cash-flow-forecast     Generate cash flow forecast")
        self.stdout.write("  --subscription-growth    Generate subscription growth forecast")
        self.stdout.write("  --churn-prediction       Generate churn prediction")
        self.stdout.write("  --seasonal-trends        Generate seasonal trends forecast")
        self.stdout.write("  --all-forecasts          Generate all forecasts")
        self.stdout.write("  --forecast-summary       Display forecast summary")
        self.stdout.write("\n Example usage:")
        self.stdout.write("  python manage.py advanced_forecasting --all-forecasts")
        self.stdout.write("  python manage.py advanced_forecasting --forecast-summary")