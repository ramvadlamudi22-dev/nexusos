"""Cloudflare R2 storage — evidence artifact persistence.

Stores screenshots, traces, videos, and evidence bundles in R2.
Falls back to local filesystem when R2 credentials are not configured.
"""

import hashlib
import os
from pathlib import Path
from typing import Optional


class R2Storage:
    """Object storage for evidence artifacts.

    Uses Cloudflare R2 (S3-compatible) in production,
    local filesystem in development.
    """

    def __init__(self):
        self._account_id = os.environ.get("R2_ACCOUNT_ID")
        self._access_key = os.environ.get("R2_ACCESS_KEY_ID")
        self._secret_key = os.environ.get("R2_SECRET_ACCESS_KEY")
        self._bucket = os.environ.get("R2_BUCKET_NAME", "nexusos-evidence")
        self._endpoint = os.environ.get("R2_ENDPOINT")
        self._local_dir = Path("artifacts/evidence")
        self._local_dir.mkdir(parents=True, exist_ok=True)

        self._client = None
        if self._account_id and self._access_key and self._secret_key:
            self._init_r2()

    def _init_r2(self) -> None:
        """Initialize R2 client using boto3 S3-compatible interface."""
        try:
            import boto3

            self._client = boto3.client(
                "s3",
                endpoint_url=self._endpoint,
                aws_access_key_id=self._access_key,
                aws_secret_access_key=self._secret_key,
                region_name="auto",
            )
            self._mode = "r2"
        except ImportError:
            self._mode = "local"

    @property
    def mode(self) -> str:
        """Current storage mode."""
        if self._client:
            return "r2"
        return "local"

    def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Upload an artifact.

        Args:
            key: Storage key (path within bucket).
            data: File content bytes.
            content_type: MIME type.

        Returns:
            Storage URL or local path.
        """
        content_hash = hashlib.sha256(data).hexdigest()

        if self.mode == "r2":
            self._client.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
                Metadata={"content-hash": content_hash},
            )
            return f"r2://{self._bucket}/{key}"
        else:
            # Local storage
            local_path = self._local_dir / key
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_bytes(data)
            return str(local_path)

    def download(self, key: str) -> Optional[bytes]:
        """Download an artifact.

        Args:
            key: Storage key.

        Returns:
            File content bytes, or None if not found.
        """
        if self.mode == "r2":
            try:
                response = self._client.get_object(Bucket=self._bucket, Key=key)
                return response["Body"].read()
            except Exception:
                return None
        else:
            local_path = self._local_dir / key
            if local_path.exists():
                return local_path.read_bytes()
            return None

    def exists(self, key: str) -> bool:
        """Check if an artifact exists.

        Args:
            key: Storage key.

        Returns:
            True if the artifact exists.
        """
        if self.mode == "r2":
            try:
                self._client.head_object(Bucket=self._bucket, Key=key)
                return True
            except Exception:
                return False
        else:
            return (self._local_dir / key).exists()

    def list_keys(self, prefix: str = "") -> list:
        """List artifact keys with a prefix.

        Args:
            prefix: Key prefix to filter by.

        Returns:
            List of matching keys.
        """
        if self.mode == "r2":
            try:
                response = self._client.list_objects_v2(
                    Bucket=self._bucket, Prefix=prefix
                )
                return [obj["Key"] for obj in response.get("Contents", [])]
            except Exception:
                return []
        else:
            base = self._local_dir / prefix
            if not base.exists():
                return []
            return [
                str(p.relative_to(self._local_dir))
                for p in self._local_dir.rglob("*")
                if p.is_file() and str(p.relative_to(self._local_dir)).startswith(prefix)
            ]

    def get_url(self, key: str) -> str:
        """Get a public URL for an artifact.

        Args:
            key: Storage key.

        Returns:
            Public URL or local path.
        """
        if self.mode == "r2":
            return f"https://{self._bucket}.{self._account_id}.r2.cloudflarestorage.com/{key}"
        return str(self._local_dir / key)
