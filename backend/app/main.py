import logging

from app.config import Settings
from app.database import get_db
from app.middleware import RequestGuard
from app.models import Fixture, Player
from app.routes.dashboard import router as dashboard_router
from app.routes.data_quality import router as data_quality_router
from app.routes.fixtures import router as fixtures_router
from app.routes.players import router as players_router
from app.routes.recommendations import router as recommendations_router
from app.routes.squads import router as squads_router
from app.routes.sync import router as sync_router
from app.routes.team_import import router as team_import_router
from app.routes.teams import router as teams_router
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger("fpl_forge")


def create_app(settings=None):
    settings = settings or Settings.from_env()
    application = FastAPI(
        title="FPL Forge API",
        debug=False,
        docs_url=None if settings.environment == "production" else "/docs",
        redoc_url=None,
        openapi_url=None if settings.environment == "production" else "/openapi.json",
    )
    application.state.settings = settings
    application.add_middleware(RequestGuard, requests_per_minute=settings.requests_per_minute)
    application.add_middleware(TrustedHostMiddleware, allowed_hosts=list(settings.allowed_hosts))
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.origins),
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    for router in [
        players_router,
        fixtures_router,
        teams_router,
        recommendations_router,
        squads_router,
        sync_router,
        data_quality_router,
        dashboard_router,
        team_import_router,
    ]:
        application.include_router(router)

    @application.exception_handler(Exception)
    async def unexpected_error(request: Request, error: Exception):
        request_id = getattr(request.state, "request_id", "unavailable")
        logger.error(
            "Unhandled API error request_id=%s",
            request_id,
            exc_info=(type(error), error, error.__traceback__),
        )
        return JSONResponse(
            {"detail": f"Something went wrong on the server. Try again. Reference: {request_id}"},
            500,
            headers={
                "X-Request-ID": request_id,
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
            },
        )

    @application.get("/health/live", include_in_schema=False)
    def live():
        return {"status": "alive"}

    @application.get("/health/ready", include_in_schema=False)
    def ready(db: Session = Depends(get_db)):
        try:
            db.execute(text("SELECT 1"))
            db.execute(select(Player.id).limit(1))
            db.execute(select(Fixture.id).limit(1))
        except Exception:
            logger.warning("Readiness check failed")
            return JSONResponse({"status": "unavailable"}, 503)
        return {"status": "ready"}

    @application.get("/", include_in_schema=False)
    def root():
        return {"message": "FPL Forge API is running"}

    return application


# Migrations and ingestion are explicit operator commands, never startup side effects.
app = create_app()
