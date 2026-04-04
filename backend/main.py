from fastapi import FastAPI

from routers.travel import router as travel_router
from routers.weather import router as weather_router

app = FastAPI(title="Family Dashboard API")

app.include_router(travel_router)
app.include_router(weather_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
