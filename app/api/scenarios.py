"""
Scenarios API Endpoints
=======================
Endpoints for climate scenario information and projections.
"""

from flask import Blueprint, jsonify, request
from app.services.forecast_service import forecast_service
from app.config import Config

scenarios_bp = Blueprint('scenarios', __name__)
config = Config()


@scenarios_bp.route('/', methods=['GET'])
def get_all_scenarios():
    """
    Get information about all SSP scenarios.
    """
    return jsonify({
        'scenarios': config.SSP_SCENARIOS,
        'description': 'Shared Socioeconomic Pathways (SSPs) represent different future scenarios '
                       'based on socioeconomic development and greenhouse gas emissions.'
    })


@scenarios_bp.route('/<scenario_code>', methods=['GET'])
def get_scenario(scenario_code):
    """
    Get information about a specific scenario.
    
    Path Parameters:
        scenario_code (str): Scenario code (SSP1, SSP2, SSP3, SSP5)
    """
    scenario_code = scenario_code.upper()
    
    if scenario_code not in config.SSP_SCENARIOS:
        return jsonify({'error': f'Invalid scenario: {scenario_code}'}), 404
    
    return jsonify({
        'code': scenario_code,
        **config.SSP_SCENARIOS[scenario_code]
    })


@scenarios_bp.route('/projection', methods=['GET', 'POST'])
def scenario_projection():
    """
    Get climate projections under different scenarios.
    
    Query/Body Parameters:
        variable (str): Climate variable code (required)
        region (str): Region code (optional)
        target_year (int): Target year (default: 2050)
    """
    if request.method == 'POST':
        data = request.get_json() or {}
    else:
        data = request.args
    
    variable = data.get('variable')
    region = (data.get('region') or '').upper() or None
    target_year = int(data.get('target_year', 2050))
    
    if not variable:
        return jsonify({'error': 'Variable is required'}), 400
    
    try:
        result = forecast_service.forecast_scenarios(
            variable=variable,
            region=region,
            target_year=target_year
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@scenarios_bp.route('/compare', methods=['GET'])
def compare_scenarios():
    """
    Compare all scenarios for a variable at multiple time points.
    
    Query Parameters:
        variable (str): Climate variable code (required)
        region (str): Region code (optional)
        years (str): Comma-separated target years (default: 2030,2050,2100)
    """
    variable = request.args.get('variable')
    region = (request.args.get('region') or '').upper() or None
    years_str = request.args.get('years', '2030,2050,2100')
    
    if not variable:
        return jsonify({'error': 'Variable is required'}), 400
    
    years = [int(y.strip()) for y in years_str.split(',')]
    
    try:
        comparisons = {}
        for year in years:
            result = forecast_service.forecast_scenarios(
                variable=variable,
                region=region,
                target_year=year
            )
            comparisons[year] = {
                'baseline_mean': result.get('baseline_mean'),
                'scenarios': result.get('scenarios', {})
            }
        
        return jsonify({
            'variable': variable,
            'variable_info': config.CLIMATE_VARIABLES.get(variable, {}),
            'region': region,
            'years': years,
            'comparisons': comparisons
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@scenarios_bp.route('/timeline', methods=['GET'])
def scenario_timeline():
    """
    Get scenario projections as a timeline.
    
    Query Parameters:
        variable (str): Climate variable code (required)
        region (str): Region code (optional)
        scenario (str): Scenario code (default: all)
        start_year (int): Start year (default: 2020)
        end_year (int): End year (default: 2100)
        interval (int): Year interval (default: 10)
    """
    variable = request.args.get('variable')
    region = (request.args.get('region') or '').upper() or None
    scenario = request.args.get('scenario', 'all').upper()
    start_year = int(request.args.get('start_year', 2020))
    end_year = int(request.args.get('end_year', 2100))
    interval = int(request.args.get('interval', 10))
    
    if not variable:
        return jsonify({'error': 'Variable is required'}), 400
    
    years = list(range(start_year, end_year + 1, interval))
    
    try:
        timeline = {ssp: [] for ssp in config.SSP_SCENARIOS.keys()}
        baseline = None
        
        for year in years:
            result = forecast_service.forecast_scenarios(
                variable=variable,
                region=region,
                target_year=year
            )
            
            if baseline is None:
                baseline = result.get('baseline_mean')
            
            for ssp, values in result.get('scenarios', {}).items():
                timeline[ssp].append({
                    'year': year,
                    'value': values.get('projected_value'),
                    'change': values.get('change_from_baseline')
                })
        
        if scenario != 'ALL' and scenario in timeline:
            timeline = {scenario: timeline[scenario]}
        
        return jsonify({
            'variable': variable,
            'variable_info': config.CLIMATE_VARIABLES.get(variable, {}),
            'region': region,
            'baseline': baseline,
            'years': years,
            'timeline': timeline
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
