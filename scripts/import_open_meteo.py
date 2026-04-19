import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import SessionLocal
from app.models import City, WeatherMeasurement

load_dotenv()

OPEN_METEO_ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import historical hourly weather data via Open-Meteo."
    )
    parser.add_argument("--city-id", type=int, required=True)
    parser.add_argument("--start-date", type=str, required=True, help="YYYY-MM-DD")
    parser.add_argument("--end-date", type=str, required=True, help="YYYY-MM-DD")
    parser.add_argument(
        "--variables",
        type=str,
        default="temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
        help="Comma-separated Open-Meteo hourly variables.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    db = SessionLocal()
    try:
        city = db.get(City, args.city_id)
        if not city:
            raise SystemExit("City not found. Create it first via /cities.")
        if city.latitude is None or city.longitude is None:
            raise SystemExit("City missing latitude/longitude. Update city first.")

        params = {
            "latitude": city.latitude,
            "longitude": city.longitude,
            "start_date": args.start_date,
            "end_date": args.end_date,
            "hourly": args.variables,
            "timezone": "UTC",
        }

        response = None
        for attempt in range(1, 4):
            try:
                response = httpx.get(OPEN_METEO_ARCHIVE, params=params, timeout=60.0)
                response.raise_for_status()
                break
            except httpx.HTTPError:
                if attempt >= 3:
                    raise
                time.sleep(1.0 * attempt)

        if response is None:
            print("No response from Open-Meteo.")
            return

        payload = response.json()
        hourly = payload.get("hourly") or {}
        times = hourly.get("time") or []
        if not times:
            print("No hourly results returned.")
            return

        temps = hourly.get("temperature_2m") or []
        humidities = hourly.get("relative_humidity_2m") or []
        precipitations = hourly.get("precipitation") or []
        wind_speeds = hourly.get("wind_speed_10m") or []

        inserted = 0
        for idx, raw_time in enumerate(times):
            measured_at = datetime.fromisoformat(raw_time).replace(tzinfo=timezone.utc)

            exists = (
                db.query(WeatherMeasurement)
                .filter(
                    WeatherMeasurement.city_id == city.id,
                    WeatherMeasurement.datetime_utc == measured_at,
                )
                .first()
            )
            if exists:
                continue

            weather_measurement = WeatherMeasurement(
                city_id=city.id,
                datetime_utc=measured_at,
                temperature_c=float(temps[idx]) if idx < len(temps) and temps[idx] is not None else None,
                relative_humidity=float(humidities[idx])
                if idx < len(humidities) and humidities[idx] is not None
                else None,
                precipitation_mm=float(precipitations[idx])
                if idx < len(precipitations) and precipitations[idx] is not None
                else None,
                wind_speed_kmh=float(wind_speeds[idx])
                if idx < len(wind_speeds) and wind_speeds[idx] is not None
                else None,
                source="open-meteo",
            )
            db.add(weather_measurement)
            inserted += 1

        db.commit()
        print(f"Imported {inserted} hourly weather rows for city_id={city.id}.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
