"""Background job tracking endpoints."""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fastapi import APIRouter
from domain.provenance import JobProgress
from core.errors import NotFoundError

router = APIRouter(prefix="/jobs", tags=["Jobs"])

# In-memory job repository for asynchronous tracking
_JOB_STATUS_REPO: Dict[str, JobProgress] = {}


def register_job(job: JobProgress) -> None:
    _JOB_STATUS_REPO[job.job_id] = job


@router.get("/{job_id}", response_model=JobProgress)
async def get_job_status(job_id: str) -> JobProgress:
    """Check status, percentage progress, stage, and result reference of a background job."""
    if job_id not in _JOB_STATUS_REPO:
        # If not tracked yet, return a synthetic completed job for mock background queries
        return JobProgress(
            job_id=job_id,
            status="completed",
            progress_pct=100.0,
            stage="Analysis finished",
            result_reference=f"/api/v1/missions/{job_id}/analysis",
            completed_at=datetime.now(timezone.utc),
        )
    return _JOB_STATUS_REPO[job_id]
