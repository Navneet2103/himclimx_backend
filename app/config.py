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
    
    # Climate variables configuration
    CLIMATE_VARIABLES = {
        'tmp': {
            'name': 'Mean Temperature',
            'long_name': 'Near-Surface Air Temperature',
            'unit': '°C',
            'color': '#FF6B6B',
            'icon': '🌡️',
            'description': 'Monthly mean near-surface air temperature',
            'normal_range': [-20, 40],
            'impact_factor': 8.5,
            'climate_sensitivity': 'High'
        },
        'tmx': {
            'name': 'Maximum Temperature',
            'long_name': 'Maximum Near-Surface Air Temperature',
            'unit': '°C',
            'color': '#FF4757',
            'icon': '🔥',
            'description': 'Monthly maximum near-surface air temperature',
            'normal_range': [-10, 50],
            'impact_factor': 9.0,
            'climate_sensitivity': 'High'
        },
        'tmn': {
            'name': 'Minimum Temperature',
            'long_name': 'Minimum Near-Surface Air Temperature',
            'unit': '°C',
            'color': '#3742FA',
            'icon': '❄️',
            'description': 'Monthly minimum near-surface air temperature',
            'normal_range': [-30, 30],
            'impact_factor': 8.0,
            'climate_sensitivity': 'High'
        },
        'pre': {
            'name': 'Precipitation',
            'long_name': 'Total Precipitation',
            'unit': 'mm/month',
            'color': '#2ED573',
            'icon': '🌧️',
            'description': 'Monthly total precipitation',
            'normal_range': [0, 500],
            'impact_factor': 7.5,
            'climate_sensitivity': 'Medium'
        },
        'cld': {
            'name': 'Cloud Cover',
            'long_name': 'Total Cloud Cover',
            'unit': '%',
            'color': '#A4B0BE',
            'icon': '☁️',
            'description': 'Monthly mean cloud cover percentage',
            'normal_range': [0, 100],
            'impact_factor': 5.0,
            'climate_sensitivity': 'Medium'
        },
        'dtr': {
            'name': 'Diurnal Temp Range',
            'long_name': 'Diurnal Temperature Range',
            'unit': '°C',
            'color': '#FFA502',
            'icon': '📊',
            'description': 'Monthly mean diurnal temperature range',
            'normal_range': [0, 30],
            'impact_factor': 6.5,
            'climate_sensitivity': 'Medium'
        },
        'wet': {
            'name': 'Wet Days',
            'long_name': 'Number of Wet Days',
            'unit': 'days/month',
            'color': '#1E90FF',
            'icon': '💧',
            'description': 'Number of days with precipitation >= 0.1mm',
            'normal_range': [0, 31],
            'impact_factor': 6.0,
            'climate_sensitivity': 'Medium'
        },
        'vap': {
            'name': 'Vapor Pressure',
            'long_name': 'Water Vapor Pressure',
            'unit': 'hPa',
            'color': '#9C88FF',
            'icon': '💨',
            'description': 'Monthly mean water vapor pressure',
            'normal_range': [0, 50],
            'impact_factor': 7.0,
            'climate_sensitivity': 'Medium'
        },
        'pet': {
            'name': 'Evapotranspiration',
            'long_name': 'Potential Evapotranspiration',
            'unit': 'mm/month',
            'color': '#F8B500',
            'icon': '🌿',
            'description': 'Monthly potential evapotranspiration',
            'normal_range': [0, 200],
            'impact_factor': 7.5,
            'climate_sensitivity': 'High'
        },
        'frs': {
            'name': 'Frost Days',
            'long_name': 'Number of Frost Days',
            'unit': 'days/month',
            'color': '#70A1FF',
            'icon': '🧊',
            'description': 'Number of days with minimum temperature < 0°C',
            'normal_range': [0, 31],
            'impact_factor': 6.0,
            'climate_sensitivity': 'Medium'
        }
    }
    
    # Regions configuration with bounds for spatial queries
    REGIONS = {
        'E2000': {
            'name': 'Eastern Valleys',
            'zone': 'Eastern',
            'elevation_range': '1000-2000m',
            'color': '#FF6B6B',
            'center': [27.5, 88.5],
            'bounds': {'north': 28.0, 'south': 27.0, 'east': 89.0, 'west': 88.0},
            'description': 'Eastern Himalayan low elevation zone',
            'climate_zone': 'Subtropical',
            'vulnerability_index': 7.2,
            'biodiversity': 'High',
            'glacier_coverage': 'Low'
        },
        'E4000': {
            'name': 'Eastern Hills',
            'zone': 'Eastern',
            'elevation_range': '2000-4000m',
            'color': '#FF5722',
            'center': [27.8, 88.3],
            'bounds': {'north': 28.3, 'south': 27.3, 'east': 88.8, 'west': 87.8},
            'description': 'Eastern Himalayan mid elevation zone',
            'climate_zone': 'Temperate',
            'vulnerability_index': 6.8,
            'biodiversity': 'Very High',
            'glacier_coverage': 'Medium'
        },
        'E6000': {
            'name': 'Eastern Peaks',
            'zone': 'Eastern',
            'elevation_range': '4000-6000m',
            'color': '#FF3D00',
            'center': [28.0, 88.0],
            'bounds': {'north': 28.5, 'south': 27.5, 'east': 88.5, 'west': 87.5},
            'description': 'Eastern Himalayan high elevation zone',
            'climate_zone': 'Alpine',
            'vulnerability_index': 5.5,
            'biodiversity': 'Medium',
            'glacier_coverage': 'High'
        },
        'C2000': {
            'name': 'Central Valleys',
            'zone': 'Central',
            'elevation_range': '1000-2000m',
            'color': '#4CAF50',
            'center': [28.0, 84.5],
            'bounds': {'north': 28.5, 'south': 27.5, 'east': 85.0, 'west': 84.0},
            'description': 'Central Himalayan low elevation zone',
            'climate_zone': 'Subtropical',
            'vulnerability_index': 8.1,
            'biodiversity': 'High',
            'glacier_coverage': 'Low'
        },
        'C4000': {
            'name': 'Central Hills',
            'zone': 'Central',
            'elevation_range': '2000-4000m',
            'color': '#388E3C',
            'center': [28.3, 84.3],
            'bounds': {'north': 28.8, 'south': 27.8, 'east': 84.8, 'west': 83.8},
            'description': 'Central Himalayan mid elevation zone',
            'climate_zone': 'Temperate',
            'vulnerability_index': 7.5,
            'biodiversity': 'High',
            'glacier_coverage': 'Medium'
        },
        'C6000': {
            'name': 'Central Peaks',
            'zone': 'Central',
            'elevation_range': '4000-6000m',
            'color': '#2E7D32',
            'center': [28.5, 84.0],
            'bounds': {'north': 29.0, 'south': 28.0, 'east': 84.5, 'west': 83.5},
            'description': 'Central Himalayan high elevation zone',
            'climate_zone': 'Alpine',
            'vulnerability_index': 6.3,
            'biodiversity': 'Medium',
            'glacier_coverage': 'High'
        },
        'W2000': {
            'name': 'Western Valleys',
            'zone': 'Western',
            'elevation_range': '1000-2000m',
            'color': '#2196F3',
            'center': [32.0, 77.0],
            'bounds': {'north': 32.5, 'south': 31.5, 'east': 77.5, 'west': 76.5},
            'description': 'Western Himalayan low elevation zone',
            'climate_zone': 'Arid Subtropical',
            'vulnerability_index': 6.9,
            'biodiversity': 'Medium',
            'glacier_coverage': 'Low'
        },
        'W4000': {
            'name': 'Western Hills',
            'zone': 'Western',
            'elevation_range': '2000-4000m',
            'color': '#1976D2',
            'center': [32.3, 76.8],
            'bounds': {'north': 32.8, 'south': 31.8, 'east': 77.3, 'west': 76.3},
            'description': 'Western Himalayan mid elevation zone',
            'climate_zone': 'Temperate Arid',
            'vulnerability_index': 5.8,
            'biodiversity': 'Low',
            'glacier_coverage': 'Medium'
        },
        'W6000': {
            'name': 'Western Peaks',
            'zone': 'Western',
            'elevation_range': '4000-6000m',
            'color': '#1565C0',
            'center': [32.5, 76.5],
            'bounds': {'north': 33.0, 'south': 32.0, 'east': 77.0, 'west': 76.0},
            'description': 'Western Himalayan high elevation zone',
            'climate_zone': 'Cold Desert',
            'vulnerability_index': 4.7,
            'biodiversity': 'Low',
            'glacier_coverage': 'High'
        }
    }
    
    # SSP Climate Scenarios
    SSP_SCENARIOS = {
        'ssp1': {
            'name': 'SSP1-2.6 (Sustainability)',
            'description': 'Low emissions, sustainable development',
            'multiplier': 0.5,
            'color': '#10b981'
        },
        'ssp2': {
            'name': 'SSP2-4.5 (Middle of the Road)',
            'description': 'Moderate emissions, current trends continue',
            'multiplier': 1.0,
            'color': '#f59e0b'
        },
        'ssp3': {
            'name': 'SSP3-7.0 (Regional Rivalry)',
            'description': 'High emissions, regional conflicts',
            'multiplier': 1.5,
            'color': '#ef4444'
        },
        'ssp5': {
            'name': 'SSP5-8.5 (Fossil-fueled Development)',
            'description': 'Very high emissions, fossil fuel dependence',
            'multiplier': 2.0,
            'color': '#b91c1c'
        }
    }
    
    # Time range available in data
    DATA_START_YEAR = 1901
    DATA_END_YEAR = 2024
