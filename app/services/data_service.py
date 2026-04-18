"""
Data Service
============
Service for loading and processing climate data from Cloudflare R2.
Uses xarray with Zarr and fsspec for cloud-based data access.
"""

import xarray as xr
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import fsspec
import logging

from app.config import Config

logger = logging.getLogger(__name__)


class DataService:
    """Service for loading and processing climate data from R2"""
    
    def __init__(self):
        self.config = Config()
        self.zarr_base = self.config.ZARR_BASE_PATH
        self._dataset_cache = {}
    
    def get_zarr_url(self, variable: str) -> str:
        """Get the Zarr store URL for a variable"""
        return f"{self.zarr_base}/{variable}_himalayas.zarr"
    
    def load_dataset(self, variable: str) -> xr.Dataset:
        """
        Load a climate variable dataset from R2 Zarr store.
        Uses fsspec for HTTP access to Zarr.
        """
        if variable in self._dataset_cache:
            return self._dataset_cache[variable]
        
        zarr_url = self.get_zarr_url(variable)
        
        try:
            # Use fsspec to create an HTTP filesystem mapper
            mapper = fsspec.get_mapper(zarr_url)
            
            # Open Zarr store
            ds = xr.open_zarr(mapper, consolidated=True)
            
            # Cache the dataset
            self._dataset_cache[variable] = ds
            
            logger.info(f"Successfully loaded dataset for {variable}")
            return ds
        except Exception as e:
            logger.error(f"Failed to load dataset for {variable}: {str(e)}")
            raise Exception(f"Failed to load dataset for {variable}: {str(e)}")
    
    def get_region_bounds(self, region: str) -> Dict[str, float]:
        """Get the spatial bounds for a region"""
        region_info = self.config.REGIONS.get(region.upper())
        if region_info and 'bounds' in region_info:
            return region_info['bounds']
        
        # Default Himalayan bounds
        return {
            'north': 37.0,
            'south': 26.0,
            'east': 97.0,
            'west': 73.0
        }
    
    def get_timeseries(
        self,
        variable: str,
        region: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        aggregation: str = 'mean'
    ) -> Dict[str, Any]:
        """
        Get time series data for a region.
        
        Args:
            variable: Climate variable code (e.g., 'tmp', 'pre')
            region: Region code (e.g., 'C4000', 'E2000')
            start_year: Start year for filtering
            end_year: End year for filtering
            aggregation: Aggregation method ('mean', 'min', 'max', 'sum')
        
        Returns:
            Dictionary with time series data and statistics
        """
        ds = self.load_dataset(variable)
        
        # Get region bounds
        bounds = self.get_region_bounds(region)
        
        # Select region and variable
        data = ds[variable].sel(
            lat=slice(bounds['south'], bounds['north']),
            lon=slice(bounds['west'], bounds['east'])
        )
        
        # Filter by time if specified
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
        
        # Convert to pandas for easier manipulation
        df = regional_data.to_dataframe().reset_index()
        df = df.dropna()
        
        # Get values
        times = df['time'].dt.strftime('%Y-%m-%d').tolist()
        values = [round(float(v), 3) if not np.isnan(v) else None for v in df[variable]]
        
        # Calculate statistics
        valid_values = [v for v in values if v is not None]
        
        return {
            'variable': variable,
            'variable_info': self.config.CLIMATE_VARIABLES.get(variable, {}),
            'region': region,
            'region_info': self.config.REGIONS.get(region.upper(), {}),
            'aggregation': aggregation,
            'time_range': {
                'start': times[0] if times else None,
                'end': times[-1] if times else None
            },
            'data': {
                'times': times,
                'values': values
            },
            'statistics': {
                'mean': round(float(np.mean(valid_values)), 3) if valid_values else None,
                'std': round(float(np.std(valid_values)), 3) if valid_values else None,
                'min': round(float(np.min(valid_values)), 3) if valid_values else None,
                'max': round(float(np.max(valid_values)), 3) if valid_values else None,
                'median': round(float(np.median(valid_values)), 3) if valid_values else None,
                'count': len(valid_values)
            }
        }
    
    def get_climatology(
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
        
        # Filter by region if specified
        if region:
            bounds = self.get_region_bounds(region)
            data = data.sel(
                lat=slice(bounds['south'], bounds['north']),
                lon=slice(bounds['west'], bounds['east'])
            )
        
        # Spatial mean
        data = data.mean(dim=['lat', 'lon'])
        
        # Filter years
        data = data.sel(time=(data.time.dt.year >= start_year) & (data.time.dt.year <= end_year))
        
        # Calculate monthly means and std
        monthly_mean = data.groupby('time.month').mean()
        monthly_std = data.groupby('time.month').std()
        
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        return {
            'variable': variable,
            'variable_info': self.config.CLIMATE_VARIABLES.get(variable, {}),
            'region': region,
            'reference_period': f'{start_year}-{end_year}',
            'data': {
                'months': months,
                'values': [round(float(monthly_mean.sel(month=i+1)), 3) for i in range(12)],
                'std': [round(float(monthly_std.sel(month=i+1)), 3) for i in range(12)]
            }
        }
    
    def get_annual_data(
        self,
        variable: str,
        region: Optional[str] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        aggregation: str = 'mean'
    ) -> Dict[str, Any]:
        """
        Get annual aggregated time series.
        """
        ds = self.load_dataset(variable)
        data = ds[variable]
        
        # Filter by region
        if region:
            bounds = self.get_region_bounds(region)
            data = data.sel(
                lat=slice(bounds['south'], bounds['north']),
                lon=slice(bounds['west'], bounds['east'])
            )
        
        # Spatial mean
        data = data.mean(dim=['lat', 'lon'])
        
        # Filter by time
        if start_year:
            data = data.sel(time=data.time.dt.year >= start_year)
        if end_year:
            data = data.sel(time=data.time.dt.year <= end_year)
        
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
            }
        }

    def get_spatial_data(
        self,
        variable: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get per-region climate mean for all 9 Himalayan regions.
        Loads the dataset once and extracts each region's spatiotemporal mean.
        Used to power the spatial heatmap visualization.
        """
        ds = self.load_dataset(variable)
        data = ds[variable]

        # Apply time filter once before slicing regions
        if start_year:
            data = data.sel(time=data.time.dt.year >= start_year)
        if end_year:
            data = data.sel(time=data.time.dt.year <= end_year)

        region_results = {}
        all_values = []

        for region_code, region_info in self.config.REGIONS.items():
            bounds = region_info['bounds']
            try:
                region_slice = data.sel(
                    lat=slice(bounds['south'], bounds['north']),
                    lon=slice(bounds['west'], bounds['east'])
                )
                raw = float(region_slice.mean(dim=['lat', 'lon', 'time']))
                value = round(raw, 3) if not np.isnan(raw) else None
            except Exception:
                value = None

            if value is not None:
                all_values.append(value)

            region_results[region_code] = {
                'value': value,
                'name': region_info['name'],
                'zone': region_info['zone'],
                'elevation_range': region_info['elevation_range'],
                'center': region_info['center'],
                'color': region_info['color'],
                'climate_zone': region_info['climate_zone'],
                'vulnerability_index': region_info['vulnerability_index'],
            }

        time_values = data.time.values
        return {
            'variable': variable,
            'variable_info': self.config.CLIMATE_VARIABLES.get(variable, {}),
            'time_range': {
                'start': str(pd.Timestamp(time_values[0]).date()) if len(time_values) > 0 else None,
                'end': str(pd.Timestamp(time_values[-1]).date()) if len(time_values) > 0 else None,
            },
            'regions': region_results,
            'value_range': {
                'min': round(min(all_values), 3) if all_values else None,
                'max': round(max(all_values), 3) if all_values else None,
            }
        }


# Singleton instance
data_service = DataService()
