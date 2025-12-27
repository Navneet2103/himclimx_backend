"""
Impact API Endpoints
====================
Endpoints for climate impact assessment and vulnerability analysis.
"""

from flask import Blueprint, jsonify, request
from app.services.impact_service import impact_service
from app.config import Config

impact_bp = Blueprint('impact', __name__)
config = Config()


@impact_bp.route('/risk-assessment', methods=['GET', 'POST'])
def risk_assessment():
    """
    Comprehensive climate risk assessment for a region.
    
    Query/Body Parameters:
        region (str): Region code (required)
        variables (str): Comma-separated variable codes (optional, default: all)
        start_year (int): Analysis period start (default: 1990)
        end_year (int): Analysis period end (default: 2020)
    """
    if request.method == 'POST':
        data = request.get_json() or {}
    else:
        data = request.args
    
    region = (data.get('region') or '').upper()
    variables_str = data.get('variables', '')
    start_year = int(data.get('start_year', 1990))
    end_year = int(data.get('end_year', 2020))
    
    if not region:
        return jsonify({'error': 'Region is required'}), 400
    if region not in config.REGIONS:
        return jsonify({'error': f'Invalid region: {region}'}), 400
    
    variables = None
    if variables_str:
        variables = [v.strip() for v in variables_str.split(',')]
    
    try:
        result = impact_service.assess_climate_risk(
            region=region,
            variables=variables,
            period=(start_year, end_year)
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@impact_bp.route('/sector-vulnerability', methods=['GET', 'POST'])
def sector_vulnerability():
    """
    Assess vulnerability for a specific sector.
    
    Query/Body Parameters:
        region (str): Region code (required)
        sector (str): Sector name (required)
            Options: agriculture, water_resources, ecosystems, human_health, infrastructure
        start_year (int): Analysis period start (default: 1990)
        end_year (int): Analysis period end (default: 2020)
    """
    if request.method == 'POST':
        data = request.get_json() or {}
    else:
        data = request.args
    
    region = (data.get('region') or '').upper()
    sector = data.get('sector', '').lower()
    start_year = int(data.get('start_year', 1990))
    end_year = int(data.get('end_year', 2020))
    
    if not region:
        return jsonify({'error': 'Region is required'}), 400
    if not sector:
        return jsonify({'error': 'Sector is required'}), 400
    
    try:
        result = impact_service.sector_vulnerability(
            region=region,
            sector=sector,
            period=(start_year, end_year)
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@impact_bp.route('/regional-comparison', methods=['GET'])
def regional_comparison():
    """
    Compare all regions for a specific variable.
    
    Query Parameters:
        variable (str): Climate variable code (required)
        start_year (int): Analysis period start (default: 1990)
        end_year (int): Analysis period end (default: 2020)
    """
    variable = request.args.get('variable')
    start_year = int(request.args.get('start_year', 1990))
    end_year = int(request.args.get('end_year', 2020))
    
    if not variable:
        return jsonify({'error': 'Variable is required'}), 400
    
    try:
        result = impact_service.regional_comparison(
            variable=variable,
            period=(start_year, end_year)
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@impact_bp.route('/sectors', methods=['GET'])
def get_sectors():
    """
    Get information about available sectors for vulnerability assessment.
    """
    return jsonify({
        'sectors': {
            'agriculture': {
                'name': 'Agriculture',
                'description': 'Crop production, livestock, and food security',
                'key_variables': ['tmp', 'pre', 'frs', 'pet'],
                'icon': '🌾'
            },
            'water_resources': {
                'name': 'Water Resources',
                'description': 'Water availability, quality, and management',
                'key_variables': ['pre', 'pet', 'tmp', 'wet'],
                'icon': '💧'
            },
            'ecosystems': {
                'name': 'Ecosystems',
                'description': 'Biodiversity, forests, and natural habitats',
                'key_variables': ['tmp', 'pre', 'wet', 'vap'],
                'icon': '🌲'
            },
            'human_health': {
                'name': 'Human Health',
                'description': 'Public health and disease patterns',
                'key_variables': ['tmp', 'tmx', 'pre', 'vap'],
                'icon': '🏥'
            },
            'infrastructure': {
                'name': 'Infrastructure',
                'description': 'Buildings, roads, and critical facilities',
                'key_variables': ['pre', 'tmx', 'frs'],
                'icon': '🏗️'
            }
        }
    })


@impact_bp.route('/recommendations', methods=['GET'])
def get_recommendations():
    """
    Get climate adaptation recommendations for a region.
    
    Query Parameters:
        region (str): Region code (required)
    """
    region = (request.args.get('region') or '').upper()
    
    if not region:
        return jsonify({'error': 'Region is required'}), 400
    if region not in config.REGIONS:
        return jsonify({'error': f'Invalid region: {region}'}), 400
    
    try:
        assessment = impact_service.assess_climate_risk(region=region)
        return jsonify({
            'region': region,
            'region_info': config.REGIONS.get(region, {}),
            'risk_level': assessment['overall_risk']['level'],
            'recommendations': assessment.get('recommendations', [])
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@impact_bp.route('/summary', methods=['GET'])
def impact_summary():
    """
    Get impact summary for all regions.
    
    Query Parameters:
        variable (str): Climate variable code (optional, default: tmp)
    """
    variable = request.args.get('variable', 'tmp')
    
    try:
        summaries = []
        for region_code in config.REGIONS.keys():
            try:
                assessment = impact_service.assess_climate_risk(
                    region=region_code,
                    variables=[variable]
                )
                summaries.append({
                    'region': region_code,
                    'region_info': config.REGIONS[region_code],
                    'risk_score': assessment['overall_risk']['score'],
                    'risk_level': assessment['overall_risk']['level'],
                    'risk_color': assessment['overall_risk']['color']
                })
            except Exception:
                continue
        
        # Sort by risk score
        summaries.sort(key=lambda x: x['risk_score'], reverse=True)
        
        return jsonify({
            'variable': variable,
            'variable_info': config.CLIMATE_VARIABLES.get(variable, {}),
            'summaries': summaries
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
