"""FastAPI application main file"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from loguru import logger
import asyncio

from api.routes import search, health
from api.routes import auth, onboarding, library, reviews, books, admin
from core.config import settings
from database.postgres_service import postgres_db
from services.sqlite_helper import sqlite_book_service
from services.background_jobs import PreferenceVectorRecalculator


# Global scheduler variable
scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Handles PostgreSQL connection and background jobs.
    """
    global scheduler
    
    # Startup
    logger.info("Starting Book Recommendation RAG API")
    
    try:
        # Connect to PostgreSQL
        await postgres_db.connect()
        logger.info("PostgreSQL connected")
        
        # Initialize background jobs scheduler
        try:
            from apscheduler.schedulers.asyncio import AsyncIOScheduler
            
            scheduler = AsyncIOScheduler()
            
            # Create preference vector recalculator
            recalculator = PreferenceVectorRecalculator(
                postgres_db=postgres_db,
                sqlite_db=sqlite_book_service
            )
            
            # Schedule to run every hour at :00
            scheduler.add_job(
                recalculator.recalculate_pending_users,
                trigger='cron',
                minute=0,
                max_instances=1,  # Prevent concurrent runs
                id='recalculate_preferences'
            )
            
            scheduler.start()
            logger.info("Background jobs scheduler started")
        except Exception as e:
            logger.warning(f"Failed to start scheduler (apscheduler not installed?): {e}")
        
        # Optional: Prefetch covers for onboarding books
        # This is a background task that doesn't block startup
        asyncio.create_task(prefetch_onboarding_covers())
        
        logger.info("API startup complete")
    
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down API")
    
    if scheduler:
        scheduler.shutdown(wait=True)
        logger.info("Scheduler shut down")
    
    await postgres_db.disconnect()
    logger.info("PostgreSQL disconnected")


async def prefetch_onboarding_covers():
    """
    Background task to prefetch covers for onboarding books.
    Runs asynchronously on startup without blocking.
    """
    try:
        await asyncio.sleep(5)  # Wait for startup to complete
        
        from services.cover_fetch_service import CoverFetchService
        import os
        
        logger.info("Starting onboarding covers prefetch")
        
        onboarding_books = await postgres_db.get_onboarding_books()
        
        cover_service = CoverFetchService(
            postgres_db=postgres_db,
            api_key=os.getenv('GOOGLE_BOOKS_API_KEY')
        )
        
        books_to_fetch = [
            {
                'book_id': book['book_id'],
                'title': book['title'],
                'author': book['author']
            }
            for book in onboarding_books
        ]
        
        await cover_service.prefetch_covers_batch(books_to_fetch)
        logger.info("Onboarding covers prefetch completed")
    
    except Exception as e:
        logger.error(f"Error prefetching covers: {e}")


# Create FastAPI app with lifespan
app = FastAPI(
    title="Book Recommendation RAG API",
    description="RAG-based book recommendation system API with personalization",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers - EXISTING (DO NOT MODIFY THESE)
app.include_router(search.router)
app.include_router(health.router)

# Include NEW routers
app.include_router(auth.router, prefix="/api")
app.include_router(onboarding.router, prefix="/api")
app.include_router(library.router, prefix="/api")
app.include_router(reviews.router, prefix="/api")
app.include_router(books.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Book Recommendation RAG API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    import sys
    from pathlib import Path
    
    # Add backend directory to path for imports
    backend_dir = Path(__file__).parent.parent
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )

