from sqlalchemy import Column, Integer, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class PlayerMatchStat(Base):
    __tablename__ = "player_match_stats"

    id = Column(Integer, primary_key=True, index=True)

    player_id = Column(
        Integer,
        ForeignKey("players.id"),
        nullable=False
    )

    fixture_id = Column(
        Integer,
        ForeignKey("fixtures.id"),
        nullable=False
    )

    minutes = Column(Integer, default=0)

    goals = Column(Integer, default=0)
    assists = Column(Integer, default=0)

    shots = Column(Integer, default=0)
    shots_on_target = Column(Integer, default=0)

    key_passes = Column(Integer, default=0)

    tackles = Column(Integer, default=0)
    interceptions = Column(Integer, default=0)

    yellow_cards = Column(Integer, default=0)
    red_cards = Column(Integer, default=0)

    rating = Column(Float, nullable=True)

    player = relationship(
        "Player",
        back_populates="match_stats"
    )

    fixture = relationship(
        "Fixture",
        back_populates="player_stats"
    )

    __table_args__ = (
        UniqueConstraint(
            "player_id",
            "fixture_id",
            name="uq_player_fixture"
        ),
    )