from fastapi import FastAPI

from routers.travel import router as travel_router

app = FastAPI(title="Family Dashboard API")

app.include_router(travel_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
