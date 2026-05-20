import os
import uvicorn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


# =========================================================
# NexusOS Runtime
# =========================================================

app = FastAPI(
    title="NexusOS",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# Root Endpoint
# =========================================================

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "NexusOS",
        "runtime": "active"
    }


# =========================================================
# Health Endpoint
# =========================================================

@app.get("/api/health")
async def health():
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "NexusOS",
            "deployment": "railway",
            "version": "1.0.0"
        }
    )


# =========================================================
# Debug Endpoint
# =========================================================

@app.get("/api/debug")
async def debug():
    return {
        "PORT": os.environ.get("PORT"),
        "PYTHONPATH": os.environ.get("PYTHONPATH"),
        "environment": "production"
    }


# =========================================================
# Startup Event
# =========================================================

@app.on_event("startup")
async def startup_event():
    print("====================================")
    print(" NexusOS Runtime Started")
    print("====================================")
    print(f"PORT: {os.environ.get('PORT')}")
    print("====================================")


# =========================================================
# Railway Runtime Boot
# =========================================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 8000))

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        access_log=True,
    )