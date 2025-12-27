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
    Get time series data for a variable at a specific location.
    
    Query Parameters:
        variable (str): Climate variable code (required)
        lat (float): Latitude (required)
        lon (float): Longitude (required)
        start_year (int): Start year (optional)
        end_year (int): End year (optional)
    """
    variable = request.args.get('variable')
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    start_year = request.args.get('start_year', type=int)
    end_year = request.args.get('end_year', type=int)
    
    if not variable:
        return jsonify({'error': 'Variable is required'}), 400
    if variable not in config.CLIMATE_VARIABLES:
        return jsonify({'error': f'Invalid variable: {variable}'}), 400
    if lat is None or lon is None:
        return jsonify({'error': 'lat and lon are required'}), 400
    
    try:
        result = data_service.get_timeseries(
            variable=variable,
            lat=lat,
            lon=lon,
            start_year=start_year,
            end_year=end_year
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_bp.route('/regional', methods=['GET'])
def get_regional_timeseries():
    """
    Get regional mean time series data.
    
    Query Parameters:
        variable (str): Climate variable code (required)
        region (str): Region code (required)
        start_year (int): Start year (optional)
        end_year (int): End year (optional)
        aggregation (str): Aggregation method - mean, min, max, sum (default: mean)
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
        result = data_service.get_regional_timeseries(
            variable=variable,
            region=region,
            start_year=start_year,
            end_year=end_year,
            aggregation=aggregation
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_bp.route('/spatial', methods=['GET'])
def get_spatial_data():
    """
    Get spatial grid data for a specific time.
    
    Query Parameters:
        variable (str): Climate variable code (required)
        time (str): Time slice in YYYY-MM-DD format (required)
        lat_min (float): Minimum latitude (optional)
        lat_max (float): Maximum latitude (optional)
        lon_min (float): Minimum longitude (optional)
        lon_max (float): Maximum longitude (optional)
    """
    variable = request.args.get('variable')
    time_slice = request.args.get('time')
    lat_min = request.args.get('lat_min', type=float)
    lat_max = request.args.get('lat_max', type=float)
    lon_min = request.args.get('lon_min', type=float)
    lon_max = request.args.get('lon_max', type=float)
    
    if not variable:
        return jsonify({'error': 'Variable is required'}), 400
    if not time_slice:
        return jsonify({'error': 'Time is required'}), 400
    
    lat_range = (lat_min, lat_max) if lat_min and lat_max else None
    lon_range = (lon_min, lon_max) if lon_min and lon_max else None
    
    try:
        result = data_service.get_spatial_data(
            variable=variable,
            time_slice=time_slice,
            lat_range=lat_range,
            lon_range=lon_range
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
        start_year (int): Reference period start year (default: 1991)
        end_year (int): Reference period end year (default: 2020)
    """
    variable = request.args.get('variable')
    region = request.args.get('region', '').upper() or None
    start_year = request.args.get('start_year', 1991, type=int)
    end_year = request.args.get('end_year', 2020, type=int)
    
    if not variable:
        return jsonify({'error': 'Variable is required'}), 400
    
    try:
        result = data_service.get_monthly_climatology(
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
        aggregation (str): Aggregation method - mean, min, max, sum (default: mean)
    """
    variable = request.args.get('variable')
    region = request.args.get('region', '').upper() or None
    aggregation = request.args.get('aggregation', 'mean')
    
    if not variable:
        return jsonify({'error': 'Variable is required'}), 400
    
    try:
        result = data_service.get_annual_timeseries(
            variable=variable,
            region=region,
            aggregation=aggregation
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_bp.route('/compare', methods=['GET'])
def compare_variables():
    """
    Compare multiple variables over time.
    
    Query Parameters:
        variables (str): Comma-separated variable codes (required)
        region (str): Region code (optional)
        start_year (int): Start year (optional)
        end_year (int): End year (optional)
    """
    variables_str = request.args.get('variables', '')
    region = request.args.get('region', '').upper() or None
    start_year = request.args.get('start_year', type=int)
    end_year = request.args.get('end_year', type=int)
    
    if not variables_str:
        return jsonify({'error': 'Variables are required'}), 400
    
    variables = [v.strip() for v in variables_str.split(',')]
    
    # Validate variables
    invalid = [v for v in variables if v not in config.CLIMATE_VARIABLES]
    if invalid:
        return jsonify({'error': f'Invalid variables: {invalid}'}), 400
    
    try:
        result = data_service.compare_variables(
            variables=variables,
            region=region,
            start_year=start_year,
            end_year=end_year
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """
    Get basic statistics for a variable.
    
    Query Parameters:
        variable (str): Climate variable code (required)
        region (str): Region code (optional)
        start_year (int): Start year (optional)
        end_year (int): End year (optional)
    """
    variable = request.args.get('variable')
    region = request.args.get('region', '').upper() or None
    start_year = request.args.get('start_year', type=int)
    end_year = request.args.get('end_year', type=int)
    
    if not variable:
        return jsonify({'error': 'Variable is required'}), 400
    
    try:
        ts = data_service.get_regional_timeseries(
            variable=variable,
            region=region,
            start_year=start_year,
            end_year=end_year
        )
        return jsonify({
            'variable': variable,
            'variable_info': ts['variable_info'],
            'region': region,
            'time_range': ts['time_range'],
            'statistics': ts['statistics']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
