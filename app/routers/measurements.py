from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import City, Measurement
from app.schemas import MeasurementCreate, MeasurementOut, MeasurementUpdate

router = APIRouter(
    prefix="/measurements",
    tags=["Air quality — measurements (pollutants)"],
)


@router.post("", response_model=MeasurementOut, status_code=status.HTTP_201_CREATED)
def create_measurement(payload: MeasurementCreate, db: Session = Depends(get_db)) -> Measurement:
    city = db.get(City, payload.city_id)
    if not city:
        raise HTTPException(status_code=404, detail="City not found.")

    measurement = Measurement(**payload.model_dump())
    db.add(measurement)
    db.commit()
    db.refresh(measurement)
    return measurement


@router.get("", response_model=list[MeasurementOut])
def list_measurements(
    city_id: int | None = None,
    pollutant: str | None = None,
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[Measurement]:
    stmt = select(Measurement)
    conditions = []
    if city_id is not None:
        conditions.append(Measurement.city_id == city_id)
    if pollutant:
        conditions.append(Measurement.pollutant == pollutant.lower())
    if start:
        conditions.append(Measurement.datetime_utc >= start)
    if end:
        conditions.append(Measurement.datetime_utc <= end)
    if conditions:
        stmt = stmt.where(and_(*conditions))
    stmt = stmt.order_by(Measurement.datetime_utc.desc()).offset(skip).limit(limit)
    return db.scalars(stmt).all()


@router.put("/{measurement_id}", response_model=MeasurementOut)
def update_measurement(
    measurement_id: int,
    payload: MeasurementUpdate,
    db: Session = Depends(get_db),
) -> Measurement:
    measurement = db.get(Measurement, measurement_id)
    if not measurement:
        raise HTTPException(status_code=404, detail="Measurement not found.")

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(measurement, key, value)

    db.commit()
    db.refresh(measurement)
    return measurement


@router.delete("/{measurement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_measurement(measurement_id: int, db: Session = Depends(get_db)) -> None:
    measurement = db.get(Measurement, measurement_id)
    if not measurement:
        raise HTTPException(status_code=404, detail="Measurement not found.")
    db.delete(measurement)
    db.commit()
