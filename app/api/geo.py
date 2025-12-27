"""
Geo API Endpoints
=================
Endpoints for geographic data, regions, and map-related functionality.
"""

from flask import Blueprint, jsonify, request, Response
from app.services.data_service import data_service
from app.config import Config
import json

geo_bp = Blueprint('geo', __name__)
config = Config()


@geo_bp.route('/regions', methods=['GET'])
def get_all_regions():
    """
    Get GeoJSON for all regions combined.
    """
    try:
        geojson = data_service.load_all_regions_geojson()
        if geojson:
            return jsonify(geojson)
        else:
            return jsonify({'error': 'Failed to load regions GeoJSON'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@geo_bp.route('/regions/<region_code>', methods=['GET'])
def get_region_geojson(region_code):
    """
    Get GeoJSON for a specific region.
    
    Path Parameters:
        region_code (str): Region code (e.g., E2000, C4000)
    """
    region_code = region_code.upper()
    
    if region_code not in config.REGIONS:
        return jsonify({'error': f'Invalid region: {region_code}'}), 404
    
    try:
        geojson = data_service.load_region_geojson(region_code)
        if geojson:
            return jsonify(geojson)
        else:
            return jsonify({'error': f'GeoJSON not found for region {region_code}'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@geo_bp.route('/regions/index', methods=['GET'])
def get_regions_index():
    """
    Get regions index with metadata for all regions.
    """
    try:
        index = data_service.load_regions_index()
        if index:
            return jsonify(index)
        else:
            # Return config-based index if file not available
            return jsonify({
                'total_regions': len(config.REGIONS),
                'regions': [
                    {
                        'code': code,
                        **info
                    }
                    for code, info in config.REGIONS.items()
                ]
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@geo_bp.route('/bounds', methods=['GET'])
def get_bounds():
    """
    Get geographic bounds of the study area.
    """
    return jsonify({
        'himalayan_region': {
            'north': 37.0,
            'south': 26.0,
            'east': 97.0,
            'west': 73.0,
            'center': [31.5, 85.0]
        },
        'regions': {
            code: {
                'center': info['center'],
                'zone': info['zone']
            }
            for code, info in config.REGIONS.items()
        }
    })


@geo_bp.route('/dem/info', methods=['GET'])
def get_dem_info():
    """
    Get DEM (Digital Elevation Model) information.
    """
    return jsonify({
        'url': config.DEM_PATH,
        'format': 'Cloud-Optimized GeoTIFF (COG)',
        'coverage': 'Himalayan Region',
        'bounds': {
            'north': 37.0,
            'south': 26.0,
            'east': 97.0,
            'west': 73.0
        },
        'usage': {
            'description': 'Use with libraries like GeoTIFF.js or rasterio for client-side rendering',
            'recommended_libraries': [
                'geotiff (JavaScript)',
                'deck.gl TerrainLayer',
                'mapbox-gl terrain'
            ]
        }
    })


@geo_bp.route('/elevation-profile', methods=['GET'])
def get_elevation_profile():
    """
    Get elevation profile data for visualization.
    
    Query Parameters:
        start_lat (float): Start latitude
        start_lon (float): Start longitude
        end_lat (float): End latitude
        end_lon (float): End longitude
        points (int): Number of points (default: 100)
    """
    # This is a placeholder - actual implementation would
    # read from the DEM file
    return jsonify({
        'message': 'Elevation profile endpoint',
        'note': 'For full implementation, use client-side DEM reading with GeoTIFF.js',
        'dem_url': config.DEM_PATH
    })


@geo_bp.route('/map-config', methods=['GET'])
def get_map_config():
    """
    Get recommended map configuration for the dashboard.
    """
    return jsonify({
        'default_center': [31.5, 85.0],
        'default_zoom': 5,
        'min_zoom': 4,
        'max_zoom': 12,
        'bounds': [[26.0, 73.0], [37.0, 97.0]],
        'tile_layers': {
            'osm': {
                'url': 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
                'attribution': '© OpenStreetMap contributors'
            },
            'terrain': {
                'url': 'https://stamen-tiles-{s}.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png',
                'attribution': 'Map tiles by Stamen Design'
            },
            'satellite': {
                'url': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                'attribution': 'Esri World Imagery'
            }
        },
        'region_styles': {
            zone: {
                'fillColor': config.REGIONS[f'{zone[0].upper()}2000']['color'],
                'fillOpacity': 0.3,
                'color': config.REGIONS[f'{zone[0].upper()}2000']['color'],
                'weight': 2
            }
            for zone in ['Eastern', 'Central', 'Western']
        }
    })


@geo_bp.route('/3d-terrain-config', methods=['GET'])
def get_3d_terrain_config():
    """
    Get configuration for 3D terrain visualization.
    """
    return jsonify({
        'dem_url': config.DEM_PATH,
        'recommended_libraries': {
            'deck_gl': {
                'layer': 'TerrainLayer',
                'example': '''
import {TerrainLayer} from '@deck.gl/geo-layers';

const terrainLayer = new TerrainLayer({
  elevationDecoder: {
    rScaler: 256,
    gScaler: 1,
    bScaler: 1/256,
    offset: -32768
  },
  elevationData: 'DEM_URL',
  texture: 'SATELLITE_URL',
  bounds: [73, 26, 97, 37]
});
'''
            },
            'three_js': {
                'approach': 'Load COG as heightmap texture',
                'notes': 'Use geotiff.js to read elevation values'
            }
        },
        'visualization_settings': {
            'exaggeration': 1.5,
            'color_scale': {
                'type': 'elevation',
                'colors': ['#1a5276', '#27ae60', '#f1c40f', '#e74c3c', '#ffffff'],
                'breaks': [0, 2000, 4000, 6000, 8000]
            }
        }
    })


@geo_bp.route('/heatmap-data', methods=['GET'])
def get_heatmap_data():
    """
    Get data formatted for heatmap visualization.
    
    Query Parameters:
        variable (str): Climate variable (required)
        time (str): Time slice (required)
    """
    variable = request.args.get('variable')
    time_slice = request.args.get('time')
    
    if not variable or not time_slice:
        return jsonify({'error': 'variable and time are required'}), 400
    
    try:
        spatial = data_service.get_spatial_data(
            variable=variable,
            time_slice=time_slice
        )
        
        # Convert to heatmap format
        heatmap_data = []
        lats = spatial['lat']
        lons = spatial['lon']
        values = spatial['values']
        
        for i, lat in enumerate(lats):
            for j, lon in enumerate(lons):
                val = values[i][j]
                if val != -9999:  # Skip no-data values
                    heatmap_data.append({
                        'lat': lat,
                        'lon': lon,
                        'value': val
                    })
        
        return jsonify({
            'variable': variable,
            'time': time_slice,
            'data': heatmap_data,
            'statistics': spatial['statistics']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
