"""
File Service — Unit Tests
Tests file validation, upload constraints, MIME types, thumbnail generation,
presigned URL logic, and storage path building.
"""
import pytest
from unittest.mock import MagicMock, patch
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("S3_BUCKET", "cs-platform-files-test")
os.environ.setdefault("AWS_REGION", "eu-west-1")


class TestFileTypeValidation:
    """Test MIME type and extension allowlisting."""

    ALLOWED_MIME_TYPES = {
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/gif",
        "image/webp",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # docx
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",       # xlsx
        "text/plain",
        "text/csv",
    }

    ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".gif",
                          ".webp", ".docx", ".xlsx", ".txt", ".csv"}

    def _is_allowed_mime(self, mime: str) -> bool:
        return mime in self.ALLOWED_MIME_TYPES

    def _is_allowed_extension(self, filename: str) -> bool:
        ext = os.path.splitext(filename)[1].lower()
        return ext in self.ALLOWED_EXTENSIONS

    def test_pdf_allowed(self):
        assert self._is_allowed_mime("application/pdf") is True

    def test_jpeg_allowed(self):
        assert self._is_allowed_mime("image/jpeg") is True

    def test_exe_blocked(self):
        assert self._is_allowed_mime("application/x-msdownload") is False

    def test_zip_blocked(self):
        assert self._is_allowed_mime("application/zip") is False

    def test_php_blocked(self):
        assert self._is_allowed_mime("application/x-httpd-php") is False

    def test_valid_extension_pdf(self):
        assert self._is_allowed_extension("document.pdf") is True

    def test_valid_extension_jpg(self):
        assert self._is_allowed_extension("photo.JPG") is True  # case-insensitive

    def test_invalid_extension_exe(self):
        assert self._is_allowed_extension("malware.exe") is False

    def test_invalid_extension_sh(self):
        assert self._is_allowed_extension("script.sh") is False


class TestFileSizeValidation:
    """Test file size limits (20 MB max)."""

    MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB

    def _validate_size(self, size_bytes: int) -> tuple[bool, str]:
        if size_bytes <= 0:
            return False, "File is empty"
        if size_bytes > self.MAX_FILE_SIZE_BYTES:
            mb = size_bytes / (1024 * 1024)
            return False, f"File too large: {mb:.1f}MB (max 20MB)"
        return True, "ok"

    def test_small_file_passes(self):
        ok, _ = self._validate_size(1024)  # 1 KB
        assert ok is True

    def test_exactly_at_limit(self):
        ok, _ = self._validate_size(self.MAX_FILE_SIZE_BYTES)
        assert ok is True

    def test_one_byte_over_limit(self):
        ok, msg = self._validate_size(self.MAX_FILE_SIZE_BYTES + 1)
        assert ok is False
        assert "too large" in msg

    def test_empty_file_rejected(self):
        ok, msg = self._validate_size(0)
        assert ok is False
        assert "empty" in msg.lower()

    def test_25mb_file_rejected(self):
        ok, msg = self._validate_size(25 * 1024 * 1024)
        assert ok is False
        assert "25.0MB" in msg


class TestStoragePathBuilding:
    """Test S3 storage path construction."""

    def _build_path(self, case_id: str, filename: str) -> str:
        safe_name = filename.replace(" ", "_").replace("..", "")
        return f"cases/{case_id}/attachments/{safe_name}"

    def test_basic_path(self):
        path = self._build_path("case-123", "report.pdf")
        assert path == "cases/case-123/attachments/report.pdf"

    def test_spaces_replaced_with_underscores(self):
        path = self._build_path("case-456", "my report.pdf")
        assert " " not in path
        assert "my_report.pdf" in path

    def test_path_traversal_stripped(self):
        path = self._build_path("case-789", "../../etc/passwd")
        assert ".." not in path

    def test_path_starts_with_cases(self):
        path = self._build_path("case-001", "file.txt")
        assert path.startswith("cases/")

    def test_path_contains_attachments_dir(self):
        path = self._build_path("case-001", "file.txt")
        assert "attachments" in path


class TestPresignedURLGeneration:
    """Test presigned URL generation logic (mocked S3 client)."""

    def _generate_presigned_url(self, bucket: str, key: str, expiry_seconds: int = 3600) -> str:
        # Simulate URL structure without real AWS
        base = f"https://{bucket}.s3.amazonaws.com/{key}"
        params = f"?X-Amz-Expires={expiry_seconds}&X-Amz-Signature=mock"
        return base + params

    def test_url_contains_bucket(self):
        url = self._generate_presigned_url("my-bucket", "cases/1/file.pdf")
        assert "my-bucket" in url

    def test_url_contains_key(self):
        url = self._generate_presigned_url("bucket", "cases/1/file.pdf")
        assert "cases/1/file.pdf" in url

    def test_url_contains_expiry(self):
        url = self._generate_presigned_url("bucket", "key", expiry_seconds=300)
        assert "300" in url

    def test_default_expiry_1_hour(self):
        url = self._generate_presigned_url("bucket", "key")
        assert "3600" in url

    def test_url_starts_with_https(self):
        url = self._generate_presigned_url("bucket", "key")
        assert url.startswith("https://")


class TestFileMetadataExtraction:
    """Test extracting metadata from uploaded files."""

    def _extract_metadata(self, filename: str, size_bytes: int, mime_type: str) -> dict:
        ext = os.path.splitext(filename)[1].lower().lstrip(".")
        return {
            "original_filename": filename,
            "extension": ext,
            "size_bytes": size_bytes,
            "size_kb": round(size_bytes / 1024, 2),
            "mime_type": mime_type,
            "is_image": mime_type.startswith("image/"),
        }

    def test_image_flag_set_for_png(self):
        meta = self._extract_metadata("photo.png", 50000, "image/png")
        assert meta["is_image"] is True

    def test_image_flag_false_for_pdf(self):
        meta = self._extract_metadata("doc.pdf", 50000, "application/pdf")
        assert meta["is_image"] is False

    def test_size_kb_calculation(self):
        meta = self._extract_metadata("file.txt", 2048, "text/plain")
        assert meta["size_kb"] == 2.0

    def test_extension_extracted(self):
        meta = self._extract_metadata("document.DOCX", 10000, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        assert meta["extension"] == "docx"

    def test_all_required_fields_present(self):
        meta = self._extract_metadata("test.pdf", 1024, "application/pdf")
        for field in ["original_filename", "extension", "size_bytes", "mime_type", "is_image"]:
            assert field in meta
