"""Verification workflow templates — reusable configurations for common scenarios."""

from typing import Dict, List

from backend.verify.models import ApiCheckConfig, PageCheckConfig, VerifyRequest


# Built-in templates
TEMPLATES: Dict[str, dict] = {
    "smoke-test": {
        "name": "Smoke Test",
        "description": "Quick check that the homepage loads and a health endpoint responds.",
        "pages": [{"path": "/", "name": "Homepage"}],
        "api_checks": [{"path": "/api/health", "expected_status": 200}],
    },
    "full-site": {
        "name": "Full Site Verification",
        "description": "Checks homepage, common pages, and API health.",
        "pages": [
            {"path": "/", "name": "Homepage"},
            {"path": "/about", "name": "About"},
            {"path": "/login", "name": "Login"},
            {"path": "/dashboard", "name": "Dashboard"},
        ],
        "api_checks": [
            {"path": "/api/health", "expected_status": 200},
            {"path": "/api/status", "expected_status": 200},
        ],
    },
    "api-only": {
        "name": "API Verification",
        "description": "Validates API endpoints only, no page rendering.",
        "pages": [],
        "api_checks": [
            {"path": "/api/health", "expected_status": 200},
            {"path": "/api/status", "expected_status": 200},
        ],
    },
    "spa-check": {
        "name": "SPA Verification",
        "description": "Checks a single-page application loads correctly.",
        "pages": [
            {"path": "/", "name": "App Shell"},
            {"path": "/dashboard", "name": "Dashboard Route"},
            {"path": "/settings", "name": "Settings Route"},
        ],
        "api_checks": [],
    },
    "deployment-gate": {
        "name": "Deployment Gate",
        "description": "Comprehensive check suitable for CI/CD pipeline gates.",
        "pages": [
            {"path": "/", "name": "Homepage"},
            {"path": "/login", "name": "Login"},
        ],
        "api_checks": [
            {"path": "/api/health", "expected_status": 200, "expected_fields": ["status"]},
        ],
        "strict_console_errors": True,
    },
}


def get_template(template_id: str) -> dict:
    """Get a template by ID.

    Args:
        template_id: Template identifier.

    Returns:
        Template configuration dict.

    Raises:
        KeyError: If template not found.
    """
    if template_id not in TEMPLATES:
        raise KeyError(f"Template not found: {template_id}")
    return TEMPLATES[template_id]


def list_templates() -> List[dict]:
    """List all available templates."""
    return [
        {"id": tid, "name": t["name"], "description": t["description"]}
        for tid, t in TEMPLATES.items()
    ]


def build_request_from_template(
    template_id: str, target_url: str, **overrides
) -> VerifyRequest:
    """Build a VerifyRequest from a template.

    Args:
        template_id: Template to use.
        target_url: Target URL to verify.
        **overrides: Override any template fields.

    Returns:
        Configured VerifyRequest.
    """
    template = get_template(template_id)

    pages = [PageCheckConfig(**p) for p in template.get("pages", [])]
    api_checks = [ApiCheckConfig(**a) for a in template.get("api_checks", [])]

    return VerifyRequest(
        target_url=target_url,
        pages=overrides.get("pages", pages),
        api_checks=overrides.get("api_checks", api_checks),
        strict_console_errors=template.get("strict_console_errors", False),
        **{k: v for k, v in overrides.items() if k not in ("pages", "api_checks")},
    )
