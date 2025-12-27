"""
Data Service
============
Service for loading and processing climate data from Cloudflare R2.
Uses xarray with Zarr for efficient cloud-based data access.
"""

import xarray as xr
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import requests
from functools import lru_cache
import json

from app.config import Config


class DataService:
    """Service for loading and processing climate data from R2"""
    
    def __init__(self):
        self.config = Config()
        self.zarr_base = self.config.ZARR_BASE_PATH
        self.geojson_base = self.config.GEOJSON_BASE_PATH
        self._dataset_cache = {}
    
    def get_zarr_url(self, variable: str) -> str:
        """Get the Zarr store URL for a variable"""
        return f"{self.zarr_base}/{variable}_himalayas.zarr"
    
    @lru_cache(maxsize=20)
    def load_dataset(self, variable: str) -> xr.Dataset:
        """
        Load a climate variable dataset from R2 Zarr store.
        Uses caching to avoid repeated downloads.
        """
        zarr_url = self.get_zarr_url(variable)
        
        try:
            # Open Zarr store from HTTP URL
            ds = xr.open_zarr(zarr_url, consolidated=True)
            return ds
        except Exception as e:
            raise Exception(f"Failed to load dataset for {variable}: {str(e)}")
    
    def get_timeseries(
        self,
        variable: str,
        lat: float,
        lon: float,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Extract time series for a specific location.
        
        Args:
            variable: Climate variable code (e.g., 'tmp', 'pre')
            lat: Latitude
            lon: Longitude
            start_year: Start year for filtering
            end_year: End year for filtering
        
        Returns:
            Dictionary with time series data and statistics
        """
        ds = self.load_dataset(variable)
        
        # Select nearest point
        data = ds[variable].sel(lat=lat, lon=lon, method='nearest')
        
        # Filter by time if specified
        if start_year:
            data = data.sel(time=data.time.dt.year >= start_year)
        if end_year:
            data = data.sel(time=data.time.dt.year <= end_year)
        
        # Convert to pandas for easier manipulation
        df = data.to_dataframe().reset_index()
        
        # Calculate statistics
        values = df[variable].dropna()
        
        return {
            'variable': variable,
            'variable_info': self.config.CLIMATE_VARIABLES.get(variable, {}),
            'location': {'lat': float(data.lat), 'lon': float(data.lon)},
            'time_range': {
                'start': df['time'].min().isoformat(),
                'end': df['time'].max().isoformat()
            },
            'data': {
                'times': df['time'].dt.strftime('%Y-%m-%d').tolist(),
                'values': df[variable].round(3).tolist()
            },
            'statistics': {
                'mean': round(float(values.mean()), 3),
                'std': round(float(values.std()), 3),
                'min': round(float(values.min()), 3),
                'max': round(float(values.max()), 3),
                'median': round(float(values.median()), 3),
                'count': int(len(values))
            }
        }
    
    def get_regional_timeseries(
        self,
        variable: str,
        region: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        aggregation: str = 'mean'
    ) -> Dict[str, Any]:
        """
        Get time series averaged over a region.
        
        Args:
            variable: Climate variable code
            region: Region code (e.g., 'E2000', 'C4000')
            start_year: Start year
            end_year: End year
            aggregation: Aggregation method ('mean', 'min', 'max', 'sum')
        """
        ds = self.load_dataset(variable)
        
        # Load region geometry
        region_geojson = self.load_region_geojson(region)
        
        if region_geojson:
            # Get region bounds for simple rectangular selection
            # For more accurate masking, you'd use regionmask or rasterio
            bounds = self._get_bounds_from_geojson(region_geojson)
            
            # Select region
            data = ds[variable].sel(
                lat=slice(bounds['south'], bounds['north']),
                lon=slice(bounds['west'], bounds['east'])
            )
        else:
            data = ds[variable]
        
        # Filter by time
        if start_year:
            data = data.sel(time=data.time.dt.year >= start_year)
        if end_year:
            data = data.sel(time=data.time.dt.year <= end_year)
        
        # Spatial aggregation
        if aggregation == 'mean':
            regional_data = data.mean(dim=['lat', 'lon'])
        elif aggregation == 'min':
            regional_data = data.min(dim=['lat', 'lon'])
        elif aggregation == 'max':
            regional_data = data.max(dim=['lat', 'lon'])
        elif aggregation == 'sum':
            regional_data = data.sum(dim=['lat', 'lon'])
        else:
            regional_data = data.mean(dim=['lat', 'lon'])
        
        # Convert to dataframe
        df = regional_data.to_dataframe().reset_index()
        values = df[variable].dropna()
        
        return {
            'variable': variable,
            'variable_info': self.config.CLIMATE_VARIABLES.get(variable, {}),
            'region': region,
            'region_info': self.config.REGIONS.get(region, {}),
            'aggregation': aggregation,
            'time_range': {
                'start': df['time'].min().isoformat(),
                'end': df['time'].max().isoformat()
            },
            'data': {
                'times': df['time'].dt.strftime('%Y-%m-%d').tolist(),
                'values': df[variable].round(3).tolist()
            },
            'statistics': {
                'mean': round(float(values.mean()), 3),
                'std': round(float(values.std()), 3),
                'min': round(float(values.min()), 3),
                'max': round(float(values.max()), 3),
                'median': round(float(values.median()), 3),
                'count': int(len(values))
            }
        }
    
    def get_spatial_data(
        self,
        variable: str,
        time_slice: str,
        lat_range: Optional[Tuple[float, float]] = None,
        lon_range: Optional[Tuple[float, float]] = None
    ) -> Dict[str, Any]:
        """
        Get spatial grid data for a specific time.
        
        Args:
            variable: Climate variable
            time_slice: Time string (e.g., '2020-01-01')
            lat_range: Latitude range tuple (min, max)
            lon_range: Longitude range tuple (min, max)
        """
        ds = self.load_dataset(variable)
        
        # Select time
        data = ds[variable].sel(time=time_slice, method='nearest')
        
        # Subset spatially if specified
        if lat_range:
            data = data.sel(lat=slice(lat_range[0], lat_range[1]))
        if lon_range:
            data = data.sel(lon=slice(lon_range[0], lon_range[1]))
        
        # Convert to list format for JSON serialization
        return {
            'variable': variable,
            'variable_info': self.config.CLIMATE_VARIABLES.get(variable, {}),
            'time': str(data.time.values),
            'lat': data.lat.values.tolist(),
            'lon': data.lon.values.tolist(),
            'values': np.nan_to_num(data.values, nan=-9999).tolist(),
            'bounds': {
                'lat_min': float(data.lat.min()),
                'lat_max': float(data.lat.max()),
                'lon_min': float(data.lon.min()),
                'lon_max': float(data.lon.max())
            },
            'statistics': {
                'mean': round(float(np.nanmean(data.values)), 3),
                'min': round(float(np.nanmin(data.values)), 3),
                'max': round(float(np.nanmax(data.values)), 3)
            }
        }
    
    def get_monthly_climatology(
        self,
        variable: str,
        region: Optional[str] = None,
        start_year: int = 1991,
        end_year: int = 2020
    ) -> Dict[str, Any]:
        """
        Calculate monthly climatology (long-term monthly means).
        """
        ds = self.load_dataset(variable)
        data = ds[variable]
        
        # Filter years
        data = data.sel(time=(data.time.dt.year >= start_year) & (data.time.dt.year <= end_year))
        
        # If region specified, subset and average
        if region:
            region_geojson = self.load_region_geojson(region)
            if region_geojson:
                bounds = self._get_bounds_from_geojson(region_geojson)
                data = data.sel(
                    lat=slice(bounds['south'], bounds['north']),
                    lon=slice(bounds['west'], bounds['east'])
                )
            data = data.mean(dim=['lat', 'lon'])
        else:
            data = data.mean(dim=['lat', 'lon'])
        
        # Calculate monthly means
        monthly_clim = data.groupby('time.month').mean()
        
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        return {
            'variable': variable,
            'variable_info': self.config.CLIMATE_VARIABLES.get(variable, {}),
            'region': region,
            'reference_period': f'{start_year}-{end_year}',
            'data': {
                'months': months,
                'values': [round(float(monthly_clim.sel(month=i+1)), 3) for i in range(12)]
            }
        }
    
    def get_annual_timeseries(
        self,
        variable: str,
        region: Optional[str] = None,
        aggregation: str = 'mean'
    ) -> Dict[str, Any]:
        """
        Get annual aggregated time series.
        """
        ds = self.load_dataset(variable)
        data = ds[variable]
        
        # Regional averaging if specified
        if region:
            region_geojson = self.load_region_geojson(region)
            if region_geojson:
                bounds = self._get_bounds_from_geojson(region_geojson)
                data = data.sel(
                    lat=slice(bounds['south'], bounds['north']),
                    lon=slice(bounds['west'], bounds['east'])
                )
            data = data.mean(dim=['lat', 'lon'])
        else:
            data = data.mean(dim=['lat', 'lon'])
        
        # Annual aggregation
        if aggregation == 'mean':
            annual = data.groupby('time.year').mean()
        elif aggregation == 'sum':
            annual = data.groupby('time.year').sum()
        elif aggregation == 'max':
            annual = data.groupby('time.year').max()
        elif aggregation == 'min':
            annual = data.groupby('time.year').min()
        else:
            annual = data.groupby('time.year').mean()
        
        years = annual.year.values.tolist()
        values = [round(float(v), 3) if not np.isnan(v) else None for v in annual.values]
        
        return {
            'variable': variable,
            'variable_info': self.config.CLIMATE_VARIABLES.get(variable, {}),
            'region': region,
            'aggregation': aggregation,
            'data': {
                'years': years,
                'values': values
            },
            'statistics': {
                'mean': round(float(np.nanmean(annual.values)), 3),
                'std': round(float(np.nanstd(annual.values)), 3),
                'min': round(float(np.nanmin(annual.values)), 3),
                'max': round(float(np.nanmax(annual.values)), 3)
            }
        }
    
    def load_region_geojson(self, region: str) -> Optional[Dict]:
        """Load GeoJSON for a specific region from R2"""
        url = f"{self.geojson_base}/{region.lower()}.geojson"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        
        return None
    
    def load_all_regions_geojson(self) -> Optional[Dict]:
        """Load combined GeoJSON with all regions"""
        url = f"{self.geojson_base}/all_regions.geojson"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        
        return None
    
    def load_regions_index(self) -> Optional[Dict]:
        """Load regions index with metadata"""
        url = f"{self.geojson_base}/regions_index.json"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        
        return None
    
    def _get_bounds_from_geojson(self, geojson: Dict) -> Dict[str, float]:
        """Extract bounding box from GeoJSON"""
        if 'bbox' in geojson:
            bbox = geojson['bbox']
            return {
                'west': bbox[0],
                'south': bbox[1],
                'east': bbox[2],
                'north': bbox[3]
            }
        
        # Calculate from features
        coords = []
        features = geojson.get('features', [geojson])
        
        for feature in features:
            geometry = feature.get('geometry', feature)
            if geometry['type'] == 'Polygon':
                coords.extend(geometry['coordinates'][0])
            elif geometry['type'] == 'MultiPolygon':
                for poly in geometry['coordinates']:
                    coords.extend(poly[0])
        
        if coords:
            lons = [c[0] for c in coords]
            lats = [c[1] for c in coords]
            return {
                'west': min(lons),
                'south': min(lats),
                'east': max(lons),
                'north': max(lats)
            }
        
        # Default Himalayan bounds
        return {
            'west': 73.0,
            'south': 26.0,
            'east': 97.0,
            'north': 37.0
        }
    
    def compare_variables(
        self,
        variables: List[str],
        region: Optional[str] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Compare multiple variables over time.
        """
        results = {
            'variables': [],
            'region': region,
            'time_range': {'start': None, 'end': None}
        }
        
        for var in variables:
            ts = self.get_regional_timeseries(
                variable=var,
                region=region,
                start_year=start_year,
                end_year=end_year
            )
            results['variables'].append({
                'code': var,
                'info': ts['variable_info'],
                'data': ts['data'],
                'statistics': ts['statistics']
            })
            
            if results['time_range']['start'] is None:
                results['time_range'] = ts['time_range']
        
        return results


# Singleton instance
data_service = DataService()
