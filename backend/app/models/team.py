from sqlalchemy import Column, Integer, String, Index
from sqlalchemy.orm import relationship

from app.database import Base


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)

    # ID supplied by the external football API
    external_api_id = Column(Integer, nullable=True)

    name = Column(String, nullable=False)
    short_name = Column(String, nullable=True)

    fpl_team_id = Column(Integer, nullable=True)
    fpl_season = Column(String(7), nullable=True)

    __table_args__ = (
        Index("uq_teams_api_season_id", "fpl_season", "external_api_id", unique=True),
        Index("uq_teams_name_season", "fpl_season", "name", unique=True),
        Index(
            "uq_teams_fpl_season_id",
            "fpl_season",
            "fpl_team_id",
            unique=True
        ),
    )

    # Relationships
    players = relationship("Player", back_populates="team")

    home_fixtures = relationship(
        "Fixture",
        foreign_keys="Fixture.home_team_id",
        back_populates="home_team"
    )

    away_fixtures = relationship(
        "Fixture",
        foreign_keys="Fixture.away_team_id",
        back_populates="away_team"
    )