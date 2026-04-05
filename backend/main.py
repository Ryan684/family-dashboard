import asyncio

from fastapi import FastAPI

from routers.calendar import router as calendar_router
from routers.travel import router as travel_router
from routers.weather import router as weather_router
from scheduler import run_scheduler

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
