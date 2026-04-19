import argparse
from datetime import datetime
import time

import httpx
from dotenv import load_dotenv
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import SessionLocal
from app.models import City, Measurement

OPENAQ_API = "https://api.openaq.org/v3/sensors/{sensor_id}/measurements"

load_dotenv()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import OpenAQ measurements by sensor ID.")
    parser.add_argument("--sensor-id", type=int, required=True)
    parser.add_argument("--city", type=str, required=True)
    parser.add_argument("--country", type=str, required=True)
    parser.add_argument("--pollutant", type=str, required=True)
    parser.add_argument("--unit", type=str, default="ug/m3")
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument(
        "--max-pages",
        type=int,
        default=1,
        help="How many pages to fetch from OpenAQ (page starts at 1).",
    )
    parser.add_argument(
        "--datetime-from",
        type=str,
        default=None,
        help="ISO datetime string, e.g. 2025-01-01T00:00:00Z",
    )
    parser.add_argument(
        "--datetime-to",
        type=str,
        default=None,
        help="ISO datetime string, e.g. 2025-02-01T00:00:00Z",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    import os

    api_key = os.environ.get("OPENAQ_API_KEY")
    normalized_pollutant = args.pollutant.lower()

    headers = {}
    if api_key:
        headers["X-API-Key"] = api_key

    base_params: dict[str, str | int] = {"limit": args.limit}
    if args.datetime_from:
        base_params["datetime_from"] = args.datetime_from
    if args.datetime_to:
        base_params["datetime_to"] = args.datetime_to

    db = SessionLocal()
    try:
        city = (
            db.query(City)
            .filter(City.name == args.city, City.country == args.country)
            .first()
        )
        if city is None:
            city = City(name=args.city, country=args.country)
            db.add(city)
            db.commit()
            db.refresh(city)

        inserted_total = 0
        fetched_total = 0

        with httpx.Client(timeout=30.0) as client_http:
            for page in range(1, max(1, args.max_pages) + 1):
                params = dict(base_params)
                params["page"] = page

                response = None
                for attempt in range(1, 4):
                    try:
                        response = client_http.get(
                            OPENAQ_API.format(sensor_id=args.sensor_id),
                            params=params,
                            headers=headers,
                        )
                        response.raise_for_status()
                        break
                    except httpx.HTTPError:
                        if attempt >= 3:
                            raise
                        time.sleep(1.0 * attempt)

                if response is None:
                    break
                payload = response.json()
                rows = payload.get("results", []) or []
                if not rows:
                    break

                fetched_total += len(rows)
                inserted = 0

                for row in rows:
                    # OpenAQ v3 may return timestamps under `period.datetimeFrom.utc`
                    # rather than top-level `datetimeFrom`.
                    datetime_from = (
                        row.get("period", {}).get("datetimeFrom", {}).get("utc")
                        or row.get("datetimeFrom", {}).get("utc")
                    )
                    if not datetime_from:
                        continue

                    value = row.get("value")
                    if value is None:
                        continue

                    # OpenAQ returns a parameter block describing units; fall back to CLI unit.
                    parameter = row.get("parameter") or {}
                    units = parameter.get("units") or args.unit

                    measurement_dt = datetime.fromisoformat(datetime_from.replace("Z", "+00:00"))

                    # Simple dedupe: (city_id, datetime_utc, pollutant) to avoid repeated imports.
                    exists = (
                        db.query(Measurement)
                        .filter(
                            Measurement.city_id == city.id,
                            Measurement.datetime_utc == measurement_dt,
                            Measurement.pollutant == normalized_pollutant,
                        )
                        .first()
                    )
                    if exists:
                        continue

                    measurement = Measurement(
                        city_id=city.id,
                        datetime_utc=measurement_dt,
                        pollutant=normalized_pollutant,
                        value=float(value),
                        unit=str(units),
                        source="openaq",
                    )
                    db.add(measurement)
                    inserted += 1

                db.commit()
                inserted_total += inserted

        if fetched_total == 0:
            print("No measurement rows returned.")
            return

        print(
            f"Fetched {fetched_total} rows, imported {inserted_total} new rows "
            f"for city={city.name}, sensor={args.sensor_id}."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
