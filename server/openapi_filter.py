"""
OpenAPI Schema Filtering

Filters OpenAPI schema based on user role/scope to prevent API reconnaissance.
Only shows endpoints the user is actually allowed to call.
"""

from typing import Any

from api_exposure import get_allowed_tags_for_role
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from rbac.permissions import Role


def get_filtered_openapi(
    app: FastAPI,
    role: Role | None = None,
    title: str | None = None,
    version: str | None = None,
) -> dict[str, Any]:
    """
    Generate OpenAPI schema filtered by user role.

    Args:
        app: FastAPI application instance
        role: User's RBAC role (None for unauthenticated)
        title: Optional custom title for the schema
        version: Optional custom version for the schema

    Returns:
        Filtered OpenAPI schema dictionary
    """
    # Get the full OpenAPI schema
    if not app.openapi_schema:
        app.openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            openapi_version=app.openapi_version,
            description=app.description,
            routes=app.routes,
        )

    # Make a deep copy to avoid modifying the cached schema
    import copy

    schema = copy.deepcopy(app.openapi_schema)

    # Get allowed tags for this role
    allowed_tags = get_allowed_tags_for_role(role)

    # If no tags allowed (public/unauthenticated), return minimal schema
    if not allowed_tags:
        schema["paths"] = {}
        schema["components"] = {"schemas": {}}
        if title:
            schema["info"]["title"] = title
        if version:
            schema["info"]["version"] = version
        return schema

    # Filter paths based on allowed tags
    filtered_paths = {}
    for path, path_item in schema.get("paths", {}).items():
        # Check each operation (get, post, put, delete, etc.)
        filtered_operations = {}
        for method, operation in path_item.items():
            if method in ["get", "post", "put", "delete", "patch", "options", "head"]:
                # Check if operation has any allowed tags
                operation_tags = operation.get("tags", [])
                if any(tag in allowed_tags for tag in operation_tags):
                    filtered_operations[method] = operation

        # Only include path if it has at least one allowed operation
        if filtered_operations:
            # Preserve path-level parameters if they exist
            if "parameters" in path_item:
                filtered_operations["parameters"] = path_item["parameters"]
            filtered_paths[path] = filtered_operations

    schema["paths"] = filtered_paths

    # Filter tags list to only show used tags
    if "tags" in schema:
        used_tags = set()
        for path_item in filtered_paths.values():
            for operation in path_item.values():
                if isinstance(operation, dict) and "tags" in operation:
                    used_tags.update(operation["tags"])

        schema["tags"] = [tag_info for tag_info in schema["tags"] if tag_info.get("name") in used_tags]

    # Update title and version if provided
    if title:
        schema["info"]["title"] = title
    if version:
        schema["info"]["version"] = version

    # Add security notice to description
    role_name = role.name if role else "unauthenticated"
    security_notice = (
        f"\n\n**Documentation Access Level:** {role_name}\n\n"
        "This documentation shows only the endpoints you are authorized to access. "
        "Additional endpoints may exist but are not visible to your current role."
    )

    if "description" in schema["info"]:
        schema["info"]["description"] += security_notice
    else:
        schema["info"]["description"] = security_notice.strip()

    return schema


def get_endpoint_count(schema: dict[str, Any]) -> int:
    """
    Count the number of endpoints in an OpenAPI schema.

    Args:
        schema: OpenAPI schema dictionary

    Returns:
        Number of operation endpoints
    """
    count = 0
    for path_item in schema.get("paths", {}).values():
        for method in ["get", "post", "put", "delete", "patch", "options", "head"]:
            if method in path_item:
                count += 1
    return count
