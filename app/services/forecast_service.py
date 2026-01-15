"""
Forecast Service
================
Service for time series forecasting and climate scenario projections.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
import logging

from app.config import Config

logger = logging.getLogger(__name__)

# Try to import Prophet
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    logger.warning("Prophet not available. Forecast features will be limited.")


class ForecastService:
    """Service for climate forecasting"""
    
    def __init__(self):
        self.config = Config()
    
    def prophet_forecast(
        self,
        times: List[str],
        values: List[float],
        years: int = 5
    ) -> Dict[str, Any]:
        """
        Generate forecast using Prophet.
        """
        if not PROPHET_AVAILABLE:
            return self._simple_forecast(times, values, years)
        
        try:
            # Prepare data for Prophet
            df = pd.DataFrame({
                'ds': pd.to_datetime(times),
                'y': values
            })
            df = df.dropna()
            
            if len(df) < 24:  # Need at least 2 years of data
                return {'error': 'Insufficient data for forecasting'}
            
            # Create and fit model
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=False,
                daily_seasonality=False,
                changepoint_prior_scale=0.05
            )
            
            # Suppress Prophet logging
            import logging
            logging.getLogger('prophet').setLevel(logging.WARNING)
            logging.getLogger('cmdstanpy').setLevel(logging.WARNING)
            
            model.fit(df)
            
            # Make future dataframe
            future = model.make_future_dataframe(periods=years * 12, freq='MS')
            forecast = model.predict(future)
            
            # Get forecast period only
            forecast_only = forecast.tail(years * 12)
            
            # Calculate change rate
            historical_mean = df['y'].mean()
            forecast_mean = forecast_only['yhat'].mean()
            change_rate = ((forecast_mean - historical_mean) / historical_mean * 100) if historical_mean != 0 else 0
            
            # Determine trend direction
            if change_rate > 5:
                trend = 'increasing'
            elif change_rate < -5:
                trend = 'decreasing'
            else:
                trend = 'stable'
            
            return {
                'dates': forecast_only['ds'].dt.strftime('%Y-%m-%d').tolist(),
                'values': [round(float(v), 3) for v in forecast_only['yhat']],
                'lower': [round(float(v), 3) for v in forecast_only['yhat_lower']],
                'upper': [round(float(v), 3) for v in forecast_only['yhat_upper']],
                'trend': trend,
                'change_rate': round(float(change_rate), 2),
                'method': 'prophet'
            }
        except Exception as e:
            logger.error(f"Prophet forecast error: {str(e)}")
            return self._simple_forecast(times, values, years)
    
    def _simple_forecast(
        self,
        times: List[str],
        values: List[float],
        years: int = 5
    ) -> Dict[str, Any]:
        """
        Simple linear extrapolation forecast as fallback.
        """
        try:
            df = pd.DataFrame({
                'date': pd.to_datetime(times),
                'value': values
            })
            df = df.dropna()
            
            # Calculate annual means
            df['year'] = df['date'].dt.year
            annual = df.groupby('year')['value'].mean()
            
            # Linear regression
            x = np.arange(len(annual))
            y = annual.values
            
            slope, intercept = np.polyfit(x, y, 1)
            
            # Generate future dates
            last_date = df['date'].max()
            future_dates = pd.date_range(
                start=last_date + pd.DateOffset(months=1),
                periods=years * 12,
                freq='MS'
            )
            
            # Project values
            future_x = np.arange(len(annual), len(annual) + years)
            future_values = []
            for i in range(years * 12):
                year_offset = i // 12
                projected = intercept + slope * (len(annual) + year_offset)
                future_values.append(projected)
            
            # Calculate uncertainty (simple ± 10%)
            std = np.std(y)
            
            # Calculate change rate
            historical_mean = np.mean(y)
            forecast_mean = np.mean(future_values)
            change_rate = ((forecast_mean - historical_mean) / historical_mean * 100) if historical_mean != 0 else 0
            
            trend = 'increasing' if slope > 0 else ('decreasing' if slope < 0 else 'stable')
            
            return {
                'dates': future_dates.strftime('%Y-%m-%d').tolist(),
                'values': [round(float(v), 3) for v in future_values],
                'lower': [round(float(v - std), 3) for v in future_values],
                'upper': [round(float(v + std), 3) for v in future_values],
                'trend': trend,
                'change_rate': round(float(change_rate), 2),
                'method': 'linear_extrapolation'
            }
        except Exception as e:
            logger.error(f"Simple forecast error: {str(e)}")
            return {'error': str(e)}
    
    def generate_scenarios(
        self,
        times: List[str],
        values: List[float],
        target_year: int = 2050
    ) -> Dict[str, Any]:
        """
        Generate climate scenarios based on SSP pathways.
        """
        try:
            df = pd.DataFrame({
                'date': pd.to_datetime(times),
                'value': values
            })
            df = df.dropna()
            
            # Calculate annual means
            df['year'] = df['date'].dt.year
            annual = df.groupby('year')['value'].mean()
            
            # Get current value (recent average)
            recent_years = annual.tail(10)
            current_value = recent_years.mean()
            
            # Calculate trend
            x = np.arange(len(annual))
            y = annual.values
            slope, _ = np.polyfit(x, y, 1)
            
            # Years to target
            current_year = df['year'].max()
            years_ahead = target_year - current_year
            
            # Generate scenarios
            scenarios = {}
            for scenario_id, params in self.config.SSP_SCENARIOS.items():
                projected_slope = slope * params['multiplier']
                projected_change = projected_slope * years_ahead / 10  # Per decade
                future_value = current_value + projected_change
                
                scenarios[scenario_id] = {
                    'name': params['name'],
                    'description': params['description'],
                    'projected_change': round(float(projected_change), 3),
                    'future_value': round(float(future_value), 3),
                    'percent_change': round(float((future_value - current_value) / current_value * 100), 2) if current_value != 0 else 0,
                    'color': params['color']
                }
            
            return {
                'baseline': round(float(current_value), 3),
                'baseline_year': int(current_year),
                'target_year': target_year,
                'scenarios': scenarios
            }
        except Exception as e:
            logger.error(f"Scenario generation error: {str(e)}")
            return {'error': str(e)}


# Singleton instance
forecast_service = ForecastService()
