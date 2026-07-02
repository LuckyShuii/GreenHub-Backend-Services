from fastapi import FastAPI

app = FastAPI(
    title="Greener API",
    version="0.1.0",
)

# Checks if the API is running
@app.get("/health", tags=["health"], summary="Health Check")
async def health_check():
    return {"status": "ok"}