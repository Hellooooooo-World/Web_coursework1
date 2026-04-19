from fastapi import FastAPI

from app.database import Base, engine
import app.models  # ensure models are registered for create_all
from app.routers import analytics, cities, measurements, weather_measurements

app = FastAPI(
    title="Global Air Quality Anomaly & City Comparison API",
    version="0.1.0",
    description="Coursework API for air-quality anomaly detection and city comparison.",
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(cities.router)
app.include_router(measurements.router)
app.include_router(weather_measurements.router)
app.include_router(analytics.router)
