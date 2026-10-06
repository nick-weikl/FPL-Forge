from fastapi import FastAPI
from sqlalchemy import text
from app.database import engine
from app.database import Base, engine
from app.models import Team, Player, Fixture, PlayerMatchStat
from app.services.football_api import get_premier_league_fixtures, get_premier_league_teams
from app.services.team_service import sync_premier_league_teams
from app.database import SessionLocal
from app.services.player_service import sync_premier_league_players
from app.routes.players import router as players_router
from app.routes.teams import router as teams_router
from app.services.fixture_service import sync_premier_league_fixtures
from app.routes.fixtures import router as fixtures_router
from app.routes.sync import router as sync_router
from app.routes.recommendations import router as recommendations_router
from app.routes.squads import router as squads_router
from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.include_router(players_router)
app.include_router(fixtures_router)
app.include_router(teams_router)
app.include_router(recommendations_router)
app.include_router(squads_router)
app.include_router(sync_router)


@app.get("/")
def root():
    return {"message": "FPL Forge API is running"}


@app.get("/db-test")
def test_database():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return {"database": result.scalar()}


@app.get("/api-test")
def api_test():
    return get_premier_league_teams()


# @app.post("/sync/teams")
# def sync_teams():
#     return sync_premier_league_teams()


# @app.get("/api/teams")
# def get_teams():

#     db = SessionLocal()

#     try:

#         teams = db.query(Team).all()

#         return teams

#     finally:

#         db.close()


# @app.post("/sync/players")
# def sync_players():
#     return sync_premier_league_players()


# @app.post("/sync/fixtures")
# def sync_fixtures():
#     return sync_premier_league_fixtures()


# @app.get("/api/fixtures")
# def get_fixtures():
#     return get_premier_league_fixtures()


# @app.get("/api/match-stats")
# def get_match_stats(fixture_id: int):
#     return get_match_stats(fixture_id)

