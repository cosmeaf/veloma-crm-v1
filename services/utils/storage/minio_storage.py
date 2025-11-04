from __future__ import annotations
from typing import Optional
from minio import Minio
from minio.error import S3Error
from .service import StorageError

class MinioStorage:
    def __init__(self, *, endpoint: str, access_key: str, secret_key: str,
                 bucket: str, secure: bool = False, region: Optional[str] = None,
                 prefix: str = ""):
        if not bucket:
            raise StorageError("MINIO_BUCKET não configurado.")
        self.bucket = bucket
        self.prefix = prefix
        self.client = Minio(
            endpoint, access_key=access_key, secret_key=secret_key, secure=secure, region=region
        )
        # não criamos bucket automaticamente aqui (você já criou). Se quiser, cheque:
        # if not self.client.bucket_exists(bucket): self.client.make_bucket(bucket)

    def _key(self, path: str) -> str:
        path = path.lstrip("/")
        if self.prefix:
            return f"{self.prefix}/{path}"
        return path

    def put_file(self, path: str, content: bytes, *, content_type: Optional[str] = None) -> str:
        import io
        key = self._key(path)
        try:
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=key,
                data=io.BytesIO(content),
                length=len(content),
                content_type=content_type or "application/octet-stream",
            )
            return key
        except S3Error as e:
            raise StorageError(f"MinIO put failed: {e}")

    def get_file(self, path: str) -> bytes:
        key = self._key(path)
        try:
            resp = self.client.get_object(self.bucket, key)
            data = resp.read()
            resp.close(); resp.release_conn()
            return data
        except S3Error as e:
            raise StorageError(f"MinIO get failed: {e}")

    def delete_file(self, path: str) -> None:
        key = self._key(path)
        try:
            self.client.remove_object(self.bucket, key)
        except S3Error as e:
            raise StorageError(f"MinIO delete failed: {e}")
