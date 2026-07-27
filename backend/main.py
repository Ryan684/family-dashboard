import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from routers.calendar import router as calendar_router
from routers.travel import router as travel_router
from routers.weather import router as weather_router
from scheduler import run_scheduler

DIST_DIR = Path(__file__).parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the background polling loop, and cancel it on shutdown.

    Replaces the deprecated `@app.on_event("startup")` hook: Starlette has
    removed on_event entirely, and FastAPI only still accepts it via a
    compatibility shim of its own.
    """
    task = asyncio.create_task(run_scheduler())
    try:
        yield
    finally:
        task.cancel()


app = FastAPI(title="Family Dashboard API", lifespan=lifespan)

app.include_router(travel_router)
app.include_router(weather_router)
app.include_router(calendar_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def serve_root():
    return FileResponse(DIST_DIR / "index.html")


if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")
