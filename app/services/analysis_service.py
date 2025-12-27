"""
Analysis Service
================
Service for statistical analysis, trend detection, anomaly detection,
and seasonal decomposition.
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    from statsmodels.tsa.seasonal import seasonal_decompose
    from statsmodels.tsa.stattools import adfuller
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False

from app.services.data_service import data_service
from app.config import Config


class AnalysisService:
    """Service for climate data analysis"""
    
    def __init__(self):
        self.config = Config()
        self.data_service = data_service
    
    def compute_trend(
        self,
        variable: str,
        region: Optional[str] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        method: str = 'linear'
    ) -> Dict[str, Any]:
        """
        Compute trend analysis for a variable.
        
        Args:
            variable: Climate variable code
            region: Region code (optional)
            start_year: Start year
            end_year: End year
            method: Trend method ('linear', 'mann_kendall')
        
        Returns:
            Trend analysis results
        """
        # Get annual time series
        ts = self.data_service.get_annual_timeseries(
            variable=variable,
            region=region,
            aggregation='mean'
        )
        
        years = np.array(ts['data']['years'])
        values = np.array(ts['data']['values'])
        
        # Remove None/NaN values
        mask = ~pd.isna(values)
        years = years[mask]
        values = values[mask].astype(float)
        
        if len(years) < 3:
            return {'error': 'Insufficient data for trend analysis'}
        
        # Filter by year range
        if start_year:
            mask = years >= start_year
            years = years[mask]
            values = values[mask]
        if end_year:
            mask = years <= end_year
            years = years[mask]
            values = values[mask]
        
        # Linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(years, values)
        
        # Calculate trend line
        trend_line = slope * years + intercept
        
        # Calculate per-decade change
        per_decade = slope * 10
        
        # Calculate percent change
        start_value = trend_line[0]
        end_value = trend_line[-1]
        percent_change = ((end_value - start_value) / abs(start_value)) * 100 if start_value != 0 else 0
        
        # Mann-Kendall test (if requested and available)
        mk_result = None
        if method == 'mann_kendall':
            mk_result = self._mann_kendall_test(values)
        
        result = {
            'variable': variable,
            'variable_info': self.config.CLIMATE_VARIABLES.get(variable, {}),
            'region': region,
            'time_range': {
                'start': int(years[0]),
                'end': int(years[-1]),
                'n_years': len(years)
            },
            'linear_trend': {
                'slope': round(float(slope), 6),
                'intercept': round(float(intercept), 3),
                'r_squared': round(float(r_value ** 2), 4),
                'p_value': round(float(p_value), 6),
                'std_error': round(float(std_err), 6),
                'per_decade': round(float(per_decade), 4),
                'percent_change': round(float(percent_change), 2),
                'significant': p_value < 0.05
            },
            'data': {
                'years': years.tolist(),
                'observed': values.tolist(),
                'trend_line': trend_line.tolist()
            },
            'interpretation': self._interpret_trend(slope, p_value, variable)
        }
        
        if mk_result:
            result['mann_kendall'] = mk_result
        
        return result
    
    def _mann_kendall_test(self, values: np.ndarray) -> Dict[str, Any]:
        """Perform Mann-Kendall trend test"""
        n = len(values)
        
        # Calculate S statistic
        s = 0
        for i in range(n - 1):
            for j in range(i + 1, n):
                s += np.sign(values[j] - values[i])
        
        # Calculate variance
        unique, counts = np.unique(values, return_counts=True)
        
        var_s = (n * (n - 1) * (2 * n + 5)) / 18
        
        # Adjust for ties
        for count in counts:
            if count > 1:
                var_s -= count * (count - 1) * (2 * count + 5) / 18
        
        # Calculate Z statistic
        if s > 0:
            z = (s - 1) / np.sqrt(var_s)
        elif s < 0:
            z = (s + 1) / np.sqrt(var_s)
        else:
            z = 0
        
        # Two-tailed p-value
        p_value = 2 * (1 - stats.norm.cdf(abs(z)))
        
        # Determine trend direction
        if s > 0:
            trend = 'increasing'
        elif s < 0:
            trend = 'decreasing'
        else:
            trend = 'no trend'
        
        return {
            's_statistic': int(s),
            'z_statistic': round(float(z), 4),
            'p_value': round(float(p_value), 6),
            'trend': trend,
            'significant': p_value < 0.05
        }
    
    def _interpret_trend(self, slope: float, p_value: float, variable: str) -> str:
        """Generate human-readable trend interpretation"""
        var_info = self.config.CLIMATE_VARIABLES.get(variable, {})
        var_name = var_info.get('name', variable)
        unit = var_info.get('unit', '')
        
        significance = "statistically significant" if p_value < 0.05 else "not statistically significant"
        
        if abs(slope) < 0.001:
            direction = "relatively stable"
        elif slope > 0:
            direction = "increasing"
        else:
            direction = "decreasing"
        
        per_decade = abs(slope * 10)
        
        return f"{var_name} shows a {direction} trend ({significance}, p={p_value:.4f}). " \
               f"The rate of change is approximately {per_decade:.3f} {unit} per decade."
    
    def detect_anomalies(
        self,
        variable: str,
        region: Optional[str] = None,
        method: str = 'zscore',
        threshold: float = 2.0,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Detect anomalies in climate data.
        
        Args:
            variable: Climate variable
            region: Region code
            method: Detection method ('zscore', 'iqr', 'isolation_forest')
            threshold: Anomaly threshold (default 2.0 for z-score)
        """
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
        
        # Filter by year
        if start_year:
            mask = years >= start_year
            years, values = years[mask], values[mask]
        if end_year:
            mask = years <= end_year
            years, values = years[mask], values[mask]
        
        anomalies = []
        anomaly_mask = np.zeros(len(values), dtype=bool)
        
        if method == 'zscore':
            # Z-score method
            mean_val = np.mean(values)
            std_val = np.std(values)
            z_scores = (values - mean_val) / std_val if std_val > 0 else np.zeros_like(values)
            anomaly_mask = np.abs(z_scores) > threshold
            
            for i, is_anomaly in enumerate(anomaly_mask):
                if is_anomaly:
                    anomalies.append({
                        'year': int(years[i]),
                        'value': round(float(values[i]), 3),
                        'z_score': round(float(z_scores[i]), 3),
                        'type': 'high' if z_scores[i] > 0 else 'low'
                    })
        
        elif method == 'iqr':
            # IQR method
            q1 = np.percentile(values, 25)
            q3 = np.percentile(values, 75)
            iqr = q3 - q1
            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr
            
            anomaly_mask = (values < lower_bound) | (values > upper_bound)
            
            for i, is_anomaly in enumerate(anomaly_mask):
                if is_anomaly:
                    anomalies.append({
                        'year': int(years[i]),
                        'value': round(float(values[i]), 3),
                        'bound_exceeded': 'upper' if values[i] > upper_bound else 'lower',
                        'type': 'high' if values[i] > upper_bound else 'low'
                    })
        
        elif method == 'isolation_forest' and SKLEARN_AVAILABLE:
            # Isolation Forest method
            scaler = StandardScaler()
            values_scaled = scaler.fit_transform(values.reshape(-1, 1))
            
            clf = IsolationForest(contamination=0.1, random_state=42)
            predictions = clf.fit_predict(values_scaled)
            
            anomaly_mask = predictions == -1
            scores = clf.decision_function(values_scaled)
            
            for i, is_anomaly in enumerate(anomaly_mask):
                if is_anomaly:
                    anomalies.append({
                        'year': int(years[i]),
                        'value': round(float(values[i]), 3),
                        'anomaly_score': round(float(scores[i]), 4),
                        'type': 'outlier'
                    })
        
        return {
            'variable': variable,
            'variable_info': self.config.CLIMATE_VARIABLES.get(variable, {}),
            'region': region,
            'method': method,
            'threshold': threshold,
            'time_range': {
                'start': int(years[0]),
                'end': int(years[-1])
            },
            'statistics': {
                'total_points': len(values),
                'anomaly_count': len(anomalies),
                'anomaly_percentage': round(len(anomalies) / len(values) * 100, 2)
            },
            'anomalies': anomalies,
            'data': {
                'years': years.tolist(),
                'values': values.tolist(),
                'is_anomaly': anomaly_mask.tolist()
            }
        }
    
    def seasonal_decomposition(
        self,
        variable: str,
        region: Optional[str] = None,
        period: int = 12,
        model: str = 'additive'
    ) -> Dict[str, Any]:
        """
        Perform seasonal decomposition of time series.
        
        Args:
            variable: Climate variable
            region: Region code
            period: Seasonality period (12 for monthly data)
            model: Decomposition model ('additive' or 'multiplicative')
        """
        if not STATSMODELS_AVAILABLE:
            return {'error': 'statsmodels not available for seasonal decomposition'}
        
        # Get monthly time series
        ts = self.data_service.get_regional_timeseries(
            variable=variable,
            region=region
        )
        
        times = pd.to_datetime(ts['data']['times'])
        values = np.array(ts['data']['values'])
        
        # Create time series
        series = pd.Series(values, index=times)
        series = series.dropna()
        
        if len(series) < 2 * period:
            return {'error': f'Insufficient data for seasonal decomposition (need at least {2*period} points)'}
        
        # Perform decomposition
        try:
            decomposition = seasonal_decompose(series, model=model, period=period)
            
            return {
                'variable': variable,
                'variable_info': self.config.CLIMATE_VARIABLES.get(variable, {}),
                'region': region,
                'model': model,
                'period': period,
                'data': {
                    'times': series.index.strftime('%Y-%m-%d').tolist(),
                    'observed': series.values.tolist(),
                    'trend': np.nan_to_num(decomposition.trend.values, nan=0).tolist(),
                    'seasonal': decomposition.seasonal.values.tolist(),
                    'residual': np.nan_to_num(decomposition.resid.values, nan=0).tolist()
                },
                'seasonal_pattern': {
                    'months': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                    'values': [round(float(decomposition.seasonal.iloc[i]), 3) for i in range(min(12, len(decomposition.seasonal)))]
                }
            }
        except Exception as e:
            return {'error': f'Decomposition failed: {str(e)}'}
    
    def compute_statistics(
        self,
        variable: str,
        region: Optional[str] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Compute comprehensive statistics for a variable.
        """
        ts = self.data_service.get_regional_timeseries(
            variable=variable,
            region=region,
            start_year=start_year,
            end_year=end_year
        )
        
        values = np.array(ts['data']['values'])
        values = values[~np.isnan(values)]
        
        # Basic statistics
        basic_stats = {
            'count': int(len(values)),
            'mean': round(float(np.mean(values)), 3),
            'std': round(float(np.std(values)), 3),
            'min': round(float(np.min(values)), 3),
            'max': round(float(np.max(values)), 3),
            'median': round(float(np.median(values)), 3),
            'variance': round(float(np.var(values)), 3)
        }
        
        # Percentiles
        percentiles = {
            'p5': round(float(np.percentile(values, 5)), 3),
            'p10': round(float(np.percentile(values, 10)), 3),
            'p25': round(float(np.percentile(values, 25)), 3),
            'p75': round(float(np.percentile(values, 75)), 3),
            'p90': round(float(np.percentile(values, 90)), 3),
            'p95': round(float(np.percentile(values, 95)), 3),
            'iqr': round(float(np.percentile(values, 75) - np.percentile(values, 25)), 3)
        }
        
        # Distribution characteristics
        distribution = {
            'skewness': round(float(stats.skew(values)), 4),
            'kurtosis': round(float(stats.kurtosis(values)), 4),
            'range': round(float(np.max(values) - np.min(values)), 3),
            'cv': round(float(np.std(values) / np.mean(values) * 100), 2) if np.mean(values) != 0 else 0
        }
        
        # Normality test
        if len(values) >= 8:
            _, normality_p = stats.normaltest(values)
            distribution['normality_p_value'] = round(float(normality_p), 6)
            distribution['is_normal'] = normality_p > 0.05
        
        return {
            'variable': variable,
            'variable_info': self.config.CLIMATE_VARIABLES.get(variable, {}),
            'region': region,
            'time_range': ts['time_range'],
            'basic': basic_stats,
            'percentiles': percentiles,
            'distribution': distribution
        }
    
    def compare_periods(
        self,
        variable: str,
        region: Optional[str] = None,
        period1: Tuple[int, int] = (1961, 1990),
        period2: Tuple[int, int] = (1991, 2020)
    ) -> Dict[str, Any]:
        """
        Compare statistics between two time periods.
        """
        stats1 = self.compute_statistics(
            variable=variable,
            region=region,
            start_year=period1[0],
            end_year=period1[1]
        )
        
        stats2 = self.compute_statistics(
            variable=variable,
            region=region,
            start_year=period2[0],
            end_year=period2[1]
        )
        
        # Calculate changes
        mean_change = stats2['basic']['mean'] - stats1['basic']['mean']
        mean_change_pct = (mean_change / abs(stats1['basic']['mean']) * 100) if stats1['basic']['mean'] != 0 else 0
        
        return {
            'variable': variable,
            'variable_info': self.config.CLIMATE_VARIABLES.get(variable, {}),
            'region': region,
            'period1': {
                'range': f"{period1[0]}-{period1[1]}",
                'statistics': stats1['basic']
            },
            'period2': {
                'range': f"{period2[0]}-{period2[1]}",
                'statistics': stats2['basic']
            },
            'changes': {
                'mean_absolute': round(mean_change, 3),
                'mean_percentage': round(mean_change_pct, 2),
                'std_change': round(stats2['basic']['std'] - stats1['basic']['std'], 3),
                'min_change': round(stats2['basic']['min'] - stats1['basic']['min'], 3),
                'max_change': round(stats2['basic']['max'] - stats1['basic']['max'], 3)
            },
            'interpretation': self._interpret_period_comparison(
                variable, mean_change, mean_change_pct, period1, period2
            )
        }
    
    def _interpret_period_comparison(
        self,
        variable: str,
        mean_change: float,
        mean_change_pct: float,
        period1: Tuple[int, int],
        period2: Tuple[int, int]
    ) -> str:
        """Generate interpretation of period comparison"""
        var_info = self.config.CLIMATE_VARIABLES.get(variable, {})
        var_name = var_info.get('name', variable)
        unit = var_info.get('unit', '')
        
        if abs(mean_change) < 0.01:
            direction = "remained relatively stable"
        elif mean_change > 0:
            direction = f"increased by {abs(mean_change):.2f} {unit} ({abs(mean_change_pct):.1f}%)"
        else:
            direction = f"decreased by {abs(mean_change):.2f} {unit} ({abs(mean_change_pct):.1f}%)"
        
        return f"{var_name} has {direction} between {period1[0]}-{period1[1]} and {period2[0]}-{period2[1]}."


# Singleton instance
analysis_service = AnalysisService()
