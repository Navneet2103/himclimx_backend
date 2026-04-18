# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

HimClimX is a Himalayan climate data visualization dashboard built as part of Navneet Kumar's M.Tech thesis at BIT Mesra. It visualizes CRU (Climate Research Unit) gridded data for 1901–2024 across 9 Himalayan regions and 10 climate variables.

- **Frontend:** https://himclimx.com (Vercel) — repo: `github.com/Navneet2103/himclimx_frontend`
- **Backend:** https://web-production-6719e.up.railway.app (Railway) — repo: `github.com/Navneet2103/himclimx_backend`
- **Data:** ~6GB of Zarr-format CRU data on Cloudflare R2

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (dev)
python run.py

# Run with Gunicorn (matches production)
gunicorn run:app --bind 0.0.0.0:5000 --workers 2 --timeout 120

# Test key endpoints
curl http://localhost:5000/health
curl "http://localhost:5000/api/v1/metadata/variables"
curl "http://localhost:5000/api/v1/data/timeseries?variable=tmp&region=C4000"
curl "http://localhost:5000/api/v1/forecast/scenarios?variable=tmp&region=C4000&target_year=2050"
```

There is no test suite. Manual verification is done via the API endpoints.

## Environment Variables

| Variable | Default | Notes |
|----------|---------|-------|
| `PORT` | 5000 | Used by run.py and Gunicorn |
| `FLASK_DEBUG` | False | Set to `true` for debug mode |
| `SECRET_KEY` | (hardcoded dev value) | Override in production |
| `R2_PUBLIC_URL` | `https://pub-e2d58bcf3d37484daaab4821c96b004a.r2.dev` | Cloudflare R2 public endpoint |
| `R2_BUCKET_NAME` | `himclimx` | R2 bucket name |

## Architecture

### Request Path

```
run.py
  └─ create_app()  [app/__init__.py]
       ├─ CORS (all origins, all methods)
       ├─ Blueprint: /api/v1/metadata  → app/api/metadata.py
       ├─ Blueprint: /api/v1/data      → app/api/data.py
       ├─ Blueprint: /api/v1/analysis  → app/api/analysis.py
       ├─ Blueprint: /api/v1/forecast  → app/api/forecast.py
       └─ Blueprint: /api/v1/impact    → app/api/impact.py
```

Each blueprint delegates immediately to a service singleton imported from `app/services/__init__.py`. Business logic lives only in services — API files handle parameter extraction, validation, and JSON serialization.

### Service Layer

| Service | File | Responsibility |
|---------|------|----------------|
| `data_service` | `services/data_service.py` | Zarr loading, spatial slicing, temporal filtering, aggregation |
| `analysis_service` | `services/analysis_service.py` | Trend (linregress + Mann-Kendall), anomalies (z-score), statistics |
| `forecast_service` | `services/forecast_service.py` | Prophet forecast; falls back to numpy polyfit if Prophet unavailable or <24 months of data |
| `impact_service` | `services/impact_service.py` | Rule-based risk scoring per variable+region combination |

### Data Access

All climate data is stored as Zarr arrays on Cloudflare R2. There is **no SQL database**.

- URL pattern: `{ZARR_BASE_PATH}/{variable}_himalayas.zarr`
- Accessed via `fsspec.get_mapper(url)` → `xr.open_zarr(mapper, consolidated=True)`
- `DataService._dataset_cache` (dict) caches loaded datasets in memory for the process lifetime — no re-fetching per request.
- Spatial dimensions: `lat`, `lon` (sliced by region bounds from `Config.REGIONS`)
- Temporal dimension: monthly from 1901-01 to 2024-12

### Configuration as Data (`app/config.py`)

`Config` is both the env-var config class and the authoritative registry for:
- **10 climate variables** (tmp, tmx, tmn, pre, cld, dtr, wet, vap, pet, frs) with metadata like `impact_factor`, `climate_sensitivity`, `normal_range`
- **9 regions** (E2000, E4000, E6000, C2000, C4000, C6000, W2000, W4000, W6000) with `bounds`, `vulnerability_index`, `climate_zone`
- **4 SSP scenarios** (ssp1–ssp5) with `multiplier` values used by `forecast_service` for scenario projections

When adding a new variable or region, update `Config` first — all services and endpoints derive their metadata from it.

### Forecast Fallback Logic

`forecast_service.prophet_forecast()` silently falls back to linear regression if:
1. Prophet is not installed
2. The timeseries has fewer than 24 data points

The response shape is identical in both cases, so the frontend cannot distinguish which method was used.

## Known Issues & Fixes

**CORS errors** — if cross-origin requests are blocked, `app/__init__.py` must have:
```python
CORS(app,
     resources={r"/*": {"origins": "*"}},
     methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
     supports_credentials=False)
```

**Scenarios endpoint 404** — the correct path is `/api/v1/forecast/scenarios`, not `/api/v1/scenarios`.

**Wrong year range in frontend** — `src/lib/store.ts` defaults `startYear: 1950, endYear: 2020`. Should be `1901` / `2024` to match the full dataset. Similarly `getYearRange()` in `utils.ts` defaults `datasetEnd` to 2020.

**DNS resolution errors reaching Railway** — flush DNS cache (`ipconfig /flushdns` on Windows).

## Deployment

Hosted on Railway. Deployment is automatic on push to `main`.

- Config: `railway.toml` (nixpacks builder, Gunicorn start command)
- Health check: `GET /health` (must return 200 within 100s)
- Production URL: `https://web-production-6719e.up.railway.app`

## Frontend

Local path: `E:\himalayan_climate_dashboard\himclimx_frontend\himclimx_frontend`  
Framework: Next.js 14 / TypeScript, deployed on Vercel at `himclimx.com`.  
Backend URL set via `NEXT_PUBLIC_API_URL` in Vercel environment variables.

The frontend's `src/lib/api.ts` is the HTTP client that calls these endpoints. **This file is currently missing from the frontend repo** (not present on disk despite being imported by `page.tsx`) and needs to be created.
