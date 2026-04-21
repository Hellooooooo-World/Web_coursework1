# Global Air Quality Anomaly & City Comparison API

Coursework project API built with FastAPI + SQLAlchemy for air-quality and weather analysis across major cities.

## Core capabilities

- City-to-city comparison for pollutant levels
- Anomaly detection using z-score
- Daily trend analytics for pollutant and temperature metrics
- Session-based authentication with sign-in/sign-up pages

## Technology stack

- Python 3.11+
- FastAPI
- SQLAlchemy
- SQLite (default local database: `air_quality.db`)
- Optional PostgreSQL via `DATABASE_URL`

---

## 1) Setup

### 1.1 Install dependencies

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 1.2 Environment configuration

Create `.env` (or set platform environment variables) with at least:

- `DATABASE_URL` (optional; defaults to local SQLite)
- `SESSION_SECRET` (recommended for production deployments)
- `SESSION_MAX_AGE_SECONDS` (optional session expiry in seconds)
- `BASIC_AUTH_USERNAME` / `BASIC_AUTH_PASSWORD` (initial admin account seed on startup; defaults to `admin/admin`)

If `SESSION_SECRET` is not set, the app generates one at startup, so all users must re-login after every restart.

### 1.3 Run the API

```bash
uvicorn app.main:app --reload
```

Main URLs:

- App root: <http://127.0.0.1:8000/>
- Swagger docs: <http://127.0.0.1:8000/docs>
- Login page: <http://127.0.0.1:8000/login>
- Sign-up page: <http://127.0.0.1:8000/signup>

---

## 2) Authentication behavior

- Unauthenticated requests to protected routes (including `/`, `/docs`, `/openapi.json`, and data endpoints) are redirected to `/login` or rejected with 401.
- Users authenticate via form-based session login (`/login`).
- New users can be created through `/signup`.
- Logout endpoint: `POST /logout`.
- A hidden programmatic endpoint exists for creating users: `POST /users` (not shown in Swagger UI).

---

## 3) API endpoints

### 3.1 Cities

- `POST /cities`
- `GET /cities`
- `GET /cities/{city_id}`
- `PUT /cities/{city_id}`
- `DELETE /cities/{city_id}`

### 3.2 Air quality measurements

- `POST /measurements`
- `GET /measurements` (filters: `city_id`, `pollutant`, `start`, `end`, paging)
- `PUT /measurements/{measurement_id}`
- `DELETE /measurements/{measurement_id}`

### 3.3 Weather measurements

- `POST /weather-measurements`
- `GET /weather-measurements` (filters: `city_id`, `start`, `end`, paging)
- `GET /weather-measurements/{weather_id}`
- `PUT /weather-measurements/{weather_id}`
- `DELETE /weather-measurements/{weather_id}`

### 3.4 Analytics

- `GET /analytics/city-comparison` (`city_ids`, `pollutant`, `start`, `end`)
- `GET /analytics/anomalies` (`city_id`, `pollutant`, `start`, `end`, `threshold`)
- `GET /analytics/daily-trend` (`city_id`, `metric`, `start`, `end`)
  - `metric` examples: `pm25`, `pm10`, `no2`, `o3`, `temperature_c`

---

## 4) Data import and generation scripts

### 4.1 Import PM2.5 from OpenAQ

```bash
python scripts/import_openaq.py --sensor-id 1234 --city London --country UK --pollutant pm25 --limit 200
```

OpenAQ documentation: <https://docs.openaq.org/>

### 4.2 Import weather data from Open-Meteo

```bash
python scripts/import_open_meteo.py --city-id 1 --start-date 2023-07-01 --end-date 2023-12-31
```

### 4.3 Generate missing H2 2023 dataset (project-specific)

To supplement data for five cities (London, Beijing, Paris, New York, Delhi) in the second half of 2023:

```bash
python scripts/generate_h2_2023_data.py
```

This script fills missing hourly records for:

- `pm25` in `measurements`
- `temperature_c` in `weather_measurements`
- Date range: `2023-07-01 00:00:00` to `2023-12-31 23:00:00`

---

## 5) Quick verification

### 5.1 Verify login protection

- Open `http://127.0.0.1:8000/` in a private/incognito browser window.
- Expect redirect to `/login` if not authenticated.

### 5.2 Verify full-year data coverage for target cities

Run:

```bash
python -c "import sqlite3; con=sqlite3.connect('air_quality.db'); cur=con.cursor(); print('PM25 max by city:'); [print(r) for r in cur.execute(\"\"\"select c.name,max(m.datetime_utc) from measurements m join cities c on c.id=m.city_id where c.id in (1,2,3,4,5) and lower(m.pollutant)='pm25' group by c.id,c.name order by c.id\"\"\")]; print('Temp max by city:'); [print(r) for r in cur.execute(\"\"\"select c.name,max(w.datetime_utc) from weather_measurements w join cities c on c.id=w.city_id where c.id in (1,2,3,4,5) and w.temperature_c is not null group by c.id,c.name order by c.id\"\"\")]; con.close()"
```

Expected max timestamp for all five cities: `2023-12-31 23:00:00...`

---

## 6) Deliverables

- Code repository (this project)
- API documentation source: [`docs/api-documentation.md`](docs/api-documentation.md)
- Technical report (editable + final PDF):
  - [`docs/XJCO3011_Technical_Report.docx`](docs/XJCO3011_Technical_Report.docx)
  - [`docs/XJCO3011_Technical_Report.pdf`](docs/XJCO3011_Technical_Report.pdf)
