"""Verification data models."""

import hashlib
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class VerifyVerdict(str, Enum):
    """Verification outcome."""

    PASS = "PASS"
    FAIL = "FAIL"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"


class PageCheckConfig(BaseModel):
    """Configuration for a single page check."""

    path: str
    name: str = ""
    expected_title: Optional[str] = None
    expected_elements: List[str] = Field(default_factory=list)
    max_load_ms: int = 30000


class ApiCheckConfig(BaseModel):
    """Configuration for a single API check."""

    path: str
    method: str = "GET"
    expected_status: int = 200
    expected_fields: List[str] = Field(default_factory=list)
    max_response_ms: int = 10000


class VerifyRequest(BaseModel):
    """Request to run a deployment verification."""

    target_url: str
    pages: Optional[List[PageCheckConfig]] = None
    api_checks: Optional[List[ApiCheckConfig]] = None
    viewport_width: int = 1920
    viewport_height: int = 1080
    max_retries: int = 2
    timeout_ms: int = 30000
    strict_console_errors: bool = False


class PageResult(BaseModel):
    """Result of a single page check."""

    path: str
    name: str
    status: str  # PASS, FAIL, TIMEOUT, ERROR
    load_time_ms: float = 0
    console_errors: int = 0
    console_error_messages: List[str] = Field(default_factory=list)
    elements_found: int = 0
    elements_expected: int = 0
    title_match: Optional[bool] = None
    screenshot_path: Optional[str] = None
    error: Optional[str] = None
    retries: int = 0


class ApiResult(BaseModel):
    """Result of a single API check."""

    path: str
    method: str
    status: str  # PASS, FAIL, TIMEOUT, ERROR
    response_status: Optional[int] = None
    response_time_ms: float = 0
    fields_found: List[str] = Field(default_factory=list)
    fields_missing: List[str] = Field(default_factory=list)
    error: Optional[str] = None
    retries: int = 0


class ProofManifest(BaseModel):
    """Checksummed proof of verification execution."""

    manifest_id: str
    execution_id: str
    timestamp: str
    target_url: str
    verdict: VerifyVerdict
    score: int
    duration_ms: float
    artifact_hashes: Dict[str, str] = Field(default_factory=dict)
    combined_hash: str = ""
    governance_decisions: int = 0
    all_permitted: bool = True


class VerifyRun(BaseModel):
    """Complete verification run record."""

    id: str
    timestamp: str
    target_url: str
    verdict: VerifyVerdict
    score: int
    duration_ms: float
    pages: List[PageResult] = Field(default_factory=list)
    api_results: List[ApiResult] = Field(default_factory=list)
    total_console_errors: int = 0
    proof_manifest: Optional[ProofManifest] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    governance_decisions: int = 0
    retries_total: int = 0
    error: Optional[str] = None
