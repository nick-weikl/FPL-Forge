from sqlalchemy import Column, Integer, String, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.database import Base


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)

    external_api_id = Column(Integer, unique=True, nullable=True)

    name = Column(String, nullable=False)
    position = Column(String, nullable=True)

    team_id = Column(
        Integer,
        ForeignKey("teams.id"),
        nullable=False
    )

    price_tenths = Column(Integer, nullable=True)

    fpl_player_id = Column(
        Integer,
        nullable=True
        )

    fpl_position = Column(
        String(20),
        nullable=True
    )

    fpl_season = Column(
        String(7),
        nullable=True
    )

    fpl_price_gameweek = Column(
        Integer,
        nullable=True
    )

    __table_args__ = (
        Index(
            "uq_players_fpl_season_id",
            "fpl_season",
            "fpl_player_id",
            unique=True
        ),
    )

    # Relationship back to Team
    team = relationship("Team", back_populates="players")

    # One player can have stats from many matches
    match_stats = relationship(
        "PlayerMatchStat",
        back_populates="player"
    )