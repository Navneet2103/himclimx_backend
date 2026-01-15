"""
Data API Endpoints
==================
Endpoints for retrieving climate data, time series, and spatial data.
"""

from flask import Blueprint, jsonify, request
from app.services.data_service import data_service
from app.config import Config

data_bp = Blueprint('data', __name__)
config = Config()


@data_bp.route('/timeseries', methods=['GET'])
def get_timeseries():
    """
    Get time series data for a variable and region.
    
    Query Parameters:
        variable (str): Climate variable code (required)
        region (str): Region code (required)
        start_year (int): Start year (optional)
        end_year (int): End year (optional)
        aggregation (str): Aggregation method (default: mean)
    """
    variable = request.args.get('variable')
    region = request.args.get('region', '').upper()
    start_year = request.args.get('start_year', type=int)
    end_year = request.args.get('end_year', type=int)
    aggregation = request.args.get('aggregation', 'mean')
    
    if not variable:
        return jsonify({'error': 'Variable is required'}), 400
    if variable not in config.CLIMATE_VARIABLES:
        return jsonify({'error': f'Invalid variable: {variable}'}), 400
    if not region:
        return jsonify({'error': 'Region is required'}), 400
    if region not in config.REGIONS:
        return jsonify({'error': f'Invalid region: {region}'}), 400
    
    try:
        result = data_service.get_timeseries(
            variable=variable,
            region=region,
            start_year=start_year,
            end_year=end_year,
            aggregation=aggregation
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_bp.route('/climatology', methods=['GET'])
def get_climatology():
    """
    Get monthly climatology (long-term monthly means).
    
    Query Parameters:
        variable (str): Climate variable code (required)
        region (str): Region code (optional)
        start_year (int): Reference period start (default: 1991)
        end_year (int): Reference period end (default: 2020)
    """
    variable = request.args.get('variable')
    region = request.args.get('region', '').upper() or None
    start_year = request.args.get('start_year', 1991, type=int)
    end_year = request.args.get('end_year', 2020, type=int)
    
    if not variable:
        return jsonify({'error': 'Variable is required'}), 400
    if variable not in config.CLIMATE_VARIABLES:
        return jsonify({'error': f'Invalid variable: {variable}'}), 400
    
    try:
        result = data_service.get_climatology(
            variable=variable,
            region=region,
            start_year=start_year,
            end_year=end_year
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_bp.route('/annual', methods=['GET'])
def get_annual_data():
    """
    Get annual aggregated time series.
    
    Query Parameters:
        variable (str): Climate variable code (required)
        region (str): Region code (optional)
        start_year (int): Start year (optional)
        end_year (int): End year (optional)
        aggregation (str): Aggregation method (default: mean)
    """
    variable = request.args.get('variable')
    region = request.args.get('region', '').upper() or None
    start_year = request.args.get('start_year', type=int)
    end_year = request.args.get('end_year', type=int)
    aggregation = request.args.get('aggregation', 'mean')
    
    if not variable:
        return jsonify({'error': 'Variable is required'}), 400
    if variable not in config.CLIMATE_VARIABLES:
        return jsonify({'error': f'Invalid variable: {variable}'}), 400
    
    try:
        result = data_service.get_annual_data(
            variable=variable,
            region=region,
            start_year=start_year,
            end_year=end_year,
            aggregation=aggregation
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
