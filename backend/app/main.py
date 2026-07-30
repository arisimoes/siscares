from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.db.base import Base, engine
from app.routers import auth, schools, classes, students, attendance, modules, reports, transfers, calendar, logs, uploads
from app.db import seed
from app.services.attendance_scheduler import start_attendance_scheduler

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="../frontend/static"), name="static")
templates = Jinja2Templates(directory="../frontend/templates")

app.include_router(auth.router, prefix="/api/v1")
app.include_router(schools.router, prefix="/api/v1")
app.include_router(classes.router, prefix="/api/v1")
app.include_router(students.router, prefix="/api/v1")
app.include_router(attendance.router, prefix="/api/v1")
app.include_router(transfers.router, prefix="/api/v1")
app.include_router(modules.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(calendar.router, prefix="/api/v1")
app.include_router(logs.router, prefix="/api/v1")
app.include_router(uploads.router, prefix="/api/v1")


@app.on_event("startup")
def on_startup():
    from app.db.base import ensure_schema, ensure_column_exists
    ensure_schema()
    ensure_column_exists("students", "is_transferred_externally", "BOOLEAN DEFAULT FALSE")
    seed.seed_modules()
    start_attendance_scheduler()


@app.get("/")
def index(request: Request):
    return RedirectResponse(url="/static/pages/login.html")
