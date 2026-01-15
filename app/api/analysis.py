"""
Analysis API Endpoints
======================
Endpoints for trend analysis, anomaly detection, and statistics.
"""

from flask import Blueprint, jsonify, request
from app.services.data_service import data_service
from app.services.analysis_service import analysis_service
from app.config import Config

analysis_bp = Blueprint('analysis', __name__)
config = Config()


@analysis_bp.route('/trend', methods=['GET'])
def get_trend():
    """
    Get trend analysis for a variable and region.
    
    Query Parameters:
        variable (str): Climate variable code (required)
        region (str): Region code (required)
        start_year (int): Start year (optional)
        end_year (int): End year (optional)
    """
    variable = request.args.get('variable')
    region = request.args.get('region', '').upper()
    start_year = request.args.get('start_year', type=int)
    end_year = request.args.get('end_year', type=int)
    
    if not variable:
        return jsonify({'error': 'Variable is required'}), 400
    if not region:
        return jsonify({'error': 'Region is required'}), 400
    
    try:
        # Get time series data
        ts_data = data_service.get_timeseries(
            variable=variable,
            region=region,
            start_year=start_year,
            end_year=end_year
        )
        
        # Calculate trend
        trend = analysis_service.calculate_trend(
            times=ts_data['data']['times'],
            values=ts_data['data']['values']
        )
        
        return jsonify({
            'variable': variable,
            'region': region,
            'time_range': ts_data['time_range'],
            **trend
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/anomalies', methods=['GET'])
def get_anomalies():
    """
    Get anomaly detection for a variable and region.
    
    Query Parameters:
        variable (str): Climate variable code (required)
        region (str): Region code (required)
        start_year (int): Start year (optional)
        end_year (int): End year (optional)
        threshold (float): Z-score threshold (default: 2.0)
    """
    variable = request.args.get('variable')
    region = request.args.get('region', '').upper()
    start_year = request.args.get('start_year', type=int)
    end_year = request.args.get('end_year', type=int)
    threshold = request.args.get('threshold', 2.0, type=float)
    
    if not variable:
        return jsonify({'error': 'Variable is required'}), 400
    if not region:
        return jsonify({'error': 'Region is required'}), 400
    
    try:
        # Get time series data
        ts_data = data_service.get_timeseries(
            variable=variable,
            region=region,
            start_year=start_year,
            end_year=end_year
        )
        
        # Detect anomalies
        anomalies = analysis_service.detect_anomalies(
            times=ts_data['data']['times'],
            values=ts_data['data']['values'],
            threshold=threshold
        )
        
        return jsonify({
            'variable': variable,
            'region': region,
            'time_range': ts_data['time_range'],
            **anomalies
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """
    Get comprehensive statistics for a variable and region.
    
    Query Parameters:
        variable (str): Climate variable code (required)
        region (str): Region code (required)
        start_year (int): Start year (optional)
        end_year (int): End year (optional)
    """
    variable = request.args.get('variable')
    region = request.args.get('region', '').upper()
    start_year = request.args.get('start_year', type=int)
    end_year = request.args.get('end_year', type=int)
    
    if not variable:
        return jsonify({'error': 'Variable is required'}), 400
    if not region:
        return jsonify({'error': 'Region is required'}), 400
    
    try:
        # Get time series data
        ts_data = data_service.get_timeseries(
            variable=variable,
            region=region,
            start_year=start_year,
            end_year=end_year
        )
        
        # Calculate statistics
        stats = analysis_service.calculate_statistics(
            values=ts_data['data']['values']
        )
        
        return jsonify({
            'variable': variable,
            'variable_info': ts_data['variable_info'],
            'region': region,
            'region_info': ts_data['region_info'],
            'time_range': ts_data['time_range'],
            'statistics': stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
