from datetime import datetime
from statistics import mean, median

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Measurement, WeatherMeasurement
from app.schemas import (
    AnomalyItem,
    AnomalyResponse,
    CityComparisonResponse,
    CityComparisonStats,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])

INVALID_VALUE_MIN = -1000.0
INVALID_VALUE_MAX = 100000.0
NON_NEGATIVE_POLLUTANTS = {"pm25", "pm10"}


def percentile_95(values: list[float]) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = int(0.95 * (len(sorted_values) - 1))
    return float(sorted_values[index])


@router.get("/city-comparison", response_model=CityComparisonResponse)
def city_comparison(
    city_ids: list[int] = Query(..., min_length=2),
    pollutant: str = Query(...),
    start: datetime = Query(...),
    end: datetime = Query(...),
    db: Session = Depends(get_db),
) -> CityComparisonResponse:
    if end < start:
        raise HTTPException(status_code=400, detail="end must be after start.")

    result: list[CityComparisonStats] = []
    pollutant_l = pollutant.lower()
    extra_conditions = []
    if pollutant_l in NON_NEGATIVE_POLLUTANTS:
        extra_conditions.append(Measurement.value >= 0)
    for city_id in city_ids:
        stmt = select(Measurement.value).where(
            and_(
                Measurement.city_id == city_id,
                Measurement.pollutant == pollutant_l,
                Measurement.datetime_utc >= start,
                Measurement.datetime_utc <= end,
                Measurement.value > INVALID_VALUE_MIN,
                Measurement.value < INVALID_VALUE_MAX,
                *extra_conditions,
            )
        )
        values = [float(v) for v in db.scalars(stmt).all()]
        if not values:
            continue

        result.append(
            CityComparisonStats(
                city_id=city_id,
                mean=round(mean(values), 4),
                median=round(median(values), 4),
                p95=round(percentile_95(values), 4),
                min=round(min(values), 4),
                max=round(max(values), 4),
                sample_count=len(values),
            )
        )

    if not result:
        raise HTTPException(status_code=404, detail="No data found for given filters.")

    return CityComparisonResponse(
        pollutant=pollutant.lower(),
        start=start,
        end=end,
        cities=result,
    )


@router.get("/anomalies", response_model=AnomalyResponse)
def detect_anomalies(
    city_id: int = Query(...),
    pollutant: str = Query(...),
    start: datetime = Query(...),
    end: datetime = Query(...),
    threshold: float = Query(default=2.5, gt=0),
    db: Session = Depends(get_db),
) -> AnomalyResponse:
    if end < start:
        raise HTTPException(status_code=400, detail="end must be after start.")

    pollutant_l = pollutant.lower()
    extra_conditions = []
    if pollutant_l in NON_NEGATIVE_POLLUTANTS:
        extra_conditions.append(Measurement.value >= 0)

    stmt = select(Measurement).where(
        and_(
            Measurement.city_id == city_id,
            Measurement.pollutant == pollutant_l,
            Measurement.datetime_utc >= start,
            Measurement.datetime_utc <= end,
            Measurement.value > INVALID_VALUE_MIN,
            Measurement.value < INVALID_VALUE_MAX,
            *extra_conditions,
        )
    )
    rows = db.scalars(stmt).all()
    if len(rows) < 2:
        raise HTTPException(status_code=404, detail="Not enough data points for anomaly detection.")

    values = [float(m.value) for m in rows]
    avg = mean(values)
    variance = sum((x - avg) ** 2 for x in values) / (len(values) - 1)
    std = variance ** 0.5

    if std == 0:
        return AnomalyResponse(
            city_id=city_id,
            pollutant=pollutant.lower(),
            start=start,
            end=end,
            threshold=threshold,
            total_points=len(rows),
            anomaly_count=0,
            anomalies=[],
        )

    anomalies: list[AnomalyItem] = []
    for m in rows:
        z_score = (float(m.value) - avg) / std
        if abs(z_score) >= threshold:
            anomalies.append(
                AnomalyItem(
                    measurement_id=m.id,
                    city_id=m.city_id,
                    datetime_utc=m.datetime_utc,
                    value=float(m.value),
                    z_score=round(z_score, 4),
                )
            )

    return AnomalyResponse(
        city_id=city_id,
        pollutant=pollutant.lower(),
        start=start,
        end=end,
        threshold=threshold,
        total_points=len(rows),
        anomaly_count=len(anomalies),
        anomalies=anomalies,
    )


@router.get("/daily-trend", tags=["analytics"])
def daily_trend(
    city_id: int = Query(...),
    metric: str = Query(..., description="pm25|pm10|no2|o3|temperature_c"),
    start: datetime = Query(...),
    end: datetime = Query(...),
    db: Session = Depends(get_db),
) -> dict:
    """Daily average trend for pollutant values or temperature."""
    if end < start:
        raise HTTPException(status_code=400, detail="end must be after start.")

    metric_l = metric.lower()

    if metric_l == "temperature_c":
        day_col = func.date(WeatherMeasurement.datetime_utc).label("day")
        avg_col = func.avg(WeatherMeasurement.temperature_c).label("avg")
        stmt = (
            select(day_col, avg_col, func.count().label("n"))
            .where(
                and_(
                    WeatherMeasurement.city_id == city_id,
                    WeatherMeasurement.datetime_utc >= start,
                    WeatherMeasurement.datetime_utc <= end,
                    WeatherMeasurement.temperature_c.is_not(None),
                )
            )
            .group_by(day_col)
            .order_by(day_col)
        )
    else:
        extra_conditions = []
        if metric_l in NON_NEGATIVE_POLLUTANTS:
            extra_conditions.append(Measurement.value >= 0)

        day_col = func.date(Measurement.datetime_utc).label("day")
        avg_col = func.avg(Measurement.value).label("avg")
        stmt = (
            select(day_col, avg_col, func.count().label("n"))
            .where(
                and_(
                    Measurement.city_id == city_id,
                    Measurement.pollutant == metric_l,
                    Measurement.datetime_utc >= start,
                    Measurement.datetime_utc <= end,
                    Measurement.value > INVALID_VALUE_MIN,
                    Measurement.value < INVALID_VALUE_MAX,
                    *extra_conditions,
                )
            )
            .group_by(day_col)
            .order_by(day_col)
        )

    rows = db.execute(stmt).all()
    if not rows:
        raise HTTPException(status_code=404, detail="No data found for given filters.")

    return {
        "city_id": city_id,
        "metric": metric_l,
        "start": start,
        "end": end,
        "points": [
            {"day": str(day), "avg": float(avg) if avg is not None else None, "n": int(n)}
            for day, avg, n in rows
        ],
    }
