"""
Forecast Service
================
Service for time series forecasting using Prophet and other methods.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False

from app.services.data_service import data_service
from app.config import Config


class ForecastService:
    """Service for climate forecasting"""
    
    def __init__(self):
        self.config = Config()
        self.data_service = data_service
    
    def prophet_forecast(
        self,
        variable: str,
        region: Optional[str] = None,
        periods: int = 60,  # 5 years of monthly data
        yearly_seasonality: bool = True,
        include_history: bool = True,
        confidence_interval: float = 0.95
    ) -> Dict[str, Any]:
        """
        Generate forecast using Facebook Prophet.
        
        Args:
            variable: Climate variable
            region: Region code
            periods: Number of periods to forecast
            yearly_seasonality: Include yearly seasonality
            include_history: Include historical data in response
            confidence_interval: Confidence interval width
        """
        if not PROPHET_AVAILABLE:
            return self._simple_forecast(variable, region, periods)
        
        # Get time series data
        ts = self.data_service.get_regional_timeseries(
            variable=variable,
            region=region
        )
        
        # Prepare data for Prophet
        df = pd.DataFrame({
            'ds': pd.to_datetime(ts['data']['times']),
            'y': ts['data']['values']
        })
        df = df.dropna()
        
        if len(df) < 24:
            return {'error': 'Insufficient data for forecasting (need at least 24 months)'}
        
        try:
            # Initialize Prophet
            model = Prophet(
                yearly_seasonality=yearly_seasonality,
                weekly_seasonality=False,
                daily_seasonality=False,
                interval_width=confidence_interval,
                changepoint_prior_scale=0.05
            )
            
            # Fit model
            model.fit(df)
            
            # Create future dataframe
            future = model.make_future_dataframe(periods=periods, freq='MS')
            
            # Generate forecast
            forecast = model.predict(future)
            
            # Separate historical and future
            historical_end = df['ds'].max()
            
            # Prepare response
            result = {
                'variable': variable,
                'variable_info': self.config.CLIMATE_VARIABLES.get(variable, {}),
                'region': region,
                'model': 'prophet',
                'periods_forecast': periods,
                'confidence_interval': confidence_interval,
                'forecast_start': (historical_end + timedelta(days=1)).strftime('%Y-%m-%d'),
                'forecast_end': forecast['ds'].max().strftime('%Y-%m-%d'),
                'forecast': {
                    'dates': forecast[forecast['ds'] > historical_end]['ds'].dt.strftime('%Y-%m-%d').tolist(),
                    'values': forecast[forecast['ds'] > historical_end]['yhat'].round(3).tolist(),
                    'lower': forecast[forecast['ds'] > historical_end]['yhat_lower'].round(3).tolist(),
                    'upper': forecast[forecast['ds'] > historical_end]['yhat_upper'].round(3).tolist()
                },
                'components': {
                    'trend': {
                        'dates': forecast['ds'].dt.strftime('%Y-%m-%d').tolist(),
                        'values': forecast['trend'].round(3).tolist()
                    }
                },
                'metrics': {
                    'trend_direction': 'increasing' if forecast['trend'].iloc[-1] > forecast['trend'].iloc[0] else 'decreasing',
                    'trend_change': round(float(forecast['trend'].iloc[-1] - forecast['trend'].iloc[0]), 3),
                    'forecast_mean': round(float(forecast[forecast['ds'] > historical_end]['yhat'].mean()), 3),
                    'forecast_std': round(float(forecast[forecast['ds'] > historical_end]['yhat'].std()), 3)
                }
            }
            
            # Add yearly seasonality if available
            if 'yearly' in forecast.columns:
                result['components']['yearly'] = {
                    'values': forecast['yearly'].round(3).tolist()[:12]  # One year of seasonality
                }
            
            # Include history if requested
            if include_history:
                result['history'] = {
                    'dates': df['ds'].dt.strftime('%Y-%m-%d').tolist(),
                    'values': df['y'].round(3).tolist(),
                    'fitted': forecast[forecast['ds'] <= historical_end]['yhat'].round(3).tolist()
                }
            
            return result
            
        except Exception as e:
            return {'error': f'Prophet forecast failed: {str(e)}'}
    
    def _simple_forecast(
        self,
        variable: str,
        region: Optional[str],
        periods: int
    ) -> Dict[str, Any]:
        """
        Simple linear trend forecast when Prophet is not available.
        """
        from scipy import stats
        
        # Get annual time series
        ts = self.data_service.get_annual_timeseries(
            variable=variable,
            region=region,
            aggregation='mean'
        )
        
        years = np.array(ts['data']['years'])
        values = np.array(ts['data']['values'])
        
        # Remove None values
        mask = ~pd.isna(values)
        years = years[mask]
        values = values[mask].astype(float)
        
        # Linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(years, values)
        
        # Generate future years
        last_year = years[-1]
        future_years = np.arange(last_year + 1, last_year + 1 + (periods // 12) + 1)
        
        # Forecast
        forecast_values = slope * future_years + intercept
        
        # Simple confidence interval (based on std error)
        ci_width = 1.96 * std_err * np.sqrt(1 + 1/len(years) + (future_years - years.mean())**2 / np.sum((years - years.mean())**2))
        
        return {
            'variable': variable,
            'variable_info': self.config.CLIMATE_VARIABLES.get(variable, {}),
            'region': region,
            'model': 'linear_trend',
            'periods_forecast': len(future_years),
            'forecast': {
                'years': future_years.tolist(),
                'values': forecast_values.round(3).tolist(),
                'lower': (forecast_values - ci_width).round(3).tolist(),
                'upper': (forecast_values + ci_width).round(3).tolist()
            },
            'trend': {
                'slope': round(float(slope), 6),
                'intercept': round(float(intercept), 3),
                'r_squared': round(float(r_value ** 2), 4),
                'per_decade': round(float(slope * 10), 4)
            },
            'history': {
                'years': years.tolist(),
                'values': values.tolist()
            },
            'note': 'Using simple linear trend forecast (Prophet not available)'
        }
    
    def forecast_scenarios(
        self,
        variable: str,
        region: Optional[str] = None,
        target_year: int = 2050,
        base_period: tuple = (1995, 2014)
    ) -> Dict[str, Any]:
        """
        Generate forecasts under different SSP scenarios.
        """
        # Get baseline statistics
        baseline = self.data_service.get_annual_timeseries(
            variable=variable,
            region=region
        )
        
        years = np.array(baseline['data']['years'])
        values = np.array(baseline['data']['values'])
        
        # Filter to base period
        mask = (years >= base_period[0]) & (years <= base_period[1])
        base_values = values[mask]
        base_values = base_values[~pd.isna(base_values)]
        
        if len(base_values) == 0:
            return {'error': 'No data available for base period'}
        
        baseline_mean = float(np.mean(base_values))
        current_year = int(years[~pd.isna(values)][-1])
        
        # Calculate scenarios
        scenarios = {}
        for ssp_code, ssp_info in self.config.SSP_SCENARIOS.items():
            # Interpolate temperature increase
            if target_year <= 2050:
                temp_increase = ssp_info['temp_increase_2050'] * (target_year - current_year) / (2050 - current_year)
            else:
                temp_increase_2050 = ssp_info['temp_increase_2050']
                temp_increase_2100 = ssp_info['temp_increase_2100']
                temp_increase = temp_increase_2050 + (temp_increase_2100 - temp_increase_2050) * (target_year - 2050) / 50
            
            # Apply change based on variable type
            if variable in ['tmp', 'tmx', 'tmn', 'dtr']:
                # Direct temperature addition
                projected_value = baseline_mean + temp_increase
            elif variable == 'pre':
                # Precipitation: complex relationship, roughly +5% per degree for wet areas
                pct_change = temp_increase * 5  # 5% per degree
                projected_value = baseline_mean * (1 + pct_change / 100)
            elif variable in ['pet']:
                # Evapotranspiration increases with temperature
                pct_change = temp_increase * 3  # 3% per degree
                projected_value = baseline_mean * (1 + pct_change / 100)
            elif variable == 'frs':
                # Frost days decrease with warming
                pct_change = -temp_increase * 10  # -10% per degree
                projected_value = max(0, baseline_mean * (1 + pct_change / 100))
            else:
                # Default: small percentage change
                pct_change = temp_increase * 2
                projected_value = baseline_mean * (1 + pct_change / 100)
            
            scenarios[ssp_code] = {
                'name': ssp_info['name'],
                'description': ssp_info['description'],
                'color': ssp_info['color'],
                'temp_increase': round(temp_increase, 2),
                'projected_value': round(projected_value, 3),
                'change_from_baseline': round(projected_value - baseline_mean, 3),
                'change_percent': round((projected_value - baseline_mean) / baseline_mean * 100, 2) if baseline_mean != 0 else 0
            }
        
        return {
            'variable': variable,
            'variable_info': self.config.CLIMATE_VARIABLES.get(variable, {}),
            'region': region,
            'target_year': target_year,
            'base_period': f'{base_period[0]}-{base_period[1]}',
            'baseline_mean': round(baseline_mean, 3),
            'current_year': current_year,
            'scenarios': scenarios,
            'interpretation': self._interpret_scenarios(variable, scenarios, target_year)
        }
    
    def _interpret_scenarios(
        self,
        variable: str,
        scenarios: Dict,
        target_year: int
    ) -> str:
        """Generate interpretation of scenario projections"""
        var_info = self.config.CLIMATE_VARIABLES.get(variable, {})
        var_name = var_info.get('name', variable)
        unit = var_info.get('unit', '')
        
        ssp1_change = scenarios['SSP1']['change_from_baseline']
        ssp5_change = scenarios['SSP5']['change_from_baseline']
        
        return f"By {target_year}, {var_name} is projected to change between " \
               f"{ssp1_change:+.2f} {unit} (SSP1, sustainability) and " \
               f"{ssp5_change:+.2f} {unit} (SSP5, high emissions) compared to the baseline period."
    
    def get_forecast_summary(
        self,
        variables: List[str],
        region: Optional[str] = None,
        forecast_years: int = 5
    ) -> Dict[str, Any]:
        """
        Get forecast summary for multiple variables.
        """
        summaries = []
        
        for var in variables:
            try:
                forecast = self.prophet_forecast(
                    variable=var,
                    region=region,
                    periods=forecast_years * 12,
                    include_history=False
                )
                
                if 'error' not in forecast:
                    summaries.append({
                        'variable': var,
                        'variable_info': self.config.CLIMATE_VARIABLES.get(var, {}),
                        'forecast_mean': forecast.get('metrics', {}).get('forecast_mean'),
                        'trend_direction': forecast.get('metrics', {}).get('trend_direction'),
                        'trend_change': forecast.get('metrics', {}).get('trend_change')
                    })
            except Exception:
                continue
        
        return {
            'region': region,
            'forecast_years': forecast_years,
            'summaries': summaries
        }


# Singleton instance
forecast_service = ForecastService()
