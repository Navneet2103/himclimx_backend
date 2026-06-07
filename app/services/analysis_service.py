"""
Analysis Service
================
Service for performing statistical analysis on climate data.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from scipy import stats as scipy_stats
import logging

from app.config import Config

logger = logging.getLogger(__name__)


class AnalysisService:
    """Service for climate data analysis"""
    
    def __init__(self):
        self.config = Config()
    
    def calculate_trend(
        self,
        times: List[str],
        values: List[float]
    ) -> Dict[str, Any]:
        """
        Calculate linear trend with statistical significance.
        Aggregates to annual means first — removes seasonal noise and is the
        standard approach in climate science (WMO guidelines).
        """
        try:
            df = pd.DataFrame({'date': pd.to_datetime(times), 'value': values})
            df = df.dropna(subset=['value'])

            if len(df) < 24:
                return {'error': 'Insufficient data for trend analysis (need ≥ 2 years)'}

            # Aggregate to annual means — removes intra-annual seasonal noise
            df['year'] = df['date'].dt.year
            annual = df.groupby('year')['value'].mean().dropna()

            if len(annual) < 5:
                return {'error': 'Insufficient annual data for trend analysis'}

            years_arr = annual.index.values.astype(float)
            vals_arr  = annual.values

            # OLS linear regression on annual means
            slope, intercept, r_value, p_value, std_err = scipy_stats.linregress(years_arr, vals_arr)

            # Sen's slope (robust estimator — preferred in climate studies)
            n = len(vals_arr)
            slopes = []
            for i in range(n - 1):
                for j in range(i + 1, n):
                    dy = vals_arr[j] - vals_arr[i]
                    dx = years_arr[j] - years_arr[i]
                    if dx != 0:
                        slopes.append(dy / dx)
            sens_slope = float(np.median(slopes)) if slopes else float(slope)

            # Mann-Kendall test on annual data
            mk_result = self._mann_kendall_test(vals_arr)

            mean_val = float(np.mean(vals_arr))
            return {
                'slope':          round(float(slope), 6),
                'intercept':      round(float(intercept), 3),
                'r_squared':      round(float(r_value ** 2), 4),
                # Do NOT round p_value — rounding to 6dp truncates values like 1e-30 to 0.0,
                # making confidence = (1 - 0) * 100 = 100% on the frontend.
                'p_value':        float(p_value),
                'std_err':        round(float(std_err), 6),
                'per_decade':     round(float(slope * 10), 4),
                'sens_slope':     round(sens_slope, 6),
                'sens_per_decade': round(sens_slope * 10, 4),
                'percent_change': round(float((slope * 10) / mean_val * 100), 2) if mean_val != 0 else 0.0,
                'annual_values':  [round(float(v), 3) for v in vals_arr],
                'annual_years':   [int(y) for y in years_arr],
                'mann_kendall':   mk_result,
            }
        except Exception as e:
            logger.error(f"Trend calculation error: {str(e)}")
            return {'error': str(e)}
    
    def _mann_kendall_test(self, values: np.ndarray) -> Dict[str, Any]:
        """
        Perform Mann-Kendall test for trend detection.
        """
        try:
            n = len(values)
            s = 0
            
            for i in range(n - 1):
                for j in range(i + 1, n):
                    s += np.sign(values[j] - values[i])
            
            # Variance of S
            var_s = n * (n - 1) * (2 * n + 5) / 18
            
            # Z statistic
            if s > 0:
                z = (s - 1) / np.sqrt(var_s)
            elif s < 0:
                z = (s + 1) / np.sqrt(var_s)
            else:
                z = 0
            
            # P-value (two-tailed) — keep full float precision (no rounding)
            p_value = 2 * (1 - scipy_stats.norm.cdf(abs(z)))
            
            # Kendall's tau
            tau = s / (n * (n - 1) / 2)
            
            # Trend direction
            if p_value < 0.05:
                trend = 'increasing' if s > 0 else 'decreasing'
            else:
                trend = 'no significant trend'
            
            return {
                'trend': trend,
                'p_value': float(p_value),
                'tau': round(float(tau), 4),
                'z_statistic': round(float(z), 4)
            }
        except Exception as e:
            logger.error(f"Mann-Kendall test error: {str(e)}")
            return {'trend': 'unknown', 'p_value': 1.0, 'tau': 0.0}
    
    def detect_anomalies(
        self,
        times: List[str],
        values: List[float],
        threshold: float = 2.0
    ) -> Dict[str, Any]:
        """
        Detect anomalies using z-score method.
        """
        try:
            # Convert to annual if needed
            df = pd.DataFrame({
                'date': pd.to_datetime(times),
                'value': values
            })
            df = df.dropna()
            
            # Group by year and calculate mean
            df['year'] = df['date'].dt.year
            annual = df.groupby('year')['value'].mean().reset_index()
            
            years = annual['year'].tolist()
            vals = annual['value'].values
            
            # Calculate z-scores
            mean_val = np.mean(vals)
            std_val = np.std(vals)
            
            if std_val == 0:
                z_scores = np.zeros_like(vals)
            else:
                z_scores = (vals - mean_val) / std_val
            
            # Find anomalies
            anomalies = []
            for i, (year, val, z) in enumerate(zip(years, vals, z_scores)):
                if abs(z) > threshold:
                    anomalies.append({
                        'year': int(year),
                        'value': round(float(val), 3),
                        'z_score': round(float(z), 3),
                        'type': 'high' if z > 0 else 'low'
                    })
            
            return {
                'years': years,
                'values': [round(float(v), 3) for v in vals],
                'z_scores': [round(float(z), 3) for z in z_scores],
                'anomalies': anomalies,
                'threshold': threshold,
                'mean': round(float(mean_val), 3),
                'std': round(float(std_val), 3)
            }
        except Exception as e:
            logger.error(f"Anomaly detection error: {str(e)}")
            return {'error': str(e)}
    
    def calculate_statistics(
        self,
        values: List[float]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive statistics.
        """
        try:
            vals = np.array([v for v in values if v is not None])
            vals = vals[~np.isnan(vals)]
            
            if len(vals) == 0:
                return {'error': 'No valid data'}
            
            return {
                'mean': round(float(np.mean(vals)), 3),
                'median': round(float(np.median(vals)), 3),
                'std': round(float(np.std(vals)), 3),
                'min': round(float(np.min(vals)), 3),
                'max': round(float(np.max(vals)), 3),
                'count': int(len(vals)),
                'variance': round(float(np.var(vals)), 3),
                'skewness': round(float(scipy_stats.skew(vals)), 3),
                'kurtosis': round(float(scipy_stats.kurtosis(vals)), 3),
                'percentiles': {
                    'p5': round(float(np.percentile(vals, 5)), 3),
                    'p25': round(float(np.percentile(vals, 25)), 3),
                    'p75': round(float(np.percentile(vals, 75)), 3),
                    'p95': round(float(np.percentile(vals, 95)), 3)
                }
            }
        except Exception as e:
            logger.error(f"Statistics calculation error: {str(e)}")
            return {'error': str(e)}


# Singleton instance
analysis_service = AnalysisService()
