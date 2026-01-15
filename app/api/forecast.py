"""
Forecast API Endpoints
======================
Endpoints for time series forecasting and scenario projections.
"""

from flask import Blueprint, jsonify, request
from app.services.data_service import data_service
from app.services.forecast_service import forecast_service
from app.config import Config

forecast_bp = Blueprint('forecast', __name__)
config = Config()


@forecast_bp.route('/prophet', methods=['GET'])
def get_forecast():
    """
    Get Prophet-based forecast for a variable and region.
    
    Query Parameters:
        variable (str): Climate variable code (required)
        region (str): Region code (required)
        years (int): Number of years to forecast (default: 5)
    """
    variable = request.args.get('variable')
    region = request.args.get('region', '').upper()
    years = request.args.get('years', 5, type=int)
    
    if not variable:
        return jsonify({'error': 'Variable is required'}), 400
    if not region:
        return jsonify({'error': 'Region is required'}), 400
    
    # Limit forecast years
    years = min(years, 10)
    
    try:
        # Get time series data
        ts_data = data_service.get_timeseries(
            variable=variable,
            region=region
        )
        
        # Generate forecast
        forecast = forecast_service.prophet_forecast(
            times=ts_data['data']['times'],
            values=ts_data['data']['values'],
            years=years
        )
        
        return jsonify({
            'variable': variable,
            'variable_info': ts_data['variable_info'],
            'region': region,
            'forecast_years': years,
            **forecast
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@forecast_bp.route('/scenarios', methods=['GET'])
def get_scenarios():
    """
    Get climate scenario projections.
    
    Query Parameters:
        variable (str): Climate variable code (required)
        region (str): Region code (required)
        target_year (int): Target year for projection (default: 2050)
    """
    variable = request.args.get('variable')
    region = request.args.get('region', '').upper()
    target_year = request.args.get('target_year', 2050, type=int)
    
    if not variable:
        return jsonify({'error': 'Variable is required'}), 400
    if not region:
        return jsonify({'error': 'Region is required'}), 400
    
    try:
        # Get time series data
        ts_data = data_service.get_timeseries(
            variable=variable,
            region=region
        )
        
        # Generate scenarios
        scenarios = forecast_service.generate_scenarios(
            times=ts_data['data']['times'],
            values=ts_data['data']['values'],
            target_year=target_year
        )
        
        return jsonify({
            'variable': variable,
            'variable_info': ts_data['variable_info'],
            'region': region,
            **scenarios
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
