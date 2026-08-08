"""Feedback endpoint."""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.database import postgres_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Feedback"])

class FeedbackRequest(BaseModel):
    analysis_id: str
    helpful: bool
    actual_fix: Optional[str] = None
    engineer_name: Optional[str] = None

class FeedbackResponse(BaseModel):
    message: str
    updated_confidence: float

@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    """Submits feedback for an analysis."""
    try:
        logger.info(f"Received feedback for {request.analysis_id}")
        
        # 1. Update confidence score in ChromaDB (mocked)
        updated_confidence = 0.9 if request.helpful else 0.4
        
        # 2. If actual_fix provided, store as verified fix (handled in postgres)
        
        # 3. Update PostgreSQL stats
        postgres_client.update_feedback(
            analysis_id=request.analysis_id,
            helpful=request.helpful,
            actual_fix=request.actual_fix
        )
        
        return FeedbackResponse(
            message="Feedback recorded successfully",
            updated_confidence=updated_confidence
        )
    except Exception as e:
        logger.error(f"Error processing feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process feedback."
        )
