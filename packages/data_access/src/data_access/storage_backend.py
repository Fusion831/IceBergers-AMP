"""Storage backend protocol and local filesystem implementation."""
import os
from pathlib import Path
from typing import Protocol, Any, Optional
from core.config import settings
from core.logging import get_logger

logger = get_logger("data_access.storage")


class StorageBackend(Protocol):
    """Abstract interface for local filesystem and object storage (S3/MinIO)."""
    def exists(self, path: str) -> bool: ...
    def get_absolute_path(self, path: str) -> str: ...
    def read_bytes(self, path: str) -> bytes: ...
    def write_bytes(self, path: str, data: bytes) -> None: ...


class LocalFileSystemStorage:
    """Local filesystem storage implementation."""
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir or settings.DATA_DIR).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def exists(self, path: str) -> bool:
        full_path = (self.base_dir / path).resolve()
        return full_path.exists()

    def get_absolute_path(self, path: str) -> str:
        return str((self.base_dir / path).resolve())

    def read_bytes(self, path: str) -> bytes:
        full_path = (self.base_dir / path).resolve()
        with open(full_path, "rb") as f:
            return f.read()

    def write_bytes(self, path: str, data: bytes) -> None:
        full_path = (self.base_dir / path).resolve()
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(data)


default_storage = LocalFileSystemStorage()
