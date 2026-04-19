# API Documentation

**Project:** Global Air Quality Anomaly & City Comparison API  
**Version:** 0.1.0  
**Base URL (local):** `http://127.0.0.1:8000`  
**Machine-readable schema:** `GET /openapi.json` (OpenAPI 3)

This document describes all HTTP endpoints, parameters, JSON request/response shapes, authentication, and common error codes.

---

## 1. Authentication

This API does **not** implement API keys or JWT in the current version. All endpoints are **public** when the server is running locally.

- **Authentication:** None required.
- **Future work (optional):** API key header or OAuth2 could be added without changing core data models.

---

## 2. Common conventions

- **Content-Type:** `application/json` for request bodies where applicable.
- **Date/time:** ISO 8601 strings with timezone, e.g. `2023-07-21T10:00:00Z`.
- **Pollutant names:** Stored lowercased in the database (e.g. `pm25`, `pm10`, `no2`, `o3`).

---

## 3. HTTP status codes (summary)

| Code | Meaning | Typical cause |
|------|---------|-----------------|
| 200 | OK | Successful GET/PUT |
| 201 | Created | Successful POST |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid query (e.g. `end` before `start`) |
| 404 | Not Found | Missing resource or no data for analytics filters |
| 409 | Conflict | Unique constraint violation (duplicate city / duplicate weather row) |
| 422 | Unprocessable Entity | Validation error (FastAPI/Pydantic) |
| 500 | Internal Server Error | Unexpected server error |

**Error body (typical):**

```json
{
  "detail": "City not found."
}
```

Validation errors may return a structured `detail` array from FastAPI.

---

## 4. Endpoints

### 4.1 System

#### `GET /health`

Health check.

**Parameters:** None.

**Response 200:**

```json
{
  "status": "ok"
}
```

**Example (curl):**

```bash
curl -s http://127.0.0.1:8000/health
```

---

### 4.2 Cities (`/cities`)

#### `POST /cities`

Create a city.

**Request body (JSON):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | City name |
| country | string | Yes | Country name |
| latitude | number \| null | No | Latitude (WGS84) |
| longitude | number \| null | No | Longitude (WGS84) |

**Response 201:** `CityOut`

```json
{
  "name": "London",
  "country": "UK",
  "latitude": 51.5074,
  "longitude": -0.1278,
  "id": 1
}
```

**Errors:** `409` if duplicate `(name, country)`.

**Example:**

```bash
curl -s -X POST http://127.0.0.1:8000/cities \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"London\",\"country\":\"UK\",\"latitude\":51.5074,\"longitude\":-0.1278}"
```

---

#### `GET /cities`

List cities (paginated).

**Query parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| skip | int | 0 | Offset |
| limit | int | 100 | Page size (1–200) |

**Response 200:** `CityOut[]`

---

#### `GET /cities/{city_id}`

Get one city by ID.

**Path:** `city_id` (int)

**Response 200:** `CityOut`  
**Errors:** `404` if not found.

---

#### `PUT /cities/{city_id}`

Update a city (partial update supported via omitted fields).

**Request body:** any subset of `name`, `country`, `latitude`, `longitude`

**Response 200:** `CityOut`  
**Errors:** `404`, `409` (duplicate name/country).

---

#### `DELETE /cities/{city_id}`

Delete a city (cascades related measurements per ORM configuration).

**Response 204:** empty body  
**Errors:** `404`

---

### 4.3 Air quality measurements (`/measurements`)

#### `POST /measurements`

Create a measurement row.

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| city_id | int | Yes | Foreign key to `cities.id` |
| datetime_utc | string (ISO datetime) | Yes | Observation time (UTC) |
| pollutant | string | Yes | e.g. `pm25` |
| value | number | Yes | Measured value |
| unit | string | Yes | e.g. `ug/m3` |
| source | string \| null | No | Provenance, e.g. `openaq` |

**Response 201:** `MeasurementOut` (includes `id`)

**Errors:** `404` if `city_id` does not exist.

**Example:**

```bash
curl -s -X POST http://127.0.0.1:8000/measurements \
  -H "Content-Type: application/json" \
  -d "{\"city_id\":1,\"datetime_utc\":\"2026-04-01T10:00:00Z\",\"pollutant\":\"pm25\",\"value\":12.3,\"unit\":\"ug/m3\",\"source\":\"manual\"}"
```

---

#### `GET /measurements`

List measurements with optional filters.

**Query parameters:**

| Name | Type | Description |
|------|------|-------------|
| city_id | int \| omitted | Filter by city |
| pollutant | string \| omitted | Filter (lowercased internally) |
| start | datetime \| omitted | Inclusive lower bound |
| end | datetime \| omitted | Inclusive upper bound |
| skip | int | Pagination offset |
| limit | int | Page size (1–500) |

**Response 200:** `MeasurementOut[]` (newest first)

---

#### `PUT /measurements/{measurement_id}`

Update a measurement.

**Request body:** optional fields among `datetime_utc`, `pollutant`, `value`, `unit`, `source`

**Response 200:** `MeasurementOut`  
**Errors:** `404`

---

#### `DELETE /measurements/{measurement_id}`

Delete a measurement.

**Response 204**  
**Errors:** `404`

---

### 4.4 Weather measurements (`/weather-measurements`)

Hourly weather rows (e.g. imported from Open-Meteo). Unique per `(city_id, datetime_utc)`.

#### `POST /weather-measurements`

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| city_id | int | Yes | Foreign key |
| datetime_utc | string (ISO datetime) | Yes | Hour timestamp (UTC) |
| temperature_c | number \| null | No | °C |
| relative_humidity | number \| null | No | % |
| precipitation_mm | number \| null | No | mm |
| wind_speed_kmh | number \| null | No | km/h |
| source | string \| null | No | e.g. `open-meteo` |

**Response 201:** `WeatherMeasurementOut` (includes `id`)

**Errors:** `404` (city missing), `409` (duplicate time for same city)

---

#### `GET /weather-measurements`

**Query:** `city_id`, `start`, `end`, `skip`, `limit` (same pattern as measurements; `limit` up to 2000)

**Response 200:** `WeatherMeasurementOut[]`

---

#### `GET /weather-measurements/{weather_id}`

**Response 200** or **404**

---

#### `PUT /weather-measurements/{weather_id}`

**Response 200** or **404**

---

#### `DELETE /weather-measurements/{weather_id}`

**Response 204** or **404**

---

### 4.5 Analytics (`/analytics`)

Analytics apply basic **data cleaning** on air-quality values:

- Drop extreme placeholders: `value <= -1000` or `value >= 100000`
- For `pm25` and `pm10`, also require `value >= 0`

#### `GET /analytics/city-comparison`

Compare aggregate statistics for multiple cities and one pollutant over a time window.

**Query parameters:**

| Name | Type | Description |
|------|------|-------------|
| city_ids | int[] (repeatable) | At least 2 IDs |
| pollutant | string | e.g. `pm25` |
| start | datetime | Window start |
| end | datetime | Window end |

**Response 200:**

```json
{
  "pollutant": "pm25",
  "start": "2023-01-01T00:00:00Z",
  "end": "2023-06-30T23:59:59Z",
  "cities": [
    {
      "city_id": 1,
      "mean": 10.1234,
      "median": 9.5,
      "p95": 18.0,
      "min": 2.0,
      "max": 25.0,
      "sample_count": 1200
    }
  ]
}
```

**Errors:** `400` if `end < start`; `404` if no data for filters.

---

#### `GET /analytics/anomalies`

Z-score anomaly detection for one city and pollutant.

**Query parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| city_id | int | required | City |
| pollutant | string | required | e.g. `pm25` |
| start | datetime | required | Window start |
| end | datetime | required | Window end |
| threshold | float | 2.5 | \|z-score\| threshold |

**Response 200:**

```json
{
  "city_id": 1,
  "pollutant": "pm25",
  "start": "2023-01-01T00:00:00Z",
  "end": "2023-06-30T23:59:59Z",
  "threshold": 2.5,
  "total_points": 500,
  "anomaly_count": 12,
  "anomalies": [
    {
      "measurement_id": 111,
      "city_id": 1,
      "datetime_utc": "2023-07-26T13:00:00",
      "value": 45.0,
      "z_score": 3.12
    }
  ]
}
```

**Errors:** `400` (`end < start`); `404` if fewer than 2 usable points.

---

#### `GET /analytics/daily-trend`

Daily aggregated trend (mean per calendar day).

**Query parameters:**

| Name | Type | Description |
|------|------|-------------|
| city_id | int | City |
| metric | string | `pm25`, `pm10`, `no2`, `o3`, or `temperature_c` |
| start | datetime | Window start |
| end | datetime | Window end |

For `temperature_c`, data comes from `weather_measurements.temperature_c`. Other metrics use `measurements` filtered by `pollutant`.

**Response 200:**

```json
{
  "city_id": 1,
  "metric": "pm25",
  "start": "2023-01-01T00:00:00Z",
  "end": "2023-06-30T23:59:59Z",
  "points": [
    { "day": "2023-01-01", "avg": 12.4, "n": 24 }
  ]
}
```

**Errors:** `400`, `404`

---
