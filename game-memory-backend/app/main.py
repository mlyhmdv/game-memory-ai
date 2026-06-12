from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.core.config import settings
from app.api import api_router
from app.db.session import create_tables

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create DB tables. Shutdown: cleanup."""
    await create_tables()
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    print("Game Memory AI backend started")
    print(f"Uploads directory: {upload_dir.absolute()}")
    yield
    print("Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## Game Memory AI — Backend API

Your personal RPG journal powered by AI.

### Features
- 🔐 JWT Authentication
- 🎮 Game library management
- 🧠 AI-powered screenshot analysis (Claude Vision)
- 📅 Session timeline
- 💬 AI chat about your game history
- 🚀 "Continue Journey" smart summary
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS — allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded screenshots as static files
upload_dir = Path(settings.UPLOAD_DIR)
upload_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")

# Register all routes under /api/v1
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Health"])
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}


if FRONTEND_DIR.exists():
    js_dir = FRONTEND_DIR / "js"
    if js_dir.exists():
        app.mount("/js", StaticFiles(directory=str(js_dir)), name="js")

    @app.get("/")
    async def serve_index():
        return FileResponse(FRONTEND_DIR / "index.html")

    @app.get("/{filename}")
    async def serve_frontend(filename: str):
        if filename.startswith("api/") or filename in ("docs", "redoc", "openapi.json"):
            raise HTTPException(status_code=404)
        file_path = FRONTEND_DIR / filename
        if file_path.is_file():
            return FileResponse(file_path)
        html_path = FRONTEND_DIR / f"{filename}.html"
        if html_path.is_file():
            return FileResponse(html_path)
        raise HTTPException(status_code=404)
