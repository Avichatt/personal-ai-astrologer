"""Request ID middleware and context management for request tracing."""

from __future__ import annotations

import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-ID"
request_id_ctx_var: ContextVar[str] = ContextVar("request_id", default="")


def get_current_request_id() -> str:
    """Retrieve the current request ID from context var or generate a new one."""
    req_id = request_id_ctx_var.get()
    return req_id if req_id else str(uuid.uuid4())


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware that injects an X-Request-ID header into every request and response."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        incoming_id = request.headers.get(REQUEST_ID_HEADER)
        req_id = incoming_id if incoming_id else str(uuid.uuid4())
        token = request_id_ctx_var.set(req_id)
        try:
            response = await call_next(request)
            response.headers[REQUEST_ID_HEADER] = req_id
            return response
        finally:
            request_id_ctx_var.reset(token)
