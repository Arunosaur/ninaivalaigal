from __future__ import annotations

ALLOWED_ROUTES = {
    "/contexts/{id}/memories",
    "/memories/{id}",
}

def normalize_route_template(raw_path: str, template: str | None) -> str:
    return template or raw_path.split("?",1)[0]

def validate_metric_labels(labels: dict[str, str]) -> None:
    route = labels.get("route") or ""
    if route and route not in ALLOWED_ROUTES:
        raise ValueError("route label must be a known template, not a concrete path")
    reason = labels.get("reason")
    if reason and reason not in {"engine_error","regex_fallback","policy_denied"}:
        raise ValueError("invalid reason label")
