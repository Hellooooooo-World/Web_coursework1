import os
import secrets

from fastapi import Depends, FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import select

from app.database import Base, SessionLocal, engine
import app.models  # ensure models are registered for create_all
from app.models import User
from app.routers import analytics, cities, measurements, weather_measurements
from app.routers import auth as auth_router
from app.routers import users as users_router
from app.security import get_password_hash, get_session_user, require_session_user

NO_STORE_HEADERS = {"Cache-Control": "no-store", "Pragma": "no-cache", "Expires": "0"}

app = FastAPI(
    title="Global Air Quality Anomaly & City Comparison API",
    version="0.1.0",
    description="Coursework API for air-quality anomaly detection and city comparison.",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

session_secret = os.getenv("SESSION_SECRET")
if not session_secret:
    # No env var set → generate a new secret per process start,
    # so all browsers must re-login after server restarts.
    session_secret = secrets.token_urlsafe(48)

app.add_middleware(
    SessionMiddleware,
    secret_key=session_secret,
    same_site="lax",
    https_only=False,
)


@app.get("/", include_in_schema=False)
def root(user: User | None = Depends(get_session_user)):
    if user is None:
        return RedirectResponse(url="/login?next=/", status_code=302, headers=NO_STORE_HEADERS)
    return HTMLResponse(
        """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>API Home</title>
    <style>
      :root { color-scheme: light dark; }
      body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 0; }
      .wrap { max-width: 860px; margin: 0 auto; padding: 48px 20px; }
      .card { border: 1px solid rgba(128,128,128,.35); border-radius: 14px; padding: 22px; }
      h1 { margin: 0 0 8px; font-size: 22px; }
      p { margin: 8px 0 0; line-height: 1.45; opacity: .9; }
      .btn-row { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 16px; }
      a.btn {
        display: inline-block;
        padding: 10px 14px;
        border-radius: 10px;
        border: 1px solid rgba(128,128,128,.45);
        text-decoration: none;
        font-weight: 600;
      }
      a.primary { background: #2563eb; border-color: #2563eb; color: #fff; }
      a.secondary { background: transparent; }
      code { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
    </style>
  </head>
  <body>
    <div class="wrap">
      <div class="card">
        <h1>Global Air Quality Anomaly & City Comparison API</h1>
        <p>The server is running. Use the button below to open interactive API docs.</p>
        <div class="btn-row">
          <a class="btn primary" href="/docs">Open Swagger Docs</a>
        </div>
        <p style="margin-top:14px;"><small>Tip: the OpenAPI schema is at <code>/openapi.json</code>.</small></p>
      </div>
    </div>
  </body>
</html>
""".strip()
    , headers=NO_STORE_HEADERS)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    admin_username = os.getenv("BASIC_AUTH_USERNAME", "admin")
    admin_password = os.getenv("BASIC_AUTH_PASSWORD", "admin")

    db = SessionLocal()
    try:
        existing = db.scalar(select(User).where(User.username == admin_username))
        if not existing:
            db.add(User(username=admin_username, password_hash=get_password_hash(admin_password)))
            db.commit()
    finally:
        db.close()


@app.get("/openapi.json", include_in_schema=False)
def protected_openapi(user: User = Depends(require_session_user)) -> JSONResponse:
    _ = user
    return JSONResponse(app.openapi(), headers=NO_STORE_HEADERS)


@app.get("/docs", include_in_schema=False)
def protected_swagger_ui(user: User | None = Depends(get_session_user)):
    if user is None:
        return RedirectResponse(url="/login?next=/docs", status_code=302, headers=NO_STORE_HEADERS)
    resp = get_swagger_ui_html(openapi_url="/openapi.json", title=f"{app.title} - Swagger UI")
    resp.headers.update(NO_STORE_HEADERS)
    return resp


app.include_router(cities.router, dependencies=[Depends(require_session_user)])
app.include_router(measurements.router, dependencies=[Depends(require_session_user)])
app.include_router(weather_measurements.router, dependencies=[Depends(require_session_user)])
app.include_router(analytics.router, dependencies=[Depends(require_session_user)])
app.include_router(users_router.router, dependencies=[Depends(require_session_user)])
app.include_router(auth_router.router)
