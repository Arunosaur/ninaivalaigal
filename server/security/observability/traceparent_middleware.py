from starlette.middleware.base import BaseHTTPMiddleware
import uuid

class TraceparentHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        trace_id = uuid.uuid4().hex
        request.state.trace_id = trace_id
        response = await call_next(request)
        response.headers['traceparent'] = f"00-{trace_id}-00"
        return response
