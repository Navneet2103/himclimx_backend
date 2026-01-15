"""
Impact API Endpoints
====================
Endpoints for climate impact assessment and recommendations.
"""

from flask import Blueprint, jsonify, request
from app.services.data_service import data_service
from app.services.analysis_service import analysis_service
from app.services.impact_service import impact_service
from app.config import Config

impact_bp = Blueprint('impact', __name__)
config = Config()


@impact_bp.route('/assess', methods=['GET'])
def assess_impact():
    """
    Get impact assessment for a variable and region.
    
    Query Parameters:
        variable (str): Climate variable code (required)
        region (str): Region code (required)
    """
    variable = request.args.get('variable')
    region = request.args.get('region', '').upper()
    
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
        
        # Calculate trend
        trend = analysis_service.calculate_trend(
            times=ts_data['data']['times'],
            values=ts_data['data']['values']
        )
        
        # Get trend per decade
        trend_per_decade = trend.get('per_decade', 0)
        current_value = ts_data['statistics'].get('mean', 0)
        
        # Assess impact
        impact = impact_service.assess_impact(
            variable=variable,
            region=region,
            trend_per_decade=trend_per_decade,
            current_value=current_value
        )
        
        return jsonify({
            'variable': variable,
            'variable_info': ts_data['variable_info'],
            'region': region,
            'region_info': ts_data['region_info'],
            'trend': trend,
            **impact
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
