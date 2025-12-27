"""
Export API Endpoints
====================
Endpoints for exporting data in various formats.
"""

from flask import Blueprint, jsonify, request, Response
from app.services.data_service import data_service
from app.services.analysis_service import analysis_service
from app.config import Config
import json
import csv
import io
from datetime import datetime

export_bp = Blueprint('export', __name__)
config = Config()


@export_bp.route('/csv', methods=['GET'])
def export_csv():
    """
    Export time series data as CSV.
    
    Query Parameters:
        variable (str): Climate variable code (required)
        region (str): Region code (optional)
        start_year (int): Start year (optional)
        end_year (int): End year (optional)
    """
    variable = request.args.get('variable')
    region = (request.args.get('region') or '').upper() or None
    start_year = request.args.get('start_year', type=int)
    end_year = request.args.get('end_year', type=int)
    
    if not variable:
        return jsonify({'error': 'Variable is required'}), 400
    
    try:
        # Get time series data
        ts = data_service.get_regional_timeseries(
            variable=variable,
            region=region,
            start_year=start_year,
            end_year=end_year
        )
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        var_info = config.CLIMATE_VARIABLES.get(variable, {})
        writer.writerow(['# HimClimX Data Export'])
        writer.writerow([f'# Variable: {var_info.get("name", variable)}'])
        writer.writerow([f'# Unit: {var_info.get("unit", "")}'])
        writer.writerow([f'# Region: {region or "All"}'])
        writer.writerow([f'# Exported: {datetime.now().isoformat()}'])
        writer.writerow([])
        
        # Data header
        writer.writerow(['Date', variable])
        
        # Data rows
        times = ts['data']['times']
        values = ts['data']['values']
        for t, v in zip(times, values):
            writer.writerow([t, v])
        
        # Return CSV response
        output.seek(0)
        filename = f'himclimx_{variable}_{region or "all"}_{datetime.now().strftime("%Y%m%d")}.csv'
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@export_bp.route('/json', methods=['GET'])
def export_json():
    """
    Export analysis results as JSON.
    
    Query Parameters:
        variable (str): Climate variable code (required)
        region (str): Region code (optional)
        include_trend (bool): Include trend analysis (default: true)
        include_statistics (bool): Include statistics (default: true)
        include_data (bool): Include raw data (default: true)
    """
    variable = request.args.get('variable')
    region = (request.args.get('region') or '').upper() or None
    include_trend = request.args.get('include_trend', 'true').lower() == 'true'
    include_statistics = request.args.get('include_statistics', 'true').lower() == 'true'
    include_data = request.args.get('include_data', 'true').lower() == 'true'
    
    if not variable:
        return jsonify({'error': 'Variable is required'}), 400
    
    try:
        result = {
            'export_info': {
                'variable': variable,
                'variable_info': config.CLIMATE_VARIABLES.get(variable, {}),
                'region': region,
                'region_info': config.REGIONS.get(region, {}) if region else None,
                'exported_at': datetime.now().isoformat()
            }
        }
        
        if include_data:
            ts = data_service.get_regional_timeseries(
                variable=variable,
                region=region
            )
            result['time_series'] = {
                'time_range': ts['time_range'],
                'data': ts['data']
            }
        
        if include_statistics:
            stats = analysis_service.compute_statistics(
                variable=variable,
                region=region
            )
            result['statistics'] = {
                'basic': stats.get('basic', {}),
                'percentiles': stats.get('percentiles', {}),
                'distribution': stats.get('distribution', {})
            }
        
        if include_trend:
            trend = analysis_service.compute_trend(
                variable=variable,
                region=region
            )
            result['trend'] = trend.get('linear_trend', {})
            result['trend']['interpretation'] = trend.get('interpretation', '')
        
        filename = f'himclimx_{variable}_{region or "all"}_{datetime.now().strftime("%Y%m%d")}.json'
        
        return Response(
            json.dumps(result, indent=2),
            mimetype='application/json',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@export_bp.route('/report', methods=['GET', 'POST'])
def export_report():
    """
    Generate a comprehensive report (JSON format with all analyses).
    
    Query/Body Parameters:
        region (str): Region code (required)
        variables (str): Comma-separated variable codes (optional, default: all)
    """
    if request.method == 'POST':
        data = request.get_json() or {}
    else:
        data = request.args
    
    region = (data.get('region') or '').upper()
    variables_str = data.get('variables', '')
    
    if not region:
        return jsonify({'error': 'Region is required'}), 400
    if region not in config.REGIONS:
        return jsonify({'error': f'Invalid region: {region}'}), 400
    
    variables = [v.strip() for v in variables_str.split(',')] if variables_str else list(config.CLIMATE_VARIABLES.keys())
    
    try:
        report = {
            'report_info': {
                'title': f'Climate Report for {config.REGIONS[region]["name"]}',
                'region': region,
                'region_info': config.REGIONS[region],
                'generated_at': datetime.now().isoformat(),
                'variables_analyzed': variables
            },
            'variables': {}
        }
        
        for var in variables:
            if var not in config.CLIMATE_VARIABLES:
                continue
            
            var_report = {
                'info': config.CLIMATE_VARIABLES[var]
            }
            
            # Statistics
            try:
                stats = analysis_service.compute_statistics(variable=var, region=region)
                var_report['statistics'] = stats.get('basic', {})
            except Exception:
                pass
            
            # Trend
            try:
                trend = analysis_service.compute_trend(variable=var, region=region)
                var_report['trend'] = {
                    'per_decade': trend['linear_trend']['per_decade'],
                    'significant': trend['linear_trend']['significant'],
                    'interpretation': trend['interpretation']
                }
            except Exception:
                pass
            
            # Anomalies
            try:
                anomalies = analysis_service.detect_anomalies(variable=var, region=region)
                var_report['anomalies'] = {
                    'count': anomalies['statistics']['anomaly_count'],
                    'percentage': anomalies['statistics']['anomaly_percentage']
                }
            except Exception:
                pass
            
            report['variables'][var] = var_report
        
        # Impact assessment
        try:
            from app.services.impact_service import impact_service
            impact = impact_service.assess_climate_risk(region=region, variables=variables)
            report['impact_assessment'] = {
                'overall_risk': impact['overall_risk'],
                'recommendations': impact.get('recommendations', [])
            }
        except Exception:
            pass
        
        filename = f'himclimx_report_{region}_{datetime.now().strftime("%Y%m%d")}.json'
        
        return Response(
            json.dumps(report, indent=2),
            mimetype='application/json',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@export_bp.route('/geojson/<region_code>', methods=['GET'])
def export_geojson(region_code):
    """
    Export region GeoJSON with climate data attached.
    
    Path Parameters:
        region_code (str): Region code
    
    Query Parameters:
        variable (str): Climate variable to include (optional)
        time (str): Time slice for data (optional)
    """
    region_code = region_code.upper()
    variable = request.args.get('variable')
    time_slice = request.args.get('time')
    
    if region_code not in config.REGIONS:
        return jsonify({'error': f'Invalid region: {region_code}'}), 404
    
    try:
        geojson = data_service.load_region_geojson(region_code)
        
        if not geojson:
            return jsonify({'error': 'GeoJSON not found'}), 404
        
        # Add climate data as properties if requested
        if variable and time_slice:
            try:
                stats = analysis_service.compute_statistics(
                    variable=variable,
                    region=region_code
                )
                
                for feature in geojson.get('features', [geojson]):
                    if 'properties' not in feature:
                        feature['properties'] = {}
                    feature['properties']['climate_variable'] = variable
                    feature['properties']['climate_stats'] = stats.get('basic', {})
            except Exception:
                pass
        
        filename = f'{region_code.lower()}.geojson'
        
        return Response(
            json.dumps(geojson, indent=2),
            mimetype='application/geo+json',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500
