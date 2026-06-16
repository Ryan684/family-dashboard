import asyncio
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from routers.calendar import router as calendar_router
from routers.travel import router as travel_router
from routers.weather import router as weather_router
from scheduler import run_scheduler

DIST_DIR = Path(__file__).parent.parent / "frontend" / "dist"

app = FastAPI(title="Family Dashboard API")

app.include_router(travel_router)
app.include_router(weather_router)
app.include_router(calendar_router)


@app.on_event("startup")
async def startup() -> None:
    asyncio.create_task(run_scheduler())


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def serve_root():
    return FileResponse(DIST_DIR / "index.html")


if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")
