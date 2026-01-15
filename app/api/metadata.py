"""
Metadata API Endpoints
=====================
Endpoints for retrieving variable, region, and scenario metadata.
"""

from flask import Blueprint, jsonify
from app.config import Config

metadata_bp = Blueprint('metadata', __name__)
config = Config()


@metadata_bp.route('/variables', methods=['GET'])
def get_variables():
    """Get all available climate variables"""
    return jsonify({
        'count': len(config.CLIMATE_VARIABLES),
        'variables': config.CLIMATE_VARIABLES
    })


@metadata_bp.route('/regions', methods=['GET'])
def get_regions():
    """Get all available regions"""
    return jsonify({
        'count': len(config.REGIONS),
        'regions': config.REGIONS
    })


@metadata_bp.route('/scenarios', methods=['GET'])
def get_scenarios():
    """Get all SSP scenarios"""
    return jsonify({
        'count': len(config.SSP_SCENARIOS),
        'scenarios': config.SSP_SCENARIOS
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
            'list': list(config.REGIONS.keys())
        },
        'scenarios': {
            'count': len(config.SSP_SCENARIOS),
            'list': list(config.SSP_SCENARIOS.keys())
        },
        'time_range': {
            'start': config.DATA_START_YEAR,
            'end': config.DATA_END_YEAR
        }
    })
