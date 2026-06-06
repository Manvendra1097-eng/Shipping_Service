from contextlib import asynccontextmanager

from fastapi import FastAPI
from scalar_fastapi import get_scalar_api_reference

from app.api.router import app_router
from app.database.session import init_db


@asynccontextmanager
async def life_span(app: FastAPI):
    print("Server started .......")
    await init_db()
    yield
    print("Server stopping ...")


app = FastAPI(lifespan=life_span)

app.include_router(app_router)


@app.get("/api_docs", include_in_schema=False)
def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
    )
