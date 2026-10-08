from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Fixture(Base):
    __tablename__ = "fixtures"

    id = Column(Integer, primary_key=True, index=True)

    external_api_id = Column(Integer, unique=True, nullable=False)

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