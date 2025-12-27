# HimClimX Backend API

Flask-based REST API for the Himalayan Climate Dashboard.

## Features

- **Climate Data Access**: Fetch climate data from Cloudflare R2 (Zarr format)
- **Time Series Analysis**: Trend analysis, anomaly detection, seasonal decomposition
- **Forecasting**: Prophet-based predictions and SSP scenario projections
- **Impact Assessment**: Risk scoring, vulnerability analysis, recommendations
- **Geographic Data**: Region boundaries, DEM info, 3D terrain config
- **Data Export**: CSV, JSON, and comprehensive reports

## API Endpoints

### Metadata
- `GET /api/v1/metadata/variables` - List all climate variables
- `GET /api/v1/metadata/regions` - List all regions
- `GET /api/v1/metadata/scenarios` - List SSP scenarios
- `GET /api/v1/metadata/summary` - Complete metadata summary

### Data
- `GET /api/v1/data/timeseries` - Point time series
- `GET /api/v1/data/regional` - Regional mean time series
- `GET /api/v1/data/spatial` - Spatial grid data
- `GET /api/v1/data/climatology` - Monthly climatology
- `GET /api/v1/data/annual` - Annual aggregated data

### Analysis
- `GET/POST /api/v1/analysis/trend` - Trend analysis
- `GET/POST /api/v1/analysis/anomalies` - Anomaly detection
- `GET/POST /api/v1/analysis/seasonal` - Seasonal decomposition
- `GET/POST /api/v1/analysis/statistics` - Statistical analysis
- `GET/POST /api/v1/analysis/compare-periods` - Period comparison

### Forecast
- `GET/POST /api/v1/forecast/prophet` - Prophet forecasting
- `GET/POST /api/v1/forecast/scenarios` - SSP scenario projections
- `GET /api/v1/forecast/summary` - Multi-variable forecast summary

### Scenarios
- `GET /api/v1/scenarios/` - List all scenarios
- `GET /api/v1/scenarios/projection` - Get projections
- `GET /api/v1/scenarios/compare` - Compare scenarios
- `GET /api/v1/scenarios/timeline` - Scenario timeline

### Impact
- `GET/POST /api/v1/impact/risk-assessment` - Climate risk assessment
- `GET/POST /api/v1/impact/sector-vulnerability` - Sector vulnerability
- `GET /api/v1/impact/regional-comparison` - Compare regions
- `GET /api/v1/impact/recommendations` - Adaptation recommendations

### Geographic
- `GET /api/v1/geo/regions` - All regions GeoJSON
- `GET /api/v1/geo/regions/<code>` - Single region GeoJSON
- `GET /api/v1/geo/map-config` - Map configuration
- `GET /api/v1/geo/3d-terrain-config` - 3D terrain configuration

### Export
- `GET /api/v1/export/csv` - Export as CSV
- `GET /api/v1/export/json` - Export as JSON
- `GET/POST /api/v1/export/report` - Generate comprehensive report

## Quick Start

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env

# Run development server
flask run
# or
python run.py
```

### Deploy to Railway

1. Push code to GitHub
2. Connect repository to Railway
3. Set environment variables:
   - `R2_PUBLIC_URL`: Your Cloudflare R2 public URL
   - `SECRET_KEY`: Random secret key
4. Deploy!

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `R2_PUBLIC_URL` | Cloudflare R2 public URL | Required |
| `R2_BUCKET_NAME` | R2 bucket name | `himclimx` |
| `SECRET_KEY` | Flask secret key | (generated) |
| `FLASK_DEBUG` | Enable debug mode | `false` |
| `OPENAI_CHAT_URL` | Climate chat URL | - |
| `REDIS_URL` | Redis cache URL | - |

## Climate Variables

| Code | Name | Unit |
|------|------|------|
| `tmp` | Mean Temperature | °C |
| `tmx` | Maximum Temperature | °C |
| `tmn` | Minimum Temperature | °C |
| `pre` | Precipitation | mm/month |
| `cld` | Cloud Cover | % |
| `dtr` | Diurnal Temp Range | °C |
| `wet` | Wet Days | days/month |
| `vap` | Vapor Pressure | hPa |
| `pet` | Evapotranspiration | mm/month |
| `frs` | Frost Days | days/month |

## Regions

| Code | Name | Elevation |
|------|------|-----------|
| E2000 | Eastern Valleys | 1000-2000m |
| E4000 | Eastern Hills | 2000-4000m |
| E6000 | Eastern Peaks | 4000-6000m |
| C2000 | Central Valleys | 1000-2000m |
| C4000 | Central Hills | 2000-4000m |
| C6000 | Central Peaks | 4000-6000m |
| W2000 | Western Valleys | 1000-2000m |
| W4000 | Western Hills | 2000-4000m |
| W6000 | Western Peaks | 4000-6000m |

## Project Structure

```
himclimx_backend/
├── app/
│   ├── __init__.py          # Application factory
│   ├── config.py            # Configuration
│   ├── api/
│   │   ├── metadata.py      # Metadata endpoints
│   │   ├── data.py          # Data endpoints
│   │   ├── analysis.py      # Analysis endpoints
│   │   ├── forecast.py      # Forecast endpoints
│   │   ├── scenarios.py     # Scenarios endpoints
│   │   ├── impact.py        # Impact endpoints
│   │   ├── geo.py           # Geographic endpoints
│   │   └── export.py        # Export endpoints
│   └── services/
│       ├── data_service.py      # Data loading
│       ├── analysis_service.py  # Analysis
│       ├── forecast_service.py  # Forecasting
│       └── impact_service.py    # Impact assessment
├── run.py                   # Entry point
├── requirements.txt         # Dependencies
├── Procfile                 # Heroku/Railway
├── railway.toml             # Railway config
└── .env.example             # Environment template
```

## License

MIT License
