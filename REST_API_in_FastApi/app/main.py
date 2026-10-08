from fastapi import FastAPI

from app.routes import router
from app.database import Base, engine

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()

app = FastAPI(
    title="Advertisement API",
    description="REST API сервиса объявлений купли и продажи",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)

@app.get("/health", tags=["Service"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}