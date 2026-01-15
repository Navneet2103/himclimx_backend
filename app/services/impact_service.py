"""
Impact Service
==============
Service for climate impact assessment and recommendations.
"""

import numpy as np
from typing import Dict, List, Optional, Any
import logging

from app.config import Config

logger = logging.getLogger(__name__)


class ImpactService:
    """Service for climate impact assessment"""
    
    def __init__(self):
        self.config = Config()
    
    def assess_impact(
        self,
        variable: str,
        region: str,
        trend_per_decade: Optional[float] = None,
        current_value: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Assess climate impacts based on variable trends.
        """
        var_info = self.config.CLIMATE_VARIABLES.get(variable, {})
        region_info = self.config.REGIONS.get(region.upper(), {})
        
        impact = {
            'risk_level': 'low',
            'risk_score': 0.0,
            'impact_areas': [],
            'recommendations': [],
            'sector_vulnerability': {}
        }
        
        if not var_info:
            return impact
        
        # Base vulnerability from region
        base_vulnerability = region_info.get('vulnerability_index', 5.0)
        
        # Calculate risk score based on variable and trend
        risk_score = base_vulnerability
        
        # Temperature-related impacts
        if variable in ['tmp', 'tmx', 'tmn']:
            if trend_per_decade and trend_per_decade > 0.2:
                risk_score += 2.0
                impact['impact_areas'].extend([
                    'Heat stress on agriculture',
                    'Glacier melt acceleration',
                    'Ecosystem shifts',
                    'Water resource changes'
                ])
                impact['recommendations'].extend([
                    {'priority': 'high', 'action': 'Implement heat-resistant crop varieties', 'category': 'Agriculture'},
                    {'priority': 'high', 'action': 'Enhance water storage infrastructure', 'category': 'Water Resources'},
                    {'priority': 'medium', 'action': 'Develop early warning systems for extreme heat', 'category': 'Disaster Management'}
                ])
            
            if variable == 'tmn' and trend_per_decade and trend_per_decade > 0.3:
                risk_score += 1.5
                impact['impact_areas'].append('Reduced frost protection for crops')
                impact['recommendations'].append(
                    {'priority': 'medium', 'action': 'Adjust planting schedules for changing frost patterns', 'category': 'Agriculture'}
                )
        
        # Precipitation impacts
        elif variable == 'pre':
            if trend_per_decade:
                if abs(trend_per_decade) > 10:
                    risk_score += 2.0
                    if trend_per_decade > 0:
                        impact['impact_areas'].extend([
                            'Increased flood risk',
                            'Soil erosion',
                            'Landslide hazard'
                        ])
                        impact['recommendations'].extend([
                            {'priority': 'high', 'action': 'Strengthen flood protection measures', 'category': 'Infrastructure'},
                            {'priority': 'high', 'action': 'Implement soil conservation practices', 'category': 'Agriculture'},
                            {'priority': 'medium', 'action': 'Develop landslide early warning systems', 'category': 'Disaster Management'}
                        ])
                    else:
                        impact['impact_areas'].extend([
                            'Drought risk',
                            'Water scarcity',
                            'Agricultural stress'
                        ])
                        impact['recommendations'].extend([
                            {'priority': 'high', 'action': 'Invest in water conservation infrastructure', 'category': 'Water Resources'},
                            {'priority': 'high', 'action': 'Promote drought-resistant crops', 'category': 'Agriculture'},
                            {'priority': 'medium', 'action': 'Implement water rationing plans', 'category': 'Policy'}
                        ])
        
        # Frost days impacts
        elif variable == 'frs':
            if trend_per_decade and trend_per_decade < -1:
                risk_score += 1.0
                impact['impact_areas'].extend([
                    'Changes in pest dynamics',
                    'Altered growing seasons',
                    'Impact on cold-adapted species'
                ])
                impact['recommendations'].extend([
                    {'priority': 'medium', 'action': 'Monitor pest populations and disease patterns', 'category': 'Agriculture'},
                    {'priority': 'low', 'action': 'Adapt crop calendars to changing seasons', 'category': 'Agriculture'}
                ])
        
        # Evapotranspiration impacts
        elif variable == 'pet':
            if trend_per_decade and trend_per_decade > 5:
                risk_score += 1.5
                impact['impact_areas'].extend([
                    'Increased irrigation demand',
                    'Water stress on vegetation',
                    'Reduced soil moisture'
                ])
                impact['recommendations'].extend([
                    {'priority': 'high', 'action': 'Implement efficient irrigation systems', 'category': 'Agriculture'},
                    {'priority': 'medium', 'action': 'Promote mulching and soil moisture conservation', 'category': 'Agriculture'}
                ])
        
        # Cap risk score at 10
        risk_score = min(10.0, risk_score)
        
        # Determine risk level
        if risk_score >= 8:
            impact['risk_level'] = 'critical'
        elif risk_score >= 6:
            impact['risk_level'] = 'high'
        elif risk_score >= 4:
            impact['risk_level'] = 'moderate'
        else:
            impact['risk_level'] = 'low'
        
        impact['risk_score'] = round(risk_score, 1)
        
        # Calculate sector vulnerability
        impact['sector_vulnerability'] = {
            'agriculture': min(10, risk_score * 1.2) if variable in ['tmp', 'pre', 'pet', 'frs'] else risk_score * 0.8,
            'water_resources': min(10, risk_score * 1.3) if variable in ['pre', 'pet', 'tmp'] else risk_score * 0.7,
            'infrastructure': min(10, risk_score * 1.1) if variable == 'pre' else risk_score * 0.6,
            'biodiversity': min(10, risk_score * 1.0) if variable in ['tmp', 'tmn'] else risk_score * 0.8,
            'health': min(10, risk_score * 0.9) if variable in ['tmp', 'tmx'] else risk_score * 0.5
        }
        
        # Round sector vulnerability values
        impact['sector_vulnerability'] = {
            k: round(v, 1) for k, v in impact['sector_vulnerability'].items()
        }
        
        return impact


# Singleton instance
impact_service = ImpactService()
