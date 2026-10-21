"""Official FPL observations, kept separate from API-Sports metrics."""

from app.database import Base
from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint


class FPLMatchStat(Base):
    __tablename__ = "fpl_match_stats"
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False, index=True)
    fixture_id = Column(Integer, ForeignKey("fixtures.id"), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    minutes = Column(Integer, nullable=False)
    total_points = Column(Integer, nullable=False)
    stats = Column(JSON, nullable=False)
    observed_at = Column(DateTime(timezone=True), nullable=False)
    __table_args__ = (UniqueConstraint("player_id", "fixture_id", name="uq_fpl_player_fixture"),)


class FPLImport(Base):
    __tablename__ = "fpl_imports"
    id = Column(Integer, primary_key=True)
    season = Column(Integer, nullable=False)
    gameweek = Column(Integer, nullable=False)
    source_sha256 = Column(String(64), nullable=False)
    observed_at = Column(DateTime(timezone=True), nullable=False)
    player_count = Column(Integer, nullable=False)
    fixture_count = Column(Integer, nullable=False)
    __table_args__ = (UniqueConstraint("season", "gameweek", name="uq_fpl_import_season_gw"),)


class PlayerPriceSnapshot(Base):
    __tablename__ = "player_price_snapshots"
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    position = Column(String(20), nullable=False)
    price_tenths = Column(Integer, nullable=False)
    observed_at = Column(DateTime(timezone=True), nullable=False)
    source = Column(String(80), nullable=False)
    __table_args__ = (
        UniqueConstraint("player_id", "observed_at", name="uq_player_price_observation"),
    )
