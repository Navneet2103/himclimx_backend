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

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    logger.warning("Prophet not available, will use Holt-Winters ETS.")

try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    ETS_AVAILABLE = True
except ImportError:
    ETS_AVAILABLE = False
    logger.warning("statsmodels not available, will use linear fallback.")


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
        Forecast pipeline: Prophet → Holt-Winters ETS → linear fallback.
        """
        if PROPHET_AVAILABLE:
            try:
                return self._prophet_forecast(times, values, years)
            except Exception as e:
                logger.warning(f"Prophet failed ({e}), falling back to ETS.")

        if ETS_AVAILABLE:
            try:
                return self._ets_forecast(times, values, years)
            except Exception as e:
                logger.warning(f"ETS failed ({e}), falling back to linear.")

        return self._simple_forecast(times, values, years)

    def _prophet_forecast(
        self,
        times: List[str],
        values: List[float],
        years: int = 5
    ) -> Dict[str, Any]:
        """Prophet forecast with improved climate-specific settings."""
        df = pd.DataFrame({'ds': pd.to_datetime(times), 'y': values}).dropna()

        if len(df) < 24:
            raise ValueError('Insufficient data for Prophet (need ≥ 24 months)')

        logging.getLogger('prophet').setLevel(logging.WARNING)
        logging.getLogger('cmdstanpy').setLevel(logging.WARNING)

        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False,
            changepoint_prior_scale=0.1,   # more responsive to climate shifts
            seasonality_prior_scale=10.0,
            seasonality_mode='additive',
            interval_width=0.95,
        )
        model.fit(df)

        future = model.make_future_dataframe(periods=years * 12, freq='MS')
        forecast = model.predict(future)
        fc = forecast.tail(years * 12)

        historical_mean = df['y'].tail(24).mean()
        forecast_mean   = fc['yhat'].mean()
        change_rate = ((forecast_mean - historical_mean) / historical_mean * 100) if historical_mean != 0 else 0

        return {
            'dates':       fc['ds'].dt.strftime('%Y-%m-%d').tolist(),
            'values':      [round(float(v), 3) for v in fc['yhat']],
            'lower':       [round(float(v), 3) for v in fc['yhat_lower']],
            'upper':       [round(float(v), 3) for v in fc['yhat_upper']],
            'trend':       'increasing' if change_rate > 3 else ('decreasing' if change_rate < -3 else 'stable'),
            'change_rate': round(float(change_rate), 2),
            'method':      'prophet',
        }

    def _ets_forecast(
        self,
        times: List[str],
        values: List[float],
        years: int = 5
    ) -> Dict[str, Any]:
        """
        Holt-Winters triple exponential smoothing (additive trend + additive seasonality).
        Well-suited for monthly climate data with regular annual cycles.
        """
        df = pd.DataFrame({'date': pd.to_datetime(times), 'value': values}).dropna()

        if len(df) < 24:
            raise ValueError('Insufficient data for ETS (need ≥ 24 months)')

        model = ExponentialSmoothing(
            df['value'].values,
            trend='add',
            seasonal='add',
            seasonal_periods=12,
            initialization_method='estimated',
        )
        fit = model.fit(optimized=True, use_brute=False)

        n = years * 12
        forecast_vals = fit.forecast(n)

        last_date    = df['date'].max()
        future_dates = pd.date_range(
            start=last_date + pd.DateOffset(months=1), periods=n, freq='MS'
        )

        # Growing uncertainty: σ * √h (standard ETS prediction interval)
        resid_std = float(np.std(fit.resid)) if len(fit.resid) > 0 else float(np.std(df['value'].values) * 0.05)
        lower = [round(float(v - 1.96 * resid_std * np.sqrt(i + 1)), 3) for i, v in enumerate(forecast_vals)]
        upper = [round(float(v + 1.96 * resid_std * np.sqrt(i + 1)), 3) for i, v in enumerate(forecast_vals)]

        historical_mean = float(df['value'].tail(24).mean())
        forecast_mean   = float(np.mean(forecast_vals))
        change_rate = ((forecast_mean - historical_mean) / historical_mean * 100) if historical_mean != 0 else 0

        return {
            'dates':       future_dates.strftime('%Y-%m-%d').tolist(),
            'values':      [round(float(v), 3) for v in forecast_vals],
            'lower':       lower,
            'upper':       upper,
            'trend':       'increasing' if change_rate > 3 else ('decreasing' if change_rate < -3 else 'stable'),
            'change_rate': round(float(change_rate), 2),
            'method':      'holt_winters_ets',
        }
    
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
