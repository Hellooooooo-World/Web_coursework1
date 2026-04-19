from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import City
from app.schemas import CityCreate, CityOut, CityUpdate

router = APIRouter(prefix="/cities", tags=["cities"])


@router.post("", response_model=CityOut, status_code=status.HTTP_201_CREATED)
def create_city(payload: CityCreate, db: Session = Depends(get_db)) -> City:
    city = City(**payload.model_dump())
    db.add(city)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="City already exists.") from exc
    db.refresh(city)
    return city


@router.get("", response_model=list[CityOut])
def list_cities(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[City]:
    return db.scalars(select(City).offset(skip).limit(limit)).all()


@router.get("/{city_id}", response_model=CityOut)
def get_city(city_id: int, db: Session = Depends(get_db)) -> City:
    city = db.get(City, city_id)
    if not city:
        raise HTTPException(status_code=404, detail="City not found.")
    return city


@router.put("/{city_id}", response_model=CityOut)
def update_city(city_id: int, payload: CityUpdate, db: Session = Depends(get_db)) -> City:
    city = db.get(City, city_id)
    if not city:
        raise HTTPException(status_code=404, detail="City not found.")

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(city, key, value)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="City already exists.") from exc
    db.refresh(city)
    return city


@router.delete("/{city_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_city(city_id: int, db: Session = Depends(get_db)) -> None:
    city = db.get(City, city_id)
    if not city:
        raise HTTPException(status_code=404, detail="City not found.")
    db.delete(city)
    db.commit()
