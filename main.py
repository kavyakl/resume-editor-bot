"""
Main entry point for Resume Editor Bot.

This module starts the FastAPI application using the application factory.
"""

import uvicorn
from app.factory import create_app

# Create the application
app = create_app()

# Print all registered routes at startup
for route in app.routes:
    print(f"ROUTE: {route.path}  METHODS: {route.methods}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 