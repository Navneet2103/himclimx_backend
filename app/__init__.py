"""
HimClimX Backend API
====================
Flask-based REST API for the Himalayan Climate Dashboard.

Features:
- Climate data retrieval from Cloudflare R2 (Zarr format)
- Time series analysis and statistics
- Prophet-based forecasting
- Anomaly detection
- Climate scenario projections (SSP1-SSP5)
- Impact assessment and recommendations
- Regional data and GeoJSON endpoints
- 3D terrain data for visualization
"""

import os
from flask import Flask
from flask_cors import CORS

def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object('app.config.Config')
    
    # Enable CORS for all routes
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "http://localhost:3000",
                "https://*.vercel.app",
                "https://himclimx.vercel.app",
                "*"  # Remove in production
            ],
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Register blueprints
    from app.api.metadata import metadata_bp
    from app.api.data import data_bp
    from app.api.analysis import analysis_bp
    from app.api.geo import geo_bp
    from app.api.forecast import forecast_bp
    from app.api.scenarios import scenarios_bp
    from app.api.impact import impact_bp
    from app.api.export import export_bp
    
    app.register_blueprint(metadata_bp, url_prefix='/api/v1/metadata')
    app.register_blueprint(data_bp, url_prefix='/api/v1/data')
    app.register_blueprint(analysis_bp, url_prefix='/api/v1/analysis')
    app.register_blueprint(geo_bp, url_prefix='/api/v1/geo')
    app.register_blueprint(forecast_bp, url_prefix='/api/v1/forecast')
    app.register_blueprint(scenarios_bp, url_prefix='/api/v1/scenarios')
    app.register_blueprint(impact_bp, url_prefix='/api/v1/impact')
    app.register_blueprint(export_bp, url_prefix='/api/v1/export')
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'himclimx-api'}
    
    @app.route('/')
    def index():
        return {
            'name': 'HimClimX API',
            'version': '1.0.0',
            'description': 'Himalayan Climate Dashboard Backend',
            'endpoints': {
                'metadata': '/api/v1/metadata',
                'data': '/api/v1/data',
                'analysis': '/api/v1/analysis',
                'geo': '/api/v1/geo',
                'forecast': '/api/v1/forecast',
                'scenarios': '/api/v1/scenarios',
                'impact': '/api/v1/impact',
                'export': '/api/v1/export'
            },
            'documentation': '/api/v1/docs'
        }
    
    return app
