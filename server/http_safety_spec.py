"""
HTTP Safety Compliance Specification
Ensures all endpoints follow HTTP protocol standards to prevent client hangs
"""

import json
import logging
from typing import Any, Dict, List

from fastapi import Response
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class HTTPSafetySpec:
    """
    Specification for HTTP Safety Compliance
    Prevents common issues that cause client hangs or protocol violations
    """

    SAFETY_RULES = {
        "content_length_accuracy": {
            "description": "Content-Length header must match actual response body length",
            "severity": "critical",
            "fixes": [
                "Recalculate Content-Length",
                "Use chunked encoding",
                "Remove Content-Length header",
            ],
        },
        "response_completeness": {
            "description": "Response body must be complete and not truncated",
            "severity": "critical",
            "fixes": [
                "Ensure full response generation",
                "Add response validation",
                "Use streaming carefully",
            ],
        },
        "json_serialization": {
            "description": "JSON responses must be properly serialized",
            "severity": "high",
            "fixes": [
                "Validate JSON before sending",
                "Handle UUID/datetime serialization",
                "Use safe serializers",
            ],
        },
        "async_safety": {
            "description": "Async endpoints must not block on synchronous operations",
            "severity": "high",
            "fixes": [
                "Use async database calls",
                "Avoid blocking I/O",
                "Proper async/await usage",
            ],
        },
        "exception_handling": {
            "description": "All exceptions must be caught and return proper HTTP responses",
            "severity": "medium",
            "fixes": [
                "Global exception handlers",
                "Endpoint-level try/catch",
                "Safe error responses",
            ],
        },
    }

    @classmethod
    def validate_response(
        cls, response: Response, endpoint_path: str
    ) -> Dict[str, Any]:
        """
        Validate a response against HTTP safety rules
        """
        violations = []

        # Check Content-Length accuracy
        if hasattr(response, "body") and "content-length" in response.headers:
            declared_length = int(response.headers["content-length"])
            actual_length = len(response.body) if response.body else 0

            if declared_length != actual_length:
                violations.append(
                    {
                        "rule": "content_length_accuracy",
                        "severity": "critical",
                        "message": f"Content-Length mismatch: declared={declared_length}, actual={actual_length}",
                        "endpoint": endpoint_path,
                    }
                )

        # Check JSON serialization for JSON responses
        if (
            hasattr(response, "media_type")
            and response.media_type == "application/json"
        ):
            try:
                if hasattr(response, "body") and response.body:
                    json.loads(response.body.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                violations.append(
                    {
                        "rule": "json_serialization",
                        "severity": "high",
                        "message": f"Invalid JSON response: {str(e)}",
                        "endpoint": endpoint_path,
                    }
                )

        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "endpoint": endpoint_path,
        }

    @classmethod
    def create_safe_response(cls, content: Any, status_code: int = 200) -> JSONResponse:
        """
        Create a guaranteed safe HTTP response
        """
        try:
            # Ensure content is JSON serializable
            if hasattr(content, "__dict__"):
                # Convert objects to dict
                content = content.__dict__

            # Handle common non-serializable types
            safe_content = cls._make_json_safe(content)

            # Create response with explicit Content-Length
            json_str = json.dumps(safe_content, ensure_ascii=False, default=str)
            json_bytes = json_str.encode("utf-8")

            return JSONResponse(
                content=safe_content,
                status_code=status_code,
                headers={
                    "content-length": str(len(json_bytes)),
                    "content-type": "application/json; charset=utf-8",
                },
            )

        except Exception as e:
            logger.error(f"Failed to create safe response: {e}")
            # Ultimate fallback
            error_content = {"error": "Response generation failed", "detail": str(e)}
            error_json = json.dumps(error_content)
            error_bytes = error_json.encode("utf-8")

            return JSONResponse(
                content=error_content,
                status_code=500,
                headers={
                    "content-length": str(len(error_bytes)),
                    "content-type": "application/json; charset=utf-8",
                },
            )

    @classmethod
    def _make_json_safe(cls, obj: Any) -> Any:
        """
        Recursively make an object JSON serializable
        """
        if obj is None:
            return None
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, dict):
            return {key: cls._make_json_safe(value) for key, value in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [cls._make_json_safe(item) for item in obj]
        else:
            # Convert to string for non-serializable types
            return str(obj)


class SafeEndpointDecorator:
    """
    Decorator to make endpoints HTTP-safe
    """

    @staticmethod
    def safe_endpoint(func):
        """
        Decorator that wraps endpoint functions with safety checks
        """

        async def wrapper(*args, **kwargs):
            try:
                # Call the original function
                result = (
                    await func(*args, **kwargs)
                    if hasattr(func, "__code__") and func.__code__.co_flags & 0x80
                    else func(*args, **kwargs)
                )

                # Ensure result is a proper Response
                if not isinstance(result, Response):
                    # Convert to safe JSON response
                    return HTTPSafetySpec.create_safe_response(result)

                return result

            except Exception as e:
                logger.error(
                    f"Safe endpoint wrapper caught exception in {func.__name__}: {e}"
                )
                return HTTPSafetySpec.create_safe_response(
                    {"error": "Internal server error", "detail": str(e)},
                    status_code=500,
                )

        return wrapper


# Export the decorator for easy use
safe_endpoint = SafeEndpointDecorator.safe_endpoint
