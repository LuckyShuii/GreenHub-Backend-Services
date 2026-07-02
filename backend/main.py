from routers import health
from fastapi import FastAPI


app = FastAPI(
    title="Greener API",
    version="0.1.0",
)

app.include_router(health.router)