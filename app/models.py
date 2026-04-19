from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class City(Base):
    __tablename__ = "cities"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    country: Mapped[str] = mapped_column(String(100), index=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    measurements: Mapped[list["Measurement"]] = relationship(
        back_populates="city", cascade="all, delete-orphan"
    )
    weather_measurements: Mapped[list["WeatherMeasurement"]] = relationship(
        back_populates="city", cascade="all, delete-orphan"
    )
    anomalies: Mapped[list["Anomaly"]] = relationship(
        back_populates="city", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("name", "country", name="uq_city_country"),)


class Measurement(Base):
    __tablename__ = "measurements"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"), index=True)
    datetime_utc: Mapped[datetime] = mapped_column(DateTime, index=True)
    pollutant: Mapped[str] = mapped_column(String(20), index=True)
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(20))
    source: Mapped[str | None] = mapped_column(String(120), nullable=True)

    city: Mapped["City"] = relationship(back_populates="measurements")


class WeatherMeasurement(Base):
    __tablename__ = "weather_measurements"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"), index=True)
    datetime_utc: Mapped[datetime] = mapped_column(DateTime, index=True)

    temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    relative_humidity: Mapped[float | None] = mapped_column(Float, nullable=True)
    precipitation_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    wind_speed_kmh: Mapped[float | None] = mapped_column(Float, nullable=True)

    source: Mapped[str | None] = mapped_column(String(120), nullable=True)

    city: Mapped["City"] = relationship(back_populates="weather_measurements")

    __table_args__ = (
        UniqueConstraint("city_id", "datetime_utc", name="uq_weather_city_datetime"),
    )


class Anomaly(Base):
    __tablename__ = "anomalies"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"), index=True)
    pollutant: Mapped[str] = mapped_column(String(20), index=True)
    datetime_utc: Mapped[datetime] = mapped_column(DateTime, index=True)
    value: Mapped[float] = mapped_column(Float)
    z_score: Mapped[float] = mapped_column(Float)
    method: Mapped[str] = mapped_column(String(20), default="zscore")

    city: Mapped["City"] = relationship(back_populates="anomalies")
