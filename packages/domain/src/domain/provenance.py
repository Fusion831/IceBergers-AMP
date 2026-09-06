"""Provenance tracking, job status, and audit records."""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from uuid import uuid4
from pydantic import BaseModel, Field, model_validator
from domain.enums import JobStatus


class DatasetProvenance(BaseModel):
    """Provenance record for ingested or generated environmental datasets."""
    dataset_id: Optional[str] = "copernicus-seaice-poc"
    variable_name: Optional[str] = "sea_ice_concentration"
    source: str = "OSI-SAF / AMSR2 Mock"
    version: Optional[str] = "2026.1"
    initialization_time: Optional[datetime] = None
    valid_time: Optional[datetime] = None
    coverage_start: Optional[datetime] = None
    coverage_end: Optional[datetime] = None
    uri: Optional[str] = None
    checksum: Optional[str] = None

    @model_validator(mode="after")
    def sync_dataset_fields(self) -> "DatasetProvenance":
        now = datetime.now(timezone.utc)
        if self.initialization_time is None:
            self.initialization_time = self.coverage_start or now
        if self.coverage_start is None:
            self.coverage_start = self.initialization_time

        if self.valid_time is None:
            self.valid_time = self.coverage_end or now
        if self.coverage_end is None:
            self.coverage_end = self.valid_time

        if self.uri is None:
            self.uri = f"zarr://{self.dataset_id}/{self.variable_name}"
        return self


class ModelRunRecord(BaseModel):
    """Audit record capturing model execution provenance."""
    run_id: str = Field(default_factory=lambda: f"run-{uuid4().hex[:8]}")
    mission_id: Optional[str] = None
    model_name: Optional[str] = None
    model_id: Optional[str] = None
    model_version: str = "1.0.0-poc"
    execution_timestamp: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    execution_duration_ms: Optional[int] = None
    execution_duration_seconds: Optional[float] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    input_dataset_refs: Dict[str, str] = Field(default_factory=dict)
    datasets: Optional[List[DatasetProvenance]] = None
    artifact_checksum: Optional[str] = None
    git_commit: Optional[str] = "HEAD"
    is_mock: bool = True

    @model_validator(mode="after")
    def sync_run_record(self) -> "ModelRunRecord":
        if self.model_id is not None and self.model_name is None:
            self.model_name = self.model_id
        elif self.model_name is not None and self.model_id is None:
            self.model_id = self.model_name
        elif self.model_id is None and self.model_name is None:
            self.model_id = "AMIP-Mock-Pipeline-v1"
            self.model_name = self.model_id

        if self.executed_at is not None and self.execution_timestamp is None:
            self.execution_timestamp = self.executed_at
        elif self.execution_timestamp is not None and self.executed_at is None:
            self.executed_at = self.execution_timestamp
        elif self.executed_at is None:
            self.executed_at = datetime.now(timezone.utc)
            self.execution_timestamp = self.executed_at

        if self.execution_duration_seconds is not None and self.execution_duration_ms is None:
            self.execution_duration_ms = int(self.execution_duration_seconds * 1000)
        elif self.execution_duration_ms is not None and self.execution_duration_seconds is None:
            self.execution_duration_seconds = round(self.execution_duration_ms / 1000.0, 3)
        elif self.execution_duration_ms is None:
            self.execution_duration_ms = 450
            self.execution_duration_seconds = 0.45

        return self


class JobProgress(BaseModel):
    """Real-time job execution status and progress tracking."""
    job_id: str
    status: Union[JobStatus, str] = JobStatus.PENDING
    stage: str = Field(default="INITIALIZED")
    progress_percentage: int = Field(default=0, ge=0, le=100)
    progress_pct: Optional[float] = None
    result_url: Optional[str] = None
    result_reference: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    @model_validator(mode="after")
    def sync_job_fields(self) -> "JobProgress":
        if self.progress_pct is not None and self.progress_percentage == 0:
            self.progress_percentage = int(self.progress_pct)
        elif self.progress_percentage > 0 and self.progress_pct is None:
            self.progress_pct = float(self.progress_percentage)
        elif self.progress_pct is None:
            self.progress_pct = float(self.progress_percentage)

        if self.result_reference is not None and self.result_url is None:
            self.result_url = self.result_reference
        elif self.result_url is not None and self.result_reference is None:
            self.result_reference = self.result_url
        return self
