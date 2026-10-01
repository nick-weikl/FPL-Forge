from fastapi import FastAPI
from sqlalchemy import text
from app.database import engine
from app.database import Base, engine
from app.models import Team, Player, Fixture, PlayerMatchStat
from app.services.football_api import get_premier_league_teams
from app.services.team_service import sync_premier_league_teams
from app.database import SessionLocal
from app.services.player_service import sync_premier_league_players
from app.routes.players import router as players_router
from app.routes.teams import router as teams_router

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(players_router)
app.include_router(teams_router)


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


@app.post("/sync/teams")
def sync_teams():
    return sync_premier_league_teams()


@app.get("/api/teams")
def get_teams():

    db = SessionLocal()

    try:

        teams = db.query(Team).all()

        return teams

    finally:

        db.close()


@app.post("/sync/players")
def sync_players():
    return sync_premier_league_players()