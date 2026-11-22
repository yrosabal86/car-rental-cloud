from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .bootstrap import ensure_admin
from .database import SessionLocal, init_db
from .routers import admin, auth, internal


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    with SessionLocal() as db:
        ensure_admin(db)
    yield


app = FastAPI(
    title="Car Rental - auth-service",
    description="Usuarios, autenticación JWT y control de acceso por roles.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8002", "http://127.0.0.1:8002"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(internal.router)


@app.get("/health", tags=["Health"])
def health():
    return {"service": "auth-service", "status": "ok"}
