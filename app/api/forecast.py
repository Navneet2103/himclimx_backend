"""
Forecast API Endpoints
======================
Endpoints for climate forecasting and projections.
"""

from flask import Blueprint, jsonify, request
from app.services.forecast_service import forecast_service
from app.config import Config

forecast_bp = Blueprint('forecast', __name__)
config = Config()


@forecast_bp.route('/prophet', methods=['GET', 'POST'])
def prophet_forecast():
    """
    Generate forecast using Prophet model.
    
    Query/Body Parameters:
        variable (str): Climate variable code (required)
        region (str): Region code (optional)
        periods (int): Number of periods to forecast (default: 60 = 5 years)
        yearly_seasonality (bool): Include yearly seasonality (default: true)
        include_history (bool): Include historical data (default: true)
        confidence_interval (float): Confidence interval width (default: 0.95)
    """
    if request.method == 'POST':
        data = request.get_json() or {}
    else:
        data = request.args
    
    variable = data.get('variable')
    region = (data.get('region') or '').upper() or None
    periods = int(data.get('periods', 60))
    yearly_seasonality = str(data.get('yearly_seasonality', 'true')).lower() == 'true'
    include_history = str(data.get('include_history', 'true')).lower() == 'true'
    confidence_interval = float(data.get('confidence_interval', 0.95))
    
    if not variable:
        return jsonify({'error': 'Variable is required'}), 400
    if variable not in config.CLIMATE_VARIABLES:
        return jsonify({'error': f'Invalid variable: {variable}'}), 400
    
    try:
        result = forecast_service.prophet_forecast(
            variable=variable,
            region=region,
            periods=periods,
            yearly_seasonality=yearly_seasonality,
            include_history=include_history,
            confidence_interval=confidence_interval
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@forecast_bp.route('/scenarios', methods=['GET', 'POST'])
def scenario_forecast():
    """
    Generate forecasts under different SSP scenarios.
    
    Query/Body Parameters:
        variable (str): Climate variable code (required)
        region (str): Region code (optional)
        target_year (int): Target year for projection (default: 2050)
        base_period_start (int): Baseline period start (default: 1995)
        base_period_end (int): Baseline period end (default: 2014)
    """
    if request.method == 'POST':
        data = request.get_json() or {}
    else:
        data = request.args
    
    variable = data.get('variable')
    region = (data.get('region') or '').upper() or None
    target_year = int(data.get('target_year', 2050))
    base_period_start = int(data.get('base_period_start', 1995))
    base_period_end = int(data.get('base_period_end', 2014))
    
    if not variable:
        return jsonify({'error': 'Variable is required'}), 400
    
    try:
        result = forecast_service.forecast_scenarios(
            variable=variable,
            region=region,
            target_year=target_year,
            base_period=(base_period_start, base_period_end)
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@forecast_bp.route('/summary', methods=['GET'])
def forecast_summary():
    """
    Get forecast summary for multiple variables.
    
    Query Parameters:
        variables (str): Comma-separated variable codes (default: tmp,pre,pet)
        region (str): Region code (optional)
        years (int): Number of years to forecast (default: 5)
    """
    variables_str = request.args.get('variables', 'tmp,pre,pet')
    region = (request.args.get('region') or '').upper() or None
    years = int(request.args.get('years', 5))
    
    variables = [v.strip() for v in variables_str.split(',')]
    
    try:
        result = forecast_service.get_forecast_summary(
            variables=variables,
            region=region,
            forecast_years=years
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@forecast_bp.route('/available-methods', methods=['GET'])
def available_methods():
    """
    Get information about available forecasting methods.
    """
    try:
        from prophet import Prophet
        prophet_available = True
    except ImportError:
        prophet_available = False
    
    return jsonify({
        'methods': {
            'prophet': {
                'available': prophet_available,
                'description': 'Facebook Prophet time series forecasting',
                'features': ['yearly_seasonality', 'trend', 'uncertainty_intervals']
            },
            'linear_trend': {
                'available': True,
                'description': 'Simple linear trend extrapolation',
                'features': ['trend', 'confidence_intervals']
            },
            'scenarios': {
                'available': True,
                'description': 'SSP climate scenario projections',
                'scenarios': list(config.SSP_SCENARIOS.keys())
            }
        }
    })
