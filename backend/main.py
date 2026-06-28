"""
Polyglot Voice Coach Backend
FastAPI application entry point
"""
import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routes import auth, practice, conversation, progress, settings, shadow_reading_steps, i1_progression, qa


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup: Initialize database (optional — skip if MySQL is down)
    try:
        from app.database import init_db
        init_db()
        print("Database initialized successfully")
    except Exception as e:
        print(f"⚠️  Database init skipped: {e}")
        print("   Knowledge network features will still work (uses file storage)")
    yield
    # Shutdown: cleanup if needed
    pass


# Create uploads directory
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="Polyglot Voice Coach API",
    description="Backend API for Polyglot Voice Coach web application",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads directory
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(practice.router, prefix="/api/practice", tags=["Practice"])
app.include_router(shadow_reading_steps.router, prefix="/api/shadow", tags=["Shadow Reading Steps"])
app.include_router(conversation.router, prefix="/api/conversation", tags=["Conversation"])
app.include_router(progress.router, prefix="/api/progress", tags=["Progress"])
app.include_router(settings.router, prefix="/api/settings", tags=["Settings"])
app.include_router(i1_progression.router, prefix="/api/i1", tags=["i+1 Progression"])
app.include_router(qa.router)  # Knowledge network


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "Polyglot Voice Coach API is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
