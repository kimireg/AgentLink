"""
AgentLink Relay Server
FastAPI application for Agent-to-Agent communication
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
import logging

from config import settings
from models import Base, Agent, MessageQueue
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import redis.asyncio as redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Redis setup
redis_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global redis_client
    
    # Startup: Initialize database and Redis
    try:
        # Create database tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created")
        
        # Connect to Redis
        redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        await redis_client.ping()
        logger.info("Connected to Redis")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise
    
    yield
    
    # Shutdown: Close connections
    try:
        await redis_client.close()
        logger.info("Redis connection closed")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "status": "running"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    try:
        # Check database
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        
        # Check Redis
        await redis_client.ping()
        
        return {
            "status": "healthy",
            "database": "connected",
            "redis": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

@app.get("/api/status")
async def status():
    """Get server status and statistics"""
    try:
        # Get active connections from Redis
        active_connections = await redis_client.scard("active_connections")
        
        # Get pending messages
        pending_messages = await redis_client.llen("message_queue")
        
        return {
            "active_agents": active_connections,
            "pending_messages": pending_messages,
            "uptime": "running"
        }
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return {
            "active_agents": 0,
            "pending_messages": 0,
            "error": str(e)
        }

# Import routes
from routes import register, agent_card
from websocket import manager, router

# Include API routes
app.include_router(register.router, prefix="/api")
app.include_router(agent_card.router, prefix="/api")

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for Agent connections"""
    await manager.handle_connection(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
