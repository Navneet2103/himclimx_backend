"""
Analysis API Endpoints
======================
Endpoints for trend analysis, anomaly detection, and statistical analysis.
"""

from flask import Blueprint, jsonify, request
from app.services.analysis_service import analysis_service
from app.config import Config

analysis_bp = Blueprint('analysis', __name__)
config = Config()


@analysis_bp.route('/trend', methods=['GET', 'POST'])
def compute_trend():
    """
    Compute trend analysis for a variable.
    
    Query/Body Parameters:
        variable (str): Climate variable code (required)
        region (str): Region code (optional)
        start_year (int): Start year (optional)
        end_year (int): End year (optional)
        method (str): Trend method - linear, mann_kendall (default: linear)
    """
    if request.method == 'POST':
        data = request.get_json() or {}
    else:
        data = request.args
    
    variable = data.get('variable')
    region = (data.get('region') or '').upper() or None
    start_year = data.get('start_year', type=int) if hasattr(data, 'get') else data.get('start_year')
    end_year = data.get('end_year', type=int) if hasattr(data, 'get') else data.get('end_year')
    method = data.get('method', 'linear')
    
    if not variable:
        return jsonify({'error': 'Variable is required'}), 400
    if variable not in config.CLIMATE_VARIABLES:
        return jsonify({'error': f'Invalid variable: {variable}'}), 400
    
    try:
        result = analysis_service.compute_trend(
            variable=variable,
            region=region,
            start_year=int(start_year) if start_year else None,
            end_year=int(end_year) if end_year else None,
            method=method
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/anomalies', methods=['GET', 'POST'])
def detect_anomalies():
    """
    Detect anomalies in climate data.
    
    Query/Body Parameters:
        variable (str): Climate variable code (required)
        region (str): Region code (optional)
        method (str): Detection method - zscore, iqr, isolation_forest (default: zscore)
        threshold (float): Anomaly threshold (default: 2.0)
        start_year (int): Start year (optional)
        end_year (int): End year (optional)
    """
    if request.method == 'POST':
        data = request.get_json() or {}
    else:
        data = request.args
    
    variable = data.get('variable')
    region = (data.get('region') or '').upper() or None
    method = data.get('method', 'zscore')
    threshold = float(data.get('threshold', 2.0))
    start_year = data.get('start_year')
    end_year = data.get('end_year')
    
    if not variable:
        return jsonify({'error': 'Variable is required'}), 400
    
    try:
        result = analysis_service.detect_anomalies(
            variable=variable,
            region=region,
            method=method,
            threshold=threshold,
            start_year=int(start_year) if start_year else None,
            end_year=int(end_year) if end_year else None
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/seasonal', methods=['GET', 'POST'])
def seasonal_decomposition():
    """
    Perform seasonal decomposition of time series.
    
    Query/Body Parameters:
        variable (str): Climate variable code (required)
        region (str): Region code (optional)
        period (int): Seasonality period (default: 12 for monthly)
        model (str): Decomposition model - additive, multiplicative (default: additive)
    """
    if request.method == 'POST':
        data = request.get_json() or {}
    else:
        data = request.args
    
    variable = data.get('variable')
    region = (data.get('region') or '').upper() or None
    period = int(data.get('period', 12))
    model = data.get('model', 'additive')
    
    if not variable:
        return jsonify({'error': 'Variable is required'}), 400
    
    try:
        result = analysis_service.seasonal_decomposition(
            variable=variable,
            region=region,
            period=period,
            model=model
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/statistics', methods=['GET', 'POST'])
def compute_statistics():
    """
    Compute comprehensive statistics for a variable.
    
    Query/Body Parameters:
        variable (str): Climate variable code (required)
        region (str): Region code (optional)
        start_year (int): Start year (optional)
        end_year (int): End year (optional)
    """
    if request.method == 'POST':
        data = request.get_json() or {}
    else:
        data = request.args
    
    variable = data.get('variable')
    region = (data.get('region') or '').upper() or None
    start_year = data.get('start_year')
    end_year = data.get('end_year')
    
    if not variable:
        return jsonify({'error': 'Variable is required'}), 400
    
    try:
        result = analysis_service.compute_statistics(
            variable=variable,
            region=region,
            start_year=int(start_year) if start_year else None,
            end_year=int(end_year) if end_year else None
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/compare-periods', methods=['GET', 'POST'])
def compare_periods():
    """
    Compare statistics between two time periods.
    
    Query/Body Parameters:
        variable (str): Climate variable code (required)
        region (str): Region code (optional)
        period1_start (int): First period start year (default: 1961)
        period1_end (int): First period end year (default: 1990)
        period2_start (int): Second period start year (default: 1991)
        period2_end (int): Second period end year (default: 2020)
    """
    if request.method == 'POST':
        data = request.get_json() or {}
    else:
        data = request.args
    
    variable = data.get('variable')
    region = (data.get('region') or '').upper() or None
    period1_start = int(data.get('period1_start', 1961))
    period1_end = int(data.get('period1_end', 1990))
    period2_start = int(data.get('period2_start', 1991))
    period2_end = int(data.get('period2_end', 2020))
    
    if not variable:
        return jsonify({'error': 'Variable is required'}), 400
    
    try:
        result = analysis_service.compare_periods(
            variable=variable,
            region=region,
            period1=(period1_start, period1_end),
            period2=(period2_start, period2_end)
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
