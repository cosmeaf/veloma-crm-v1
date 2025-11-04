from __future__ import annotations
from typing import Optional
from pathlib import Path
from django.conf import settings
from .service import StorageError

class LocalStorage:
    def __init__(self, *, base_dir: Optional[str] = None):
        # por padrão salva em BASE_DIR/var/storage
        root = Path(getattr(settings, "BASE_DIR", "."))  # BASE_DIR do settings
        self.base = Path(base_dir or (root / "var" / "storage"))
        self.base.mkdir(parents=True, exist_ok=True)

    def _dest(self, path: str) -> Path:
        path = path.lstrip("/")
        dest = self.base / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        return dest

    def put_file(self, path: str, content: bytes, *, content_type: Optional[str] = None) -> str:
        dest = self._dest(path)
        try:
            dest.write_bytes(content)
            return str(dest)
        except Exception as e:
            raise StorageError(f"Local put failed: {e}")

    def get_file(self, path: str) -> bytes:
        dest = self._dest(path)
        try:
            return dest.read_bytes()
        except Exception as e:
            raise StorageError(f"Local get failed: {e}")

    def delete_file(self, path: str) -> None:
        dest = self._dest(path)
        try:
            if dest.exists():
                dest.unlink()
        except Exception as e:
            raise StorageError(f"Local delete failed: {e}")
