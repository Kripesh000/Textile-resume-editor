import logging
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import engine, Base
from app.db_models import UserDB, ProfileDB, ResumeVariantDB  # noqa: F401
from app.routers import auth, profile, variant_router, template_router
# from app.routers import resumes, pdf, ai

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="TeXTile API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Catch-all exception handler: ensures unhandled errors return a proper
# JSON response so the CORSMiddleware can still attach CORS headers.
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )


app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(variant_router.router)
app.include_router(template_router.router)
# app.include_router(resumes.router)
# app.include_router(pdf.router)
# app.include_router(ai.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
