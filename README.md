# Global Air Quality Anomaly & City Comparison API

This project is a coursework-ready API built with FastAPI and SQLAlchemy.
It supports:

- City CRUD operations
- Measurement CRUD operations
- City comparison analytics
- Air-quality anomaly detection (z-score based)

## 1. Setup

### Requirements

- Python 3.11+
- PostgreSQL (recommended for final submission)

### Install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Configure

```bash
copy .env.example .env
```

Set `DATABASE_URL` in `.env` to your PostgreSQL DSN.
If `.env` is missing, the app uses local SQLite (`air_quality.db`) for quick start.

## 2. Run

```bash
uvicorn app.main:app --reload
```

Open docs:

- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>

### API documentation (coursework PDF)

Human-readable API reference (endpoints, parameters, JSON examples, status codes):

- [docs/api-documentation.md](docs/api-documentation.md)

For Minerva submission, export that document to **PDF** (e.g. save as `docs/api-documentation.pdf` in this repo, or print from your editor / browser). The coursework asks for a **PDF**; keep the Markdown as the editable source.

## 3. API Endpoints

### System

- `GET /health`

### Cities

- `POST /cities`
- `GET /cities`
- `GET /cities/{city_id}`
- `PUT /cities/{city_id}`
- `DELETE /cities/{city_id}`

### Air quality — measurements (pollutants, e.g. PM2.5)

- `POST /measurements`
- `GET /measurements` (supports `city_id`, `pollutant`, `start`, `end`)
- `PUT /measurements/{measurement_id}`
- `DELETE /measurements/{measurement_id}`

### Weather — hourly (temperature, humidity, …)

- `POST /weather-measurements`
- `GET /weather-measurements`
- `GET /weather-measurements/{weather_id}`
- `PUT /weather-measurements/{weather_id}`
- `DELETE /weather-measurements/{weather_id}`

### Analytics

- `GET /analytics/city-comparison` (`city_ids`, `pollutant`, `start`, `end`)
- `GET /analytics/anomalies` (`city_id`, `pollutant`, `start`, `end`, `threshold`)
- `GET /analytics/daily-trend` (`city_id`, `metric`, `start`, `end`) — `metric` e.g. `pm25` or `temperature_c`

## 4. Import OpenAQ Data

Use a sensor ID from OpenAQ and import records:

```bash
python scripts/import_openaq.py --sensor-id 1234 --city London --country UK --pollutant pm25 --limit 200
```

OpenAQ docs: <https://docs.openaq.org/>

### 4.1 (Optional) Find sensor_id for a London monitoring station

OpenAQ provides sensors under a `locations_id` (from the Explorer URL).

```bash
python scripts/list_openaq_sensors.py --locations-id 225715 --parameter pm2.5
```

Pick the `sensor_id` that corresponds to `pm2.5`, then use it with `import_openaq.py`.

## 4.2 Import historical weather (temperature) data

This project also supports historical hourly weather via Open-Meteo (no API key required).
Make sure your city has latitude/longitude stored (create/update via `/cities`).

Example (London city_id=1):

```bash
python scripts/import_open_meteo.py --city-id 1 --start-date 2023-07-21 --end-date 2023-08-17
```

## 4.3 Trend endpoint examples

- Daily trend for PM2.5:
  - `GET /analytics/daily-trend?city_id=1&metric=pm25&start=2023-07-21T00:00:00Z&end=2023-08-17T23:59:59Z`
- Daily trend for temperature:
  - `GET /analytics/daily-trend?city_id=1&metric=temperature_c&start=2023-07-21T00:00:00Z&end=2023-08-17T23:59:59Z`

## 5. Coursework Alignment Checklist

- [x] Database-backed CRUD API
- [x] At least four HTTP endpoints
- [x] JSON responses and proper error codes
- [x] Analytics endpoints beyond minimum requirements
- [ ] External deployment
- [ ] Technical report (max 5 pages)
- [ ] API documentation PDF export
- [ ] Presentation slides with deliverables mapping

## 6. Suggested Next Steps

1. Add authentication (API key or JWT).
2. Add tests with pytest.
3. Deploy to a public host (Render/Railway/PythonAnywhere).
4. Export Swagger/OpenAPI docs to PDF for submission.
