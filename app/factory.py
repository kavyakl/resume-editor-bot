"""
Application factory for Resume Editor Bot.

This module provides a factory function to create the FastAPI application
with proper configuration and middleware setup.
"""

import logging.config
import yaml
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
from app.core.config import settings


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured application instance
    """
    # Load logging configuration
    log_config_path = Path("config/logging.yaml")
    if log_config_path.exists():
        with open(log_config_path, "r") as f:
            log_config = yaml.safe_load(f)
            logging.config.dictConfig(log_config)
    
    # Create FastAPI app
    app = FastAPI(
        title="Resume Editor Bot",
        description="An intelligent resume editing assistant powered by RAG",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routes
    app.include_router(api_router, prefix="/api")
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": "Welcome to Resume Editor Bot API",
            "version": "1.0.0",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "resume-editor-bot"}
    
    return app 