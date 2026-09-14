from fastapi import APIRouter, FastAPI

from routers import health

API_PREFIX = "/api"

app = FastAPI(
    title="Greener API",
    version="0.1.0",
    docs_url=f"{API_PREFIX}/docs",
    redoc_url=f"{API_PREFIX}/redoc",
    openapi_url=f"{API_PREFIX}/openapi.json",
    swagger_ui_oauth2_redirect_url=f"{API_PREFIX}/docs/oauth2-redirect",
)

# The app owns /api, so paths are identical locally and behind the prod gateway
# (which routes without rewriting). Mount business routers here.
api_router = APIRouter(prefix=API_PREFIX)

app.include_router(api_router)

# /health is an infra liveness probe (container healthcheck, gateway): outside /api.
app.include_router(health.router)
