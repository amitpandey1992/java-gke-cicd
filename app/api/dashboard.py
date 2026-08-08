"""Dashboard data endpoint."""

import logging
from typing import Dict, List, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.database import postgres_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Dashboard"])

class DashboardStatsResponse(BaseModel):
    total_failures: int
    ai_resolved: int
    ai_resolution_rate: float
    avg_resolution_time_seconds: float
    failures_by_platform: Dict[str, int]
    failures_by_category: Dict[str, int]
    recent_failures: List[Dict[str, Any]]
    failures_over_time: List[Dict[str, Any]]

class TopErrorResponse(BaseModel):
    category: str
    count: int

@router.get("/stats", response_model=DashboardStatsResponse)
async def get_stats():
    """Gets dashboard statistics."""
    try:
        stats = postgres_client.get_dashboard_stats()
        return DashboardStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch dashboard statistics."
        )

@router.get("/stats/top-errors", response_model=List[TopErrorResponse])
async def get_top_errors():
    """Gets top recurring error patterns."""
    try:
        errors = postgres_client.get_top_errors(limit=10)
        return [TopErrorResponse(**e) for e in errors]
    except Exception as e:
        logger.error(f"Error fetching top errors: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch top errors."
        )
