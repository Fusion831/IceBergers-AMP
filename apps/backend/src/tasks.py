"""Asynchronous background tasks for AMIP."""

import logging
from typing import Dict, Any
from worker import celery_app
from domain.provenance import JobProgress
from api.routers.jobs import register_job
from api.dependencies import get_mission_service

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="tasks.async_analyze_mission")
def async_analyze_mission(self, mission_id: str) -> Dict[str, Any]:
    """Background task to run heavy 4D mission route optimization and risk analysis."""
    job_id = self.request.id or f"job-{mission_id}"
    logger.info("Starting asynchronous mission analysis for mission: %s (Job %s)", mission_id, job_id)

    # Update progress 10%
    register_job(
        JobProgress(
            job_id=job_id,
            status="running",
            progress_pct=10.0,
            stage="Ingesting ocean and sea ice forecast layers",
            result_reference=f"/api/v1/missions/{mission_id}/analysis",
        )
    )

    # Execute mission analysis
    mission_service = get_mission_service()
    result = mission_service.analyze_mission(mission_id)

    # Update progress 100%
    register_job(
        JobProgress(
            job_id=job_id,
            status="completed",
            progress_pct=100.0,
            stage="Completed 4-way route optimization and 4D validation",
            result_reference=f"/api/v1/missions/{mission_id}/analysis",
        )
    )

    logger.info("Finished asynchronous mission analysis for mission: %s", mission_id)
    return result
