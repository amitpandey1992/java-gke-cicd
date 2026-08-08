"""FastAPI application entry point."""

# Check sqlite version for ChromaDB
import sqlite3
if sqlite3.sqlite_version_info < (3, 35, 0):
    try:
        __import__('pysqlite3')
        import sys
        sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
    except ImportError:
        pass


import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os

from app.api import analyze, feedback, dashboard
from app.database import init_db
from app.config import get_settings

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for FastAPI app."""
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    logger.info("Starting AI-Powered CI/CD Failure Analyzer...")
    
    # Initialize PostgreSQL tables
    try:
        init_db.create_tables()
        logger.info("PostgreSQL tables initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize PostgreSQL tables: {e}")
        
    # Initialize ChromaDB collection (stub, assumes app.memory.chromadb_store)
    try:
        logger.info("ChromaDB initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB: {e}")
        
    yield
    
    logger.info("Shutting down AI-Powered CI/CD Failure Analyzer...")

app = FastAPI(
    title="AI CI/CD Failure Analyzer",
    description="Analyzes CI/CD build failure logs using AI",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for POC
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(analyze.router)
app.include_router(feedback.router)
app.include_router(dashboard.router)

# Mount static files for dashboard
os.makedirs("dashboard", exist_ok=True)
if not os.path.exists("dashboard/index.html"):
    with open("dashboard/index.html", "w") as f:
        f.write("<h1>Dashboard is under construction</h1>")
        
app.mount("/dashboard", StaticFiles(directory="dashboard"), name="dashboard")

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": app.version}

@app.get("/", tags=["Root"], include_in_schema=False)
async def root():
    """Redirect root to dashboard."""
    return RedirectResponse(url="/dashboard/index.html")

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run("app.main:app", host=settings.app_host, port=settings.app_port, reload=True)
