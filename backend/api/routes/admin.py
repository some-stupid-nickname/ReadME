"""Admin API endpoints for metrics and analytics"""
from fastapi import APIRouter, HTTPException, status, Depends, Header
from typing import Optional
from loguru import logger
import os
from datetime import datetime, timedelta

from models.schemas import MetricsResponse
from api.dependencies import get_postgres_db

router = APIRouter(prefix="/admin", tags=["Admin"])


# Simple cache for metrics (5 minutes)
_metrics_cache = None
_cache_timestamp = None
CACHE_TTL_SECONDS = 300  # 5 minutes


def verify_admin_api_key(x_api_key: Optional[str] = Header(None)):
    """
    Verify admin API key (optional, for educational project).
    If ADMIN_API_KEY is set in environment, require it.
    Otherwise, allow unauthenticated access (for demo/educational purposes).
    """
    admin_key = os.getenv('ADMIN_API_KEY')
    
    if admin_key:
        # API key is configured, require it
        if not x_api_key or x_api_key != admin_key:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or missing API key"
            )
    
    # If no API key configured, allow access (educational project)
    return True


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    db = Depends(get_postgres_db),
    _verified = Depends(verify_admin_api_key)
):
    """
    Get system metrics and analytics.
    
    Optional authentication:
    - If ADMIN_API_KEY is set in environment, requires X-API-Key header
    - Otherwise, publicly accessible (for educational/demo purposes)
    
    Metrics include:
    - User counts (total, active in 7 days)
    - Query counts (all time, today, this week)
    - Primary acceptance rate (books added to library / books shown)
    - Final acceptance rate (books rated ≥7 / books in library)
    - Average library size
    - Average and median ratings
    
    Results are cached for 5 minutes to reduce database load.
    """
    global _metrics_cache, _cache_timestamp
    
    # Check cache
    now = datetime.utcnow()
    if _metrics_cache and _cache_timestamp:
        if (now - _cache_timestamp).total_seconds() < CACHE_TTL_SECONDS:
            logger.debug("Returning cached metrics")
            return _metrics_cache
    
    # Fetch fresh metrics
    try:
        logger.info("Fetching fresh metrics from database")
        metrics_data = await db.get_metrics()
        
        response = MetricsResponse(
            total_users=metrics_data['total_users'],
            active_users_7d=metrics_data['active_users_7d'],
            total_queries_all_time=metrics_data['total_queries_all_time'],
            total_queries_today=metrics_data['total_queries_today'],
            total_queries_week=metrics_data['total_queries_week'],
            primary_acceptance_rate=round(metrics_data['primary_acceptance_rate'], 2),
            final_acceptance_rate=round(metrics_data['final_acceptance_rate'], 2),
            avg_library_size=round(metrics_data['avg_library_size'], 1),
            avg_rating=round(metrics_data['avg_rating'], 2),
            median_rating=round(metrics_data['median_rating'], 1)
        )
        
        # Update cache
        _metrics_cache = response
        _cache_timestamp = now
        
        return response
    
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch metrics"
        )
