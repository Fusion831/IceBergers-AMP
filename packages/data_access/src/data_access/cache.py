"""Deterministic cache key generation and serialization utilities."""
import hashlib
import json
from datetime import datetime
from typing import Any


def _json_serial(obj: Any) -> Any:
    """JSON serializer for objects not serializable by default json code."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, "dict"):
        return obj.dict()
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    return str(obj)


def generate_cache_key(prefix: str, **params: Any) -> str:
    """Generates a deterministic MD5 hash cache key for query caching."""
    # Sort keys for deterministic JSON serialization
    serialized = json.dumps(params, default=_json_serial, sort_keys=True)
    hash_str = hashlib.md5(serialized.encode("utf-8")).hexdigest()
    return f"{prefix}:{hash_str}"
