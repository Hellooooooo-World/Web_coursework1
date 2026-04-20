from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from sqlalchemy.exc import IntegrityError
from starlette.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import get_password_hash, verify_password

router = APIRouter(tags=["auth"])

NO_STORE_HEADERS = {"Cache-Control": "no-store", "Pragma": "no-cache", "Expires": "0"}


@router.get("/login", include_in_schema=False)
def login_page(
    next: str = Query(default="/docs"),
) -> HTMLResponse:
    html = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Sign in</title>
    <style>
      :root { color-scheme: light dark; }
      body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 0; }
      .wrap { max-width: 860px; margin: 0 auto; padding: 48px 20px; }
      .card { border: 1px solid rgba(128,128,128,.35); border-radius: 14px; padding: 22px; }
      h1 { margin: 0 0 8px; font-size: 22px; }
      p { margin: 8px 0 0; line-height: 1.45; opacity: .9; }
      label { display: block; margin-top: 12px; font-weight: 600; }
      input {
        width: 100%;
        padding: 10px 12px;
        margin-top: 6px;
        border-radius: 10px;
        border: 1px solid rgba(128,128,128,.45);
        background: transparent;
      }
      .btn-row { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 16px; }
      button, a.btn {
        display: inline-block;
        padding: 10px 14px;
        border-radius: 10px;
        border: 1px solid rgba(128,128,128,.45);
        text-decoration: none;
        font-weight: 600;
        background: transparent;
        cursor: pointer;
      }
      button.primary { background: #2563eb; border-color: #2563eb; color: #fff; }
      a.secondary { background: transparent; }
      small { opacity: .85; }
      code { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
    </style>
  </head>
  <body>
    <div class="wrap">
      <div class="card">
        <h1>Sign in</h1>
        <p>Sign in to access the API docs and protected endpoints.</p>
        <form method="post" action="/login">
          <label for="username">Username</label>
          <input id="username" name="username" minlength="3" maxlength="50" required />

          <label for="password">Password</label>
          <input id="password" name="password" type="password" minlength="6" maxlength="128" required />
          <input type="hidden" name="next" value="__NEXT__" />

          <div class="btn-row">
            <button class="primary" type="submit">Sign in</button>
            <a class="btn secondary" href="/">Home</a>
            <a class="btn secondary" href="/signup?next=__NEXT__">Create account</a>
          </div>
        </form>
        <p style="margin-top:12px;"><small>After signing in, you will be redirected to <code>__NEXT__</code>.</small></p>
      </div>
    </div>
  </body>
</html>
""".strip()
    html = html.replace("__NEXT__", next)
    return HTMLResponse(html, headers=NO_STORE_HEADERS)


@router.get("/signup", include_in_schema=False)
def signup_page(
    next: str = Query(default="/"),
) -> HTMLResponse:
    html = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Sign up</title>
    <style>
      :root { color-scheme: light dark; }
      body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 0; }
      .wrap { max-width: 860px; margin: 0 auto; padding: 48px 20px; }
      .card { border: 1px solid rgba(128,128,128,.35); border-radius: 14px; padding: 22px; }
      h1 { margin: 0 0 8px; font-size: 22px; }
      p { margin: 8px 0 0; line-height: 1.45; opacity: .9; }
      label { display: block; margin-top: 12px; font-weight: 600; }
      input {
        width: 100%;
        padding: 10px 12px;
        margin-top: 6px;
        border-radius: 10px;
        border: 1px solid rgba(128,128,128,.45);
        background: transparent;
      }
      .btn-row { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 16px; }
      button, a.btn {
        display: inline-block;
        padding: 10px 14px;
        border-radius: 10px;
        border: 1px solid rgba(128,128,128,.45);
        text-decoration: none;
        font-weight: 600;
        background: transparent;
        cursor: pointer;
      }
      button.primary { background: #16a34a; border-color: #16a34a; color: #fff; }
      a.secondary { background: transparent; }
      small { opacity: .85; }
      code { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
    </style>
  </head>
  <body>
    <div class="wrap">
      <div class="card">
        <h1>Create account</h1>
        <p>Create a new account, then sign in.</p>
        <form method="post" action="/signup">
          <label for="username">Username</label>
          <input id="username" name="username" minlength="3" maxlength="50" required />

          <label for="password">Password</label>
          <input id="password" name="password" type="password" minlength="6" maxlength="128" required />

          <input type="hidden" name="next" value="__NEXT__" />

          <div class="btn-row">
            <button class="primary" type="submit">Create account</button>
            <a class="btn secondary" href="/login?next=__NEXT__">Back to sign in</a>
          </div>
        </form>
        <p style="margin-top:12px;"><small>After signup, you will be redirected to <code>/login</code>.</small></p>
      </div>
    </div>
  </body>
</html>
""".strip()
    html = html.replace("__NEXT__", next)
    return HTMLResponse(html, headers=NO_STORE_HEADERS)


@router.post("/signup", include_in_schema=False)
def signup(
    request: Request,
    username: str = Form(..., min_length=3, max_length=50),
    password: str = Form(..., min_length=6, max_length=128),
    next: str = Form(default="/"),
    db: Session = Depends(get_db),
):
    user = User(username=username, password_hash=get_password_hash(password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        page = signup_page(next=next).body.decode("utf-8").replace(
            "<p>Create a new account, then sign in.</p>",
            '<p style="color:#ef4444;font-weight:700;">Username already exists.</p>',
        )
        return HTMLResponse(page, status_code=409, headers=NO_STORE_HEADERS)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create account.") from exc

    db.refresh(user)
    # Auto sign-in after successful signup.
    request.session["user_id"] = int(user.id)
    return RedirectResponse(url=next or "/", status_code=303, headers=NO_STORE_HEADERS)


@router.post("/login", include_in_schema=False)
def login(
    request: Request,
    username: str = Form(..., min_length=3, max_length=50),
    password: str = Form(..., min_length=1, max_length=128),
    next: str = Form(default="/docs"),
    db: Session = Depends(get_db),
):
    user = db.scalar(select(User).where(User.username == username))
    if not user or not verify_password(password, user.password_hash):
        page = login_page(next=next).body.decode("utf-8").replace(
            "<p>Sign in to access the API docs and protected endpoints.</p>",
            '<p style="color:#ef4444;font-weight:700;">Invalid username or password.</p>',
        )
        return HTMLResponse(page, status_code=400, headers=NO_STORE_HEADERS)

    request.session["user_id"] = int(user.id)
    return RedirectResponse(url=next or "/docs", status_code=303, headers=NO_STORE_HEADERS)


@router.post("/logout", include_in_schema=False)
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303, headers=NO_STORE_HEADERS)
