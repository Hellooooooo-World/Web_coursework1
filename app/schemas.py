from datetime import datetime

from pydantic import BaseModel, Field


class CityBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    country: str = Field(min_length=1, max_length=100)
    latitude: float | None = None
    longitude: float | None = None


class CityCreate(CityBase):
    pass


class CityUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    country: str | None = Field(default=None, min_length=1, max_length=100)
    latitude: float | None = None
    longitude: float | None = None


class CityOut(CityBase):
    id: int

    class Config:
        from_attributes = True


class MeasurementBase(BaseModel):
    city_id: int
    datetime_utc: datetime
    pollutant: str = Field(min_length=1, max_length=20)
    value: float
    unit: str = Field(min_length=1, max_length=20)
    source: str | None = None


class MeasurementCreate(MeasurementBase):
    pass


class MeasurementUpdate(BaseModel):
    datetime_utc: datetime | None = None
    pollutant: str | None = Field(default=None, min_length=1, max_length=20)
    value: float | None = None
    unit: str | None = Field(default=None, min_length=1, max_length=20)
    source: str | None = None


class MeasurementOut(MeasurementBase):
    id: int

    class Config:
        from_attributes = True


class WeatherMeasurementBase(BaseModel):
    city_id: int
    datetime_utc: datetime
    temperature_c: float | None = None
    relative_humidity: float | None = None
    precipitation_mm: float | None = None
    wind_speed_kmh: float | None = None
    source: str | None = None


class WeatherMeasurementCreate(WeatherMeasurementBase):
    pass


class WeatherMeasurementUpdate(BaseModel):
    datetime_utc: datetime | None = None
    temperature_c: float | None = None
    relative_humidity: float | None = None
    precipitation_mm: float | None = None
    wind_speed_kmh: float | None = None
    source: str | None = None


class WeatherMeasurementOut(WeatherMeasurementBase):
    id: int

    class Config:
        from_attributes = True


class CityComparisonStats(BaseModel):
    city_id: int
    mean: float
    median: float
    p95: float
    min: float
    max: float
    sample_count: int


class CityComparisonResponse(BaseModel):
    pollutant: str
    start: datetime
    end: datetime
    cities: list[CityComparisonStats]


class AnomalyItem(BaseModel):
    measurement_id: int
    city_id: int
    datetime_utc: datetime
    value: float
    z_score: float


class AnomalyResponse(BaseModel):
    city_id: int
    pollutant: str
    start: datetime
    end: datetime
    threshold: float
    total_points: int
    anomaly_count: int
    anomalies: list[AnomalyItem]


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)


class UserOut(BaseModel):
    id: int
    username: str
    created_at: datetime

    class Config:
        from_attributes = True
