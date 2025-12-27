"""
Impact Assessment Service
=========================
Service for climate impact assessment, vulnerability analysis,
and generating recommendations.
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from app.services.data_service import data_service
from app.services.analysis_service import analysis_service
from app.config import Config


class ImpactService:
    """Service for climate impact assessment"""
    
    def __init__(self):
        self.config = Config()
        self.data_service = data_service
        self.analysis_service = analysis_service
        
        # Impact thresholds
        self.thresholds = {
            'tmp': {
                'high': 35,      # High temperature stress
                'low': 5,        # Low temperature stress
                'change_concern': 1.5  # Concerning change per decade
            },
            'pre': {
                'drought': 50,   # mm/month - drought threshold
                'flood': 300,    # mm/month - flood risk
                'change_concern': 10  # % change per decade
            },
            'frs': {
                'high_risk': 15,  # High frost risk days
                'change_concern': -3  # Concerning reduction per decade
            },
            'pet': {
                'high': 150,     # High evapotranspiration
                'change_concern': 5
            }
        }
        
        # Sector impacts
        self.sectors = {
            'agriculture': {
                'variables': ['tmp', 'pre', 'frs', 'pet'],
                'weights': {'tmp': 0.3, 'pre': 0.35, 'frs': 0.2, 'pet': 0.15}
            },
            'water_resources': {
                'variables': ['pre', 'pet', 'tmp', 'wet'],
                'weights': {'pre': 0.4, 'pet': 0.25, 'tmp': 0.2, 'wet': 0.15}
            },
            'ecosystems': {
                'variables': ['tmp', 'pre', 'wet', 'vap'],
                'weights': {'tmp': 0.35, 'pre': 0.3, 'wet': 0.2, 'vap': 0.15}
            },
            'human_health': {
                'variables': ['tmp', 'tmx', 'pre', 'vap'],
                'weights': {'tmp': 0.25, 'tmx': 0.35, 'pre': 0.2, 'vap': 0.2}
            },
            'infrastructure': {
                'variables': ['pre', 'tmx', 'frs'],
                'weights': {'pre': 0.45, 'tmx': 0.3, 'frs': 0.25}
            }
        }
    
    def assess_climate_risk(
        self,
        region: str,
        variables: Optional[List[str]] = None,
        period: Tuple[int, int] = (1990, 2020)
    ) -> Dict[str, Any]:
        """
        Comprehensive climate risk assessment for a region.
        
        Args:
            region: Region code
            variables: List of variables to assess (default: all)
            period: Analysis period
        """
        if variables is None:
            variables = list(self.config.CLIMATE_VARIABLES.keys())
        
        risk_scores = {}
        trend_concerns = []
        extreme_events = []
        
        for var in variables:
            try:
                # Get trend analysis
                trend = self.analysis_service.compute_trend(
                    variable=var,
                    region=region,
                    start_year=period[0],
                    end_year=period[1]
                )
                
                if 'error' in trend:
                    continue
                
                # Get statistics
                stats = self.analysis_service.compute_statistics(
                    variable=var,
                    region=region,
                    start_year=period[0],
                    end_year=period[1]
                )
                
                # Calculate risk score (0-100)
                risk_score = self._calculate_variable_risk(var, trend, stats)
                risk_scores[var] = risk_score
                
                # Check for concerning trends
                per_decade = trend['linear_trend']['per_decade']
                threshold = self.thresholds.get(var, {}).get('change_concern', 1)
                
                if abs(per_decade) > abs(threshold):
                    trend_concerns.append({
                        'variable': var,
                        'variable_name': self.config.CLIMATE_VARIABLES[var]['name'],
                        'per_decade': round(per_decade, 3),
                        'threshold': threshold,
                        'direction': 'increasing' if per_decade > 0 else 'decreasing',
                        'significance': trend['linear_trend']['significant']
                    })
                
                # Check for extreme values
                extremes = self._check_extremes(var, stats)
                if extremes:
                    extreme_events.extend(extremes)
                    
            except Exception as e:
                continue
        
        # Calculate overall risk
        if risk_scores:
            overall_risk = np.mean(list(risk_scores.values()))
            risk_level = self._get_risk_level(overall_risk)
        else:
            overall_risk = 0
            risk_level = 'unknown'
        
        return {
            'region': region,
            'region_info': self.config.REGIONS.get(region, {}),
            'period': f'{period[0]}-{period[1]}',
            'overall_risk': {
                'score': round(overall_risk, 1),
                'level': risk_level,
                'color': self._get_risk_color(risk_level)
            },
            'variable_risks': {
                var: {
                    'score': round(score, 1),
                    'level': self._get_risk_level(score),
                    'variable_info': self.config.CLIMATE_VARIABLES.get(var, {})
                }
                for var, score in risk_scores.items()
            },
            'trend_concerns': trend_concerns,
            'extreme_events': extreme_events,
            'recommendations': self._generate_recommendations(risk_scores, trend_concerns, region)
        }
    
    def _calculate_variable_risk(
        self,
        variable: str,
        trend: Dict,
        stats: Dict
    ) -> float:
        """Calculate risk score for a single variable"""
        risk = 0
        
        # Trend component (0-40 points)
        if trend['linear_trend']['significant']:
            per_decade = abs(trend['linear_trend']['per_decade'])
            threshold = abs(self.thresholds.get(variable, {}).get('change_concern', 1))
            trend_risk = min(40, (per_decade / threshold) * 20)
            risk += trend_risk
        
        # Variability component (0-30 points)
        cv = stats['distribution'].get('cv', 0)
        if cv > 30:
            risk += 30
        elif cv > 20:
            risk += 20
        elif cv > 10:
            risk += 10
        
        # Extreme values component (0-30 points)
        thresholds = self.thresholds.get(variable, {})
        mean_val = stats['basic']['mean']
        max_val = stats['basic']['max']
        min_val = stats['basic']['min']
        
        if 'high' in thresholds and max_val > thresholds['high']:
            risk += 15
        if 'low' in thresholds and min_val < thresholds['low']:
            risk += 15
        
        return min(100, risk)
    
    def _check_extremes(self, variable: str, stats: Dict) -> List[Dict]:
        """Check for extreme values"""
        extremes = []
        thresholds = self.thresholds.get(variable, {})
        var_info = self.config.CLIMATE_VARIABLES.get(variable, {})
        
        if 'high' in thresholds:
            if stats['basic']['max'] > thresholds['high']:
                extremes.append({
                    'variable': variable,
                    'variable_name': var_info.get('name', variable),
                    'type': 'high_extreme',
                    'value': stats['basic']['max'],
                    'threshold': thresholds['high'],
                    'unit': var_info.get('unit', '')
                })
        
        if 'drought' in thresholds and variable == 'pre':
            if stats['percentiles']['p10'] < thresholds['drought']:
                extremes.append({
                    'variable': variable,
                    'variable_name': var_info.get('name', variable),
                    'type': 'drought_risk',
                    'value': stats['percentiles']['p10'],
                    'threshold': thresholds['drought'],
                    'unit': var_info.get('unit', '')
                })
        
        return extremes
    
    def _get_risk_level(self, score: float) -> str:
        """Convert risk score to level"""
        if score >= 70:
            return 'high'
        elif score >= 40:
            return 'moderate'
        elif score >= 20:
            return 'low'
        else:
            return 'minimal'
    
    def _get_risk_color(self, level: str) -> str:
        """Get color for risk level"""
        colors = {
            'high': '#F44336',
            'moderate': '#FF9800',
            'low': '#FFC107',
            'minimal': '#4CAF50',
            'unknown': '#9E9E9E'
        }
        return colors.get(level, '#9E9E9E')
    
    def _generate_recommendations(
        self,
        risk_scores: Dict[str, float],
        trend_concerns: List[Dict],
        region: str
    ) -> List[Dict]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Temperature recommendations
        if risk_scores.get('tmp', 0) > 40 or risk_scores.get('tmx', 0) > 40:
            recommendations.append({
                'category': 'Heat Stress',
                'priority': 'high' if risk_scores.get('tmx', 0) > 60 else 'medium',
                'actions': [
                    'Implement heat action plans for vulnerable populations',
                    'Develop heat-tolerant crop varieties',
                    'Increase urban green spaces for cooling',
                    'Establish early warning systems for heat waves'
                ]
            })
        
        # Precipitation recommendations
        if risk_scores.get('pre', 0) > 40:
            recommendations.append({
                'category': 'Water Management',
                'priority': 'high',
                'actions': [
                    'Improve water storage and conservation infrastructure',
                    'Implement rainwater harvesting systems',
                    'Develop drought-resistant agricultural practices',
                    'Strengthen flood early warning systems'
                ]
            })
        
        # Frost recommendations
        if 'frs' in risk_scores:
            frs_concerns = [c for c in trend_concerns if c['variable'] == 'frs']
            if frs_concerns:
                recommendations.append({
                    'category': 'Frost and Cryosphere',
                    'priority': 'medium',
                    'actions': [
                        'Monitor glacier retreat and permafrost changes',
                        'Assess risks to high-altitude infrastructure',
                        'Develop adaptation strategies for changing snow patterns',
                        'Support communities dependent on glacial water'
                    ]
                })
        
        # General recommendations
        if any(c['significance'] for c in trend_concerns):
            recommendations.append({
                'category': 'Climate Monitoring',
                'priority': 'high',
                'actions': [
                    'Strengthen climate monitoring network in the region',
                    'Improve data collection and sharing systems',
                    'Develop regional climate projections',
                    'Build capacity for climate analysis'
                ]
            })
        
        # Ecosystem recommendations
        region_info = self.config.REGIONS.get(region, {})
        if region_info.get('elevation_range', '').startswith('4000'):
            recommendations.append({
                'category': 'High-Altitude Ecosystems',
                'priority': 'high',
                'actions': [
                    'Protect alpine meadows and wetlands',
                    'Monitor species distribution shifts',
                    'Establish wildlife corridors',
                    'Control invasive species spread'
                ]
            })
        
        return recommendations
    
    def sector_vulnerability(
        self,
        region: str,
        sector: str,
        period: Tuple[int, int] = (1990, 2020)
    ) -> Dict[str, Any]:
        """
        Assess vulnerability for a specific sector.
        """
        if sector not in self.sectors:
            return {'error': f'Unknown sector: {sector}. Available: {list(self.sectors.keys())}'}
        
        sector_config = self.sectors[sector]
        variables = sector_config['variables']
        weights = sector_config['weights']
        
        variable_impacts = {}
        weighted_score = 0
        total_weight = 0
        
        for var in variables:
            try:
                trend = self.analysis_service.compute_trend(
                    variable=var,
                    region=region,
                    start_year=period[0],
                    end_year=period[1]
                )
                
                if 'error' in trend:
                    continue
                
                stats = self.analysis_service.compute_statistics(
                    variable=var,
                    region=region,
                    start_year=period[0],
                    end_year=period[1]
                )
                
                risk_score = self._calculate_variable_risk(var, trend, stats)
                weight = weights.get(var, 0.1)
                
                variable_impacts[var] = {
                    'risk_score': round(risk_score, 1),
                    'weight': weight,
                    'weighted_contribution': round(risk_score * weight, 2),
                    'trend': {
                        'direction': 'increasing' if trend['linear_trend']['slope'] > 0 else 'decreasing',
                        'per_decade': round(trend['linear_trend']['per_decade'], 3),
                        'significant': trend['linear_trend']['significant']
                    }
                }
                
                weighted_score += risk_score * weight
                total_weight += weight
                
            except Exception:
                continue
        
        if total_weight > 0:
            vulnerability_score = weighted_score / total_weight
        else:
            vulnerability_score = 0
        
        return {
            'region': region,
            'region_info': self.config.REGIONS.get(region, {}),
            'sector': sector,
            'period': f'{period[0]}-{period[1]}',
            'vulnerability': {
                'score': round(vulnerability_score, 1),
                'level': self._get_risk_level(vulnerability_score),
                'color': self._get_risk_color(self._get_risk_level(vulnerability_score))
            },
            'variable_impacts': variable_impacts,
            'key_concerns': self._get_sector_concerns(sector, variable_impacts),
            'adaptation_measures': self._get_sector_adaptations(sector, vulnerability_score)
        }
    
    def _get_sector_concerns(
        self,
        sector: str,
        variable_impacts: Dict
    ) -> List[str]:
        """Get key concerns for a sector"""
        concerns = []
        
        for var, impact in variable_impacts.items():
            if impact['risk_score'] > 50 and impact['trend']['significant']:
                var_name = self.config.CLIMATE_VARIABLES.get(var, {}).get('name', var)
                direction = impact['trend']['direction']
                concerns.append(f"Significant {direction} trend in {var_name}")
        
        return concerns
    
    def _get_sector_adaptations(
        self,
        sector: str,
        vulnerability_score: float
    ) -> List[str]:
        """Get adaptation measures for a sector"""
        adaptations = {
            'agriculture': [
                'Diversify crop varieties for climate resilience',
                'Implement efficient irrigation systems',
                'Develop climate-smart agricultural practices',
                'Strengthen crop insurance programs'
            ],
            'water_resources': [
                'Increase water storage capacity',
                'Implement watershed management programs',
                'Promote water-efficient technologies',
                'Develop groundwater recharge initiatives'
            ],
            'ecosystems': [
                'Establish protected area networks',
                'Restore degraded ecosystems',
                'Implement species conservation programs',
                'Monitor biodiversity changes'
            ],
            'human_health': [
                'Strengthen disease surveillance systems',
                'Improve healthcare infrastructure',
                'Develop heat and cold action plans',
                'Enhance public awareness programs'
            ],
            'infrastructure': [
                'Update building codes for climate resilience',
                'Improve drainage systems',
                'Strengthen early warning systems',
                'Conduct vulnerability assessments'
            ]
        }
        
        return adaptations.get(sector, [])
    
    def regional_comparison(
        self,
        variable: str,
        period: Tuple[int, int] = (1990, 2020)
    ) -> Dict[str, Any]:
        """
        Compare all regions for a specific variable.
        """
        comparisons = []
        
        for region_code, region_info in self.config.REGIONS.items():
            try:
                trend = self.analysis_service.compute_trend(
                    variable=variable,
                    region=region_code,
                    start_year=period[0],
                    end_year=period[1]
                )
                
                if 'error' in trend:
                    continue
                
                stats = self.analysis_service.compute_statistics(
                    variable=variable,
                    region=region_code,
                    start_year=period[0],
                    end_year=period[1]
                )
                
                comparisons.append({
                    'region': region_code,
                    'region_info': region_info,
                    'mean': stats['basic']['mean'],
                    'std': stats['basic']['std'],
                    'trend_per_decade': trend['linear_trend']['per_decade'],
                    'trend_significant': trend['linear_trend']['significant'],
                    'risk_score': round(self._calculate_variable_risk(variable, trend, stats), 1)
                })
                
            except Exception:
                continue
        
        # Sort by risk score
        comparisons.sort(key=lambda x: x['risk_score'], reverse=True)
        
        return {
            'variable': variable,
            'variable_info': self.config.CLIMATE_VARIABLES.get(variable, {}),
            'period': f'{period[0]}-{period[1]}',
            'comparisons': comparisons,
            'highest_risk': comparisons[0]['region'] if comparisons else None,
            'lowest_risk': comparisons[-1]['region'] if comparisons else None
        }


# Singleton instance
impact_service = ImpactService()
