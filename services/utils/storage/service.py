from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Optional
from django.conf import settings

class StorageError(Exception): ...

class _Backend(Protocol):
    def put_file(self, path: str, content: bytes, *, content_type: Optional[str] = None) -> str: ...
    def get_file(self, path: str) -> bytes: ...
    def delete_file(self, path: str) -> None: ...

@dataclass
class StorageService:
    """
    Fachada fina para storage. Decide backend via settings.STORAGE_BACKEND:
      - "minio"  -> MinIO/S3
      - "local"  -> filesystem local (dev)
    """
    def __post_init__(self):
        backend_name = getattr(settings, "STORAGE_BACKEND", "local").lower()
        if backend_name == "minio":
            from .minio_storage import MinioStorage
            self.backend: _Backend = MinioStorage(
                endpoint=getattr(settings, "MINIO_ENDPOINT", "127.0.0.1:9000"),
                access_key=getattr(settings, "MINIO_ACCESS_KEY", ""),
                secret_key=getattr(settings, "MINIO_SECRET_KEY", ""),
                bucket=getattr(settings, "MINIO_BUCKET", "veloma"),
                secure=bool(getattr(settings, "MINIO_SECURE", False)),
                region=getattr(settings, "MINIO_REGION", None),
                prefix=getattr(settings, "MINIO_PREFIX", "").strip("/"),
            )
        else:
            from .local_storage import LocalStorage
            self.backend = LocalStorage(
                base_dir=getattr(settings, "LOCAL_STORAGE_DIR", None)
            )

    # API pública
    def put_file(self, path: str, content: bytes, *, content_type: Optional[str] = None) -> str:
        return self.backend.put_file(path, content, content_type=content_type)

    def get_file(self, path: str) -> bytes:
        return self.backend.get_file(path)

    def delete_file(self, path: str) -> None:
        return self.backend.delete_file(path)
