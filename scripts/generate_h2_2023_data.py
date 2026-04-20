from __future__ import annotations

from datetime import datetime, timedelta
import math
import random

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import SessionLocal
from app.models import City, Measurement, WeatherMeasurement


TARGET_CITIES = {
    "London": {"temp_base": 11.0, "temp_amp": 9.0, "pm25_base": 13.0, "pm25_amp": 6.0},
    "Beijing": {"temp_base": 13.0, "temp_amp": 14.0, "pm25_base": 30.0, "pm25_amp": 16.0},
    "Paris": {"temp_base": 12.0, "temp_amp": 10.0, "pm25_base": 15.0, "pm25_amp": 7.0},
    "New York": {"temp_base": 12.0, "temp_amp": 13.0, "pm25_base": 12.0, "pm25_amp": 8.0},
    "Delhi": {"temp_base": 25.0, "temp_amp": 7.0, "pm25_base": 52.0, "pm25_amp": 24.0},
}

START = datetime(2023, 7, 1, 0, 0, 0)
END = datetime(2023, 12, 31, 23, 0, 0)


def iter_hours(start: datetime, end: datetime):
    current = start
    while current <= end:
        yield current
        current += timedelta(hours=1)


def main() -> None:
    random.seed(20260420)
    db = SessionLocal()
    try:
        cities = db.query(City).filter(City.name.in_(list(TARGET_CITIES.keys()))).all()
        cities_by_name = {c.name: c for c in cities}
        missing = [name for name in TARGET_CITIES if name not in cities_by_name]
        if missing:
            raise SystemExit(f"Missing city rows: {missing}")

        pm_inserted = 0
        temp_inserted = 0

        for city_name, params in TARGET_CITIES.items():
            city = cities_by_name[city_name]

            existing_pm25_times = {
                row[0]
                for row in db.query(Measurement.datetime_utc)
                .filter(
                    Measurement.city_id == city.id,
                    Measurement.pollutant == "pm25",
                    Measurement.datetime_utc >= START,
                    Measurement.datetime_utc <= END,
                )
                .all()
            }
            existing_weather_times = {
                row[0]
                for row in db.query(WeatherMeasurement.datetime_utc)
                .filter(
                    WeatherMeasurement.city_id == city.id,
                    WeatherMeasurement.datetime_utc >= START,
                    WeatherMeasurement.datetime_utc <= END,
                )
                .all()
            }

            for ts in iter_hours(START, END):
                doy = ts.timetuple().tm_yday
                hour = ts.hour

                seasonal = math.sin((2 * math.pi * (doy - 172)) / 365.0)
                diurnal = math.sin((2 * math.pi * (hour - 14)) / 24.0)

                temperature = (
                    params["temp_base"]
                    + params["temp_amp"] * seasonal
                    + 2.0 * diurnal
                    + random.uniform(-0.8, 0.8)
                )

                pm25 = (
                    params["pm25_base"]
                    + params["pm25_amp"] * (0.6 - seasonal)
                    + 2.5 * (-diurnal)
                    + random.uniform(-3.0, 3.0)
                )
                pm25 = max(1.0, round(pm25, 2))
                temperature = round(temperature, 2)

                if ts not in existing_weather_times:
                    db.add(
                        WeatherMeasurement(
                            city_id=city.id,
                            datetime_utc=ts,
                            temperature_c=temperature,
                            relative_humidity=None,
                            precipitation_mm=None,
                            wind_speed_kmh=None,
                            source="synthetic-h2-2023",
                        )
                    )
                    temp_inserted += 1

                if ts not in existing_pm25_times:
                    db.add(
                        Measurement(
                            city_id=city.id,
                            datetime_utc=ts,
                            pollutant="pm25",
                            value=pm25,
                            unit="ug/m3",
                            source="synthetic-h2-2023",
                        )
                    )
                    pm_inserted += 1

        db.commit()
        print(f"Inserted weather rows: {temp_inserted}")
        print(f"Inserted pm25 rows: {pm_inserted}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
