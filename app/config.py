"""
HimClimX Configuration
======================
Configuration settings for the Flask backend.
"""

import os
from datetime import timedelta


class Config:
    """Base configuration"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'himclimx-secret-key-change-in-production')
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Cloudflare R2 Settings
    R2_PUBLIC_URL = os.environ.get(
        'R2_PUBLIC_URL', 
        'https://pub-e2d58bcf3d37484daaab4821c96b004a.r2.dev'
    )
    R2_BUCKET_NAME = os.environ.get('R2_BUCKET_NAME', 'himclimx')
    
    # Data paths (relative to R2 public URL)
    ZARR_BASE_PATH = f"{R2_PUBLIC_URL}/data/zarr"
    GEOJSON_BASE_PATH = f"{R2_PUBLIC_URL}/data/geojson"
    DEM_PATH = f"{R2_PUBLIC_URL}/data/dem/dem_cog.tif"
    
    # Cache settings
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'simple')  # 'redis' for production
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    CACHE_REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # API rate limiting
    RATELIMIT_DEFAULT = "100/minute"
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'memory://')
    
    # Climate variables configuration
    CLIMATE_VARIABLES = {
        'tmp': {
            'name': 'Mean Temperature',
            'long_name': 'Near-Surface Air Temperature',
            'unit': '°C',
            'color': '#FF6B6B',
            'icon': '🌡️',
            'description': 'Monthly mean near-surface air temperature'
        },
        'tmx': {
            'name': 'Maximum Temperature',
            'long_name': 'Maximum Near-Surface Air Temperature',
            'unit': '°C',
            'color': '#FF4757',
            'icon': '🔥',
            'description': 'Monthly maximum near-surface air temperature'
        },
        'tmn': {
            'name': 'Minimum Temperature',
            'long_name': 'Minimum Near-Surface Air Temperature',
            'unit': '°C',
            'color': '#3742FA',
            'icon': '❄️',
            'description': 'Monthly minimum near-surface air temperature'
        },
        'pre': {
            'name': 'Precipitation',
            'long_name': 'Total Precipitation',
            'unit': 'mm/month',
            'color': '#2ED573',
            'icon': '🌧️',
            'description': 'Monthly total precipitation'
        },
        'cld': {
            'name': 'Cloud Cover',
            'long_name': 'Total Cloud Cover',
            'unit': '%',
            'color': '#A4B0BE',
            'icon': '☁️',
            'description': 'Monthly mean cloud cover percentage'
        },
        'dtr': {
            'name': 'Diurnal Temp Range',
            'long_name': 'Diurnal Temperature Range',
            'unit': '°C',
            'color': '#FFA502',
            'icon': '📊',
            'description': 'Monthly mean diurnal temperature range'
        },
        'wet': {
            'name': 'Wet Days',
            'long_name': 'Number of Wet Days',
            'unit': 'days/month',
            'color': '#1E90FF',
            'icon': '💧',
            'description': 'Number of days with precipitation >= 0.1mm'
        },
        'vap': {
            'name': 'Vapor Pressure',
            'long_name': 'Water Vapor Pressure',
            'unit': 'hPa',
            'color': '#9C88FF',
            'icon': '💨',
            'description': 'Monthly mean water vapor pressure'
        },
        'pet': {
            'name': 'Evapotranspiration',
            'long_name': 'Potential Evapotranspiration',
            'unit': 'mm/month',
            'color': '#F8B500',
            'icon': '🌿',
            'description': 'Monthly potential evapotranspiration'
        },
        'frs': {
            'name': 'Frost Days',
            'long_name': 'Number of Frost Days',
            'unit': 'days/month',
            'color': '#70A1FF',
            'icon': '🧊',
            'description': 'Number of days with minimum temperature < 0°C'
        }
    }
    
    # Regions configuration
    REGIONS = {
        'E2000': {
            'name': 'Eastern Valleys',
            'zone': 'Eastern',
            'elevation_range': '1000-2000m',
            'color': '#FF6B6B',
            'center': [27.5, 88.5],
            'description': 'Eastern Himalayan low elevation zone'
        },
        'E4000': {
            'name': 'Eastern Hills',
            'zone': 'Eastern',
            'elevation_range': '2000-4000m',
            'color': '#FF5722',
            'center': [27.8, 88.3],
            'description': 'Eastern Himalayan mid elevation zone'
        },
        'E6000': {
            'name': 'Eastern Peaks',
            'zone': 'Eastern',
            'elevation_range': '4000-6000m',
            'color': '#FF3D00',
            'center': [28.0, 88.0],
            'description': 'Eastern Himalayan high elevation zone'
        },
        'C2000': {
            'name': 'Central Valleys',
            'zone': 'Central',
            'elevation_range': '1000-2000m',
            'color': '#4CAF50',
            'center': [28.0, 84.5],
            'description': 'Central Himalayan low elevation zone'
        },
        'C4000': {
            'name': 'Central Hills',
            'zone': 'Central',
            'elevation_range': '2000-4000m',
            'color': '#388E3C',
            'center': [28.3, 84.3],
            'description': 'Central Himalayan mid elevation zone'
        },
        'C6000': {
            'name': 'Central Peaks',
            'zone': 'Central',
            'elevation_range': '4000-6000m',
            'color': '#2E7D32',
            'center': [28.5, 84.0],
            'description': 'Central Himalayan high elevation zone'
        },
        'W2000': {
            'name': 'Western Valleys',
            'zone': 'Western',
            'elevation_range': '1000-2000m',
            'color': '#2196F3',
            'center': [32.0, 77.0],
            'description': 'Western Himalayan low elevation zone'
        },
        'W4000': {
            'name': 'Western Hills',
            'zone': 'Western',
            'elevation_range': '2000-4000m',
            'color': '#1976D2',
            'center': [32.3, 76.8],
            'description': 'Western Himalayan mid elevation zone'
        },
        'W6000': {
            'name': 'Western Peaks',
            'zone': 'Western',
            'elevation_range': '4000-6000m',
            'color': '#1565C0',
            'center': [32.5, 76.5],
            'description': 'Western Himalayan high elevation zone'
        }
    }
    
    # SSP Climate Scenarios
    SSP_SCENARIOS = {
        'SSP1': {
            'name': 'SSP1-2.6 (Sustainability)',
            'description': 'Low emissions, sustainable development',
            'temp_increase_2050': 1.5,
            'temp_increase_2100': 1.8,
            'color': '#4CAF50'
        },
        'SSP2': {
            'name': 'SSP2-4.5 (Middle of the Road)',
            'description': 'Moderate emissions, current trends continue',
            'temp_increase_2050': 2.0,
            'temp_increase_2100': 2.7,
            'color': '#FFC107'
        },
        'SSP3': {
            'name': 'SSP3-7.0 (Regional Rivalry)',
            'description': 'High emissions, regional conflicts',
            'temp_increase_2050': 2.4,
            'temp_increase_2100': 3.6,
            'color': '#FF9800'
        },
        'SSP5': {
            'name': 'SSP5-8.5 (Fossil-fueled Development)',
            'description': 'Very high emissions, fossil fuel dependence',
            'temp_increase_2050': 2.8,
            'temp_increase_2100': 4.4,
            'color': '#F44336'
        }
    }
    
    # Time range available in data
    DATA_START_YEAR = 1901
    DATA_END_YEAR = 2024
    
    # External services
    OPENAI_CHAT_URL = os.environ.get('OPENAI_CHAT_URL', 'https://your-climate-chat.vercel.app')
    
    # Google Maps API (optional, for enhanced maps)
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    CACHE_TYPE = 'simple'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    CACHE_TYPE = 'redis'


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    CACHE_TYPE = 'simple'


# Config selector
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
