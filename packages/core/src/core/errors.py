"""AMIP Domain Exceptions and RFC 7807 Error Definitions."""

from typing import Any, Dict, List, Optional


class AMIPException(Exception):
    """Base exception for all AMIP domain errors."""
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        invalid_params: Optional[List[Dict[str, str]]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        self.invalid_params = invalid_params or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": f"urn:amip:error:{self.code.lower()}",
            "title": self.code.replace("_", " ").title(),
            "status": self.status_code,
            "detail": self.message,
            "details": self.details,
            "invalid_params": self.invalid_params,
        }


AMIPBaseError = AMIPException


class NotFoundError(AMIPException):
    """Resource not found (HTTP 404)."""
    def __init__(self, resource: str, identifier: Any = None, details: Optional[Dict[str, Any]] = None):
        if identifier is not None:
            msg = f"{resource} with identifier '{identifier}' was not found."
        else:
            msg = resource
        super().__init__(
            message=msg,
            code="RESOURCE_NOT_FOUND",
            status_code=404,
            details=details,
        )


class ValidationError(AMIPException):
    """Data or parameter validation failure (HTTP 422)."""
    def __init__(self, message: str, invalid_params: Optional[List[Dict[str, str]]] = None):
        super().__init__(
            message=message,
            code="VALIDATION_FAILED",
            status_code=422,
            invalid_params=invalid_params,
        )


class ConstraintViolationError(AMIPException):
    """Hard navigational constraint violated (HTTP 422)."""
    def __init__(self, message: str, constraint_type: str = "GENERAL", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=f"CONSTRAINT_VIOLATION_{constraint_type.upper()}",
            status_code=422,
            details=details,
        )


class ModelNotFoundError(AMIPException):
    """Requested model version or weights artifact not found (HTTP 404)."""
    def __init__(self, model_name: str, version: str):
        super().__init__(
            message=f"Model '{model_name}' version '{version}' is not registered or artifacts are missing.",
            code="MODEL_NOT_FOUND",
            status_code=404,
            details={"model_name": model_name, "version": version},
        )


class TemporalLeakageError(AMIPException):
    """Historical replay attempted to access observation data beyond simulated cutoff date (HTTP 400)."""
    def __init__(self, cutoff_date_or_message: str, requested_date: Optional[str] = None):
        if requested_date is not None:
            msg = f"Temporal leakage detected: query requested data at {requested_date} which exceeds cutoff {cutoff_date_or_message}."
            details = {"cutoff_date": cutoff_date_or_message, "requested_date": requested_date}
        else:
            msg = cutoff_date_or_message
            details = {}
        super().__init__(
            message=msg,
            code="TEMPORAL_LEAKAGE_DETECTED",
            status_code=400,
            details=details,
        )


class RoutingError(AMIPException):
    """Routing optimization failed to converge or find a feasible path (HTTP 422)."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="ROUTING_FAILED",
            status_code=422,
            details=details,
        )


class DataNotAvailableError(AMIPException):
    """Requested environmental variable, date, or bounding box is outside dataset coverage (HTTP 404)."""
    def __init__(self, variable: str, timestamp: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Environmental data for '{variable}' at timestamp '{timestamp}' is not available.",
            code="DATA_NOT_AVAILABLE",
            status_code=404,
            details=details,
        )
