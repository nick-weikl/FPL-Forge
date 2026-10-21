"""Bounded per-process API guard. Enforce global limits at the deployment edge too."""

from collections import OrderedDict, deque
from threading import Lock
from time import monotonic
from uuid import uuid4

from starlette.responses import JSONResponse


class RequestGuard:
    def __init__(self, app, requests_per_minute=120, max_body_bytes=65536):
        self.app = app
        self.limit = requests_per_minute
        self.max_body = max_body_bytes
        self.clients = OrderedDict()
        self.lock = Lock()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        request_id = uuid4().hex
        scope.setdefault("state", {})["request_id"] = request_id

        async def protected_send(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers += [
                    (b"x-content-type-options", b"nosniff"),
                    (b"referrer-policy", b"no-referrer"),
                    (b"x-request-id", request_id.encode()),
                    (b"cache-control", b"no-store"),
                ]
                message = {**message, "headers": headers}
            await send(message)

        if scope["path"].startswith("/api/"):
            client = (scope.get("client") or ("unknown", 0))[0]
            now = monotonic()
            with self.lock:
                timestamps = self.clients.pop(client, deque())
                while timestamps and timestamps[0] <= now - 60:
                    timestamps.popleft()
                allowed = len(timestamps) < self.limit
                if allowed:
                    timestamps.append(now)
                self.clients[client] = timestamps
                while len(self.clients) > 10000:
                    self.clients.popitem(last=False)
            if not allowed:
                return await JSONResponse(
                    {"detail": "Too many requests. Please wait a minute and try again."},
                    429,
                    headers={"Retry-After": "60"},
                )(scope, receive, protected_send)
        headers = dict(scope.get("headers", []))
        try:
            length = int(headers.get(b"content-length", b"0"))
        except ValueError:
            return await JSONResponse({"detail": "Invalid request length"}, 400)(
                scope, receive, protected_send
            )
        if length < 0 or length > self.max_body:
            return await JSONResponse({"detail": "Request is too large"}, 413)(
                scope, receive, protected_send
            )
        chunks, size = [], 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            size += len(chunk)
            if size > self.max_body:
                return await JSONResponse({"detail": "Request is too large"}, 413)(
                    scope, receive, protected_send
                )
            chunks.append(chunk)
            if not message.get("more_body", False):
                break
        buffered = False

        async def replay():
            nonlocal buffered
            if not buffered:
                buffered = True
                return {"type": "http.request", "body": b"".join(chunks), "more_body": False}
            return await receive()

        await self.app(scope, replay, protected_send)
