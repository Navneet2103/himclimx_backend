"""
Metadata API Endpoints
======================
Endpoints for retrieving metadata about variables, regions, and data availability.
"""

from flask import Blueprint, jsonify, current_app
from app.config import Config
from app.services.data_service import data_service

metadata_bp = Blueprint('metadata', __name__)
config = Config()


@metadata_bp.route('/variables', methods=['GET'])
def get_variables():
    """Get all available climate variables with metadata"""
    return jsonify({
        'count': len(config.CLIMATE_VARIABLES),
        'variables': config.CLIMATE_VARIABLES
    })


@metadata_bp.route('/variables/<variable_code>', methods=['GET'])
def get_variable(variable_code):
    """Get metadata for a specific variable"""
    if variable_code not in config.CLIMATE_VARIABLES:
        return jsonify({'error': f'Variable {variable_code} not found'}), 404
    
    return jsonify({
        'code': variable_code,
        **config.CLIMATE_VARIABLES[variable_code]
    })


@metadata_bp.route('/regions', methods=['GET'])
def get_regions():
    """Get all available regions with metadata"""
    return jsonify({
        'count': len(config.REGIONS),
        'regions': config.REGIONS
    })


@metadata_bp.route('/regions/<region_code>', methods=['GET'])
def get_region(region_code):
    """Get metadata for a specific region"""
    region_code = region_code.upper()
    if region_code not in config.REGIONS:
        return jsonify({'error': f'Region {region_code} not found'}), 404
    
    return jsonify({
        'code': region_code,
        **config.REGIONS[region_code]
    })


@metadata_bp.route('/time-range', methods=['GET'])
def get_time_range():
    """Get available time range in the data"""
    return jsonify({
        'start_year': config.DATA_START_YEAR,
        'end_year': config.DATA_END_YEAR,
        'temporal_resolution': 'monthly'
    })


@metadata_bp.route('/scenarios', methods=['GET'])
def get_scenarios():
    """Get SSP climate scenarios information"""
    return jsonify({
        'count': len(config.SSP_SCENARIOS),
        'scenarios': config.SSP_SCENARIOS
    })


@metadata_bp.route('/data-sources', methods=['GET'])
def get_data_sources():
    """Get information about data sources and URLs"""
    return jsonify({
        'zarr_base_url': config.ZARR_BASE_PATH,
        'geojson_base_url': config.GEOJSON_BASE_PATH,
        'dem_url': config.DEM_PATH,
        'format': {
            'climate': 'Zarr (cloud-optimized)',
            'regions': 'GeoJSON',
            'dem': 'Cloud-Optimized GeoTIFF (COG)'
        }
    })


@metadata_bp.route('/summary', methods=['GET'])
def get_summary():
    """Get complete metadata summary"""
    return jsonify({
        'variables': {
            'count': len(config.CLIMATE_VARIABLES),
            'list': list(config.CLIMATE_VARIABLES.keys())
        },
        'regions': {
            'count': len(config.REGIONS),
            'zones': ['Eastern', 'Central', 'Western'],
            'elevation_bands': ['2000m', '4000m', '6000m']
        },
        'time_range': {
            'start': config.DATA_START_YEAR,
            'end': config.DATA_END_YEAR
        },
        'scenarios': list(config.SSP_SCENARIOS.keys()),
        'external_services': {
            'climate_chat': config.OPENAI_CHAT_URL
        }
    })
