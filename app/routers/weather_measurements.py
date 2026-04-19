from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import City, WeatherMeasurement
from app.schemas import (
    WeatherMeasurementCreate,
    WeatherMeasurementOut,
    WeatherMeasurementUpdate,
)

router = APIRouter(
    prefix="/weather-measurements",
    tags=["Weather — hourly (temperature, humidity, …)"],
)


@router.post("", response_model=WeatherMeasurementOut, status_code=status.HTTP_201_CREATED)
def create_weather_measurement(
    payload: WeatherMeasurementCreate, db: Session = Depends(get_db)
) -> WeatherMeasurement:
    city = db.get(City, payload.city_id)
    if not city:
        raise HTTPException(status_code=404, detail="City not found.")

    weather_measurement = WeatherMeasurement(**payload.model_dump())
    db.add(weather_measurement)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Weather measurement already exists.") from exc
    db.refresh(weather_measurement)
    return weather_measurement


@router.get("", response_model=list[WeatherMeasurementOut])
def list_weather_measurements(
    city_id: int | None = None,
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=200, ge=1, le=2000),
    db: Session = Depends(get_db),
) -> list[WeatherMeasurement]:
    stmt = select(WeatherMeasurement)
    conditions = []
    if city_id is not None:
        conditions.append(WeatherMeasurement.city_id == city_id)
    if start:
        conditions.append(WeatherMeasurement.datetime_utc >= start)
    if end:
        conditions.append(WeatherMeasurement.datetime_utc <= end)
    if conditions:
        stmt = stmt.where(and_(*conditions))
    stmt = stmt.order_by(WeatherMeasurement.datetime_utc.desc()).offset(skip).limit(limit)
    return db.scalars(stmt).all()


@router.get("/{weather_id}", response_model=WeatherMeasurementOut)
def get_weather_measurement(weather_id: int, db: Session = Depends(get_db)) -> WeatherMeasurement:
    weather_measurement = db.get(WeatherMeasurement, weather_id)
    if not weather_measurement:
        raise HTTPException(status_code=404, detail="Weather measurement not found.")
    return weather_measurement


@router.put("/{weather_id}", response_model=WeatherMeasurementOut)
def update_weather_measurement(
    weather_id: int,
    payload: WeatherMeasurementUpdate,
    db: Session = Depends(get_db),
) -> WeatherMeasurement:
    weather_measurement = db.get(WeatherMeasurement, weather_id)
    if not weather_measurement:
        raise HTTPException(status_code=404, detail="Weather measurement not found.")

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(weather_measurement, key, value)

    db.commit()
    db.refresh(weather_measurement)
    return weather_measurement


@router.delete("/{weather_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_weather_measurement(weather_id: int, db: Session = Depends(get_db)) -> None:
    weather_measurement = db.get(WeatherMeasurement, weather_id)
    if not weather_measurement:
        raise HTTPException(status_code=404, detail="Weather measurement not found.")
    db.delete(weather_measurement)
    db.commit()
