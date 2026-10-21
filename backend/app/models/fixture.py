from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.database import Base


class Fixture(Base):
    __tablename__ = "fixtures"

    id = Column(Integer, primary_key=True, index=True)

    external_api_id = Column(Integer, unique=True, nullable=False)

    fpl_fixture_id = Column(Integer, nullable=True)

    __table_args__ = (
        Index("uq_fixtures_fpl_season_id", "season", "fpl_fixture_id", unique=True),
        Index("uq_fixtures_season_pair", "season", "home_team_id", "away_team_id", unique=True),
    )

    gameweek = Column(Integer, nullable=True)

    season = Column(
        Integer,
        nullable=False,
        index=True
    )

    fixture_date = Column(DateTime, nullable=False)

    status = Column(String, nullable=True)

    home_team_id = Column(
        Integer,
        ForeignKey("teams.id"),
        nullable=False
    )

    away_team_id = Column(
        Integer,
        ForeignKey("teams.id"),
        nullable=False
    )

    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)

    home_team = relationship(
        "Team",
        foreign_keys=[home_team_id],
        back_populates="home_fixtures"
    )

    away_team = relationship(
        "Team",
        foreign_keys=[away_team_id],
        back_populates="away_fixtures"
    )

    player_stats = relationship(
        "PlayerMatchStat",
        back_populates="fixture"
    )