from fastapi import FastAPI

app = FastAPI(title="Family Dashboard API")


@app.get("/health")
async def health():
    return {"status": "ok"}
