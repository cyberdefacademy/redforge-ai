import uuid
import re
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9\-_]{1,64}$")


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        raw = request.headers.get("X-Request-ID", "")
        # Trust client value only if safe; otherwise mint a new UUID (prevents log injection).
        request_id = raw if _REQUEST_ID_RE.match(raw) else str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        response.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
        response.headers.setdefault("X-Permitted-Cross-Domain-Policy", "none")
        # HSTS is only meaningful behind TLS; harmless otherwise.
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response
