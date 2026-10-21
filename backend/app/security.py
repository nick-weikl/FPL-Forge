import secrets

from fastapi import Header, HTTPException, Request


def require_admin(request: Request, x_admin_token: str = Header(default="")):
    settings = request.app.state.settings
    if not settings.admin_sync:
        raise HTTPException(404, "Not found")
    if not x_admin_token or not secrets.compare_digest(
        x_admin_token.encode("utf-8"), settings.admin_token.encode("utf-8")
    ):
        raise HTTPException(403, "Admin access required")
