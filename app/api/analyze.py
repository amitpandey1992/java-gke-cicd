"""Analysis endpoint — the core of the AI CI/CD Failure Analyzer."""

import logging
import uuid
import json
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.config import get_settings
from app.processing.sanitizer import sanitize_log
from app.processing.truncator import truncate_log
from app.ai_engine.ai_factory import get_ai_caller
from app.ai_engine.prompt_builder import build_analysis_prompt, parse_ai_response
from app.memory.chromadb_store import FailureMemory
from app.memory.similarity_search import SimilaritySearcher

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Analysis"])

# Initialize memory store (lazy singleton)
_failure_memory: Optional[FailureMemory] = None
_similarity_searcher: Optional[SimilaritySearcher] = None


def _get_memory():
    """Get or create the failure memory singleton."""
    global _failure_memory, _similarity_searcher
    if _failure_memory is None:
        settings = get_settings()
        _failure_memory = FailureMemory(persist_directory=settings.chromadb_path)
        _similarity_searcher = SimilaritySearcher(failure_memory=_failure_memory)
    return _failure_memory, _similarity_searcher


class AnalyzeRequest(BaseModel):
    """Request body for build failure analysis."""
    provider: str
    build_url: Optional[str] = None
    job_name: Optional[str] = None
    build_id: Optional[str] = None
    run_id: Optional[str] = None
    repo: Optional[str] = None
    raw_log: Optional[str] = None


class AnalysisResult(BaseModel):
    """Structured analysis result returned to the caller."""
    analysis_id: str
    failure_category: str
    summary: str
    failing_step: str
    root_cause: str
    suggested_fix: str
    confidence: float
    from_memory: bool
    similar_failure_id: Optional[str] = None


@router.post("/analyze", response_model=AnalysisResult, status_code=status.HTTP_200_OK)
async def analyze_failure(request: AnalyzeRequest):
    """Analyze a CI/CD build failure.

    Flow:
        1. Get raw log (from request body or fetch from CI platform)
        2. Sanitize log (remove secrets, ANSI codes)
        3. Truncate log (focus on error sections)
        4. Search ChromaDB for similar past failures
        5. If found (>80% similarity) → return cached fix
        6. If not found → call AI engine for analysis
        7. Store result in ChromaDB and PostgreSQL
        8. Return structured AnalysisResult
    """
    analysis_id = str(uuid.uuid4())[:12]
    settings = get_settings()

    try:
        # --- Step 1: Get raw log ---
        log_content = request.raw_log
        if not log_content:
            # In a full implementation, we'd fetch from CI platform here
            # For now, use a placeholder message
            log_content = (
                f"[{request.provider}] No raw_log provided in request. "
                f"Build URL: {request.build_url or 'N/A'}, "
                f"Job: {request.job_name or 'N/A'}, "
                f"Build ID: {request.build_id or 'N/A'}"
            )
            logger.warning("No raw_log in request — using placeholder")

        logger.info(
            f"Analyzing failure [{analysis_id}] from {request.provider} "
            f"(log size: {len(log_content)} chars)"
        )

        # --- Step 2: Sanitize log ---
        sanitized = sanitize_log(log_content)

        # --- Step 3: Truncate log ---
        truncated = truncate_log(sanitized)

        # --- Step 4: Search memory for similar past failures ---
        from_memory = False
        similar_failure_id = None
        ai_result = None

        try:
            memory, searcher = _get_memory()
            match = searcher.search_similar(truncated)

            if match is not None:
                # Found a similar past failure!
                from_memory = True
                similar_failure_id = match.get("matched_id")
                confidence = match.get("similarity_score", 0.85)
                ai_result = {
                    "failure_category": match.get("failure_category", "UNKNOWN"),
                    "summary": match.get("matched_summary", "Similar failure found in memory"),
                    "failing_step": match.get("failing_step", "See previous analysis"),
                    "root_cause": match.get("root_cause", "See previous analysis"),
                    "suggested_fix": match.get("previous_fix", "Apply the same fix as last time"),
                }
                logger.info(
                    f"Memory hit! Similar failure [{similar_failure_id}] "
                    f"with {confidence:.0%} similarity — skipping AI call"
                )
        except Exception as e:
            logger.warning(f"ChromaDB search failed (continuing with AI): {e}")

        # --- Step 5/6: Call AI if no memory hit ---
        if ai_result is None:
            try:
                ai_caller = get_ai_caller(settings)
                prompt = build_analysis_prompt(
                    sanitized_log=truncated,
                    provider=request.provider,
                    job_name=request.job_name,
                )
                raw_response = await ai_caller.analyze(prompt)
                ai_result = parse_ai_response(raw_response)
                confidence = 0.75  # Initial confidence for new AI analysis
                logger.info(f"AI analysis complete: {ai_result.get('failure_category', 'UNKNOWN')}")
            except Exception as e:
                logger.error(f"AI analysis failed: {e}")
                ai_result = {
                    "failure_category": "UNKNOWN",
                    "summary": f"AI analysis failed: {str(e)[:100]}",
                    "failing_step": "N/A",
                    "root_cause": "Could not determine — AI engine unavailable",
                    "suggested_fix": "Check AI engine configuration and retry",
                }
                confidence = 0.0

        # --- Step 7: Store results ---
        # Store in ChromaDB for future similarity searches
        try:
            memory, _ = _get_memory()
            memory.store_failure(
                analysis_id=analysis_id,
                sanitized_log=truncated,
                analysis_result=ai_result,
            )
        except Exception as e:
            logger.warning(f"Failed to store in ChromaDB: {e}")

        # Store in PostgreSQL for dashboard stats
        try:
            from app.database.postgres_client import insert_failure
            insert_failure({
                "analysis_id": analysis_id,
                "provider": request.provider,
                "job_name": request.job_name,
                "build_url": request.build_url,
                "failure_category": ai_result.get("failure_category", "UNKNOWN"),
                "summary": ai_result.get("summary", ""),
                "root_cause": ai_result.get("root_cause", ""),
                "suggested_fix": ai_result.get("suggested_fix", ""),
                "confidence": confidence,
                "from_memory": from_memory,
            })
        except Exception as e:
            logger.warning(f"Failed to store in PostgreSQL: {e}")

        # --- Step 8: Return result ---
        return AnalysisResult(
            analysis_id=analysis_id,
            failure_category=ai_result.get("failure_category", "UNKNOWN"),
            summary=ai_result.get("summary", "Analysis complete"),
            failing_step=ai_result.get("failing_step", "N/A"),
            root_cause=ai_result.get("root_cause", "N/A"),
            suggested_fix=ai_result.get("suggested_fix", "N/A"),
            confidence=confidence,
            from_memory=from_memory,
            similar_failure_id=similar_failure_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error analyzing failure [{analysis_id}]: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze build failure: {str(e)[:200]}",
        )
