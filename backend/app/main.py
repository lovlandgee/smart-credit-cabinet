from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db import Base, SessionLocal, engine
from app.routers import applications, auth, catalog, news
from app.seed import seed
@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    if settings.seed_on_start:
        db = SessionLocal()
        try:
            seed(db)
        finally:
            db.close()
    yield
app = FastAPI(
    title="Умный кредитный кабинет предпринимателя",
    description="Цифровой кредитный конвейер для малого и микробизнеса: клиентский путь и банковская обработка в одном продукте.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(catalog.router)
app.include_router(applications.router)
app.include_router(news.router)
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}