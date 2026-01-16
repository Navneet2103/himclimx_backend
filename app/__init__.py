"""
HimClimX Flask Application Factory
==================================
"""
from flask import Flask, jsonify
from flask_cors import CORS
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)

    # Enable CORS for all routes - FIXED
    CORS(app,
         origins=["https://himclimx.com", "https://www.himclimx.com", "http://localhost:3000", "*"],
         methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
         allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
         supports_credentials=True)

    # Register blueprints
    from app.api.metadata import metadata_bp
    from app.api.data import data_bp
    from app.api.analysis import analysis_bp
    from app.api.forecast import forecast_bp
    from app.api.impact import impact_bp
    from app.api.scenarios import scenarios_bp  # ADD THIS

    app.register_blueprint(metadata_bp, url_prefix='/api/v1/metadata')
    app.register_blueprint(data_bp, url_prefix='/api/v1/data')
    app.register_blueprint(analysis_bp, url_prefix='/api/v1/analysis')
    app.register_blueprint(forecast_bp, url_prefix='/api/v1/forecast')
    app.register_blueprint(impact_bp, url_prefix='/api/v1/impact')
    app.register_blueprint(scenarios_bp, url_prefix='/api/v1/scenarios')  # ADD THIS

    # Root endpoint
    @app.route('/')
    def index():
        return jsonify({
            'name': 'HimClimX API',
            'version': '2.0.0',
            'description': 'Himalayan Climate Dashboard Backend',
            'documentation': '/api/v1/docs',
            'endpoints': {
                'metadata': '/api/v1/metadata',
                'data': '/api/v1/data',
                'analysis': '/api/v1/analysis',
                'forecast': '/api/v1/forecast',
                'impact': '/api/v1/impact',
                'scenarios': '/api/v1/scenarios'  # ADD THIS
            }
        })

    # Health check
    @app.route('/health')
    def health():
        return jsonify({
            'status': 'healthy',
            'version': '2.0.0'
        })

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"Server error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

    logger.info("HimClimX API initialized successfully")
    return app