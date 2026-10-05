from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)

    external_api_id = Column(Integer, unique=True, nullable=False)

    name = Column(String, nullable=False)
    position = Column(String, nullable=True)

    team_id = Column(
        Integer,
        ForeignKey("teams.id"),
        nullable=False
    )

    price_tenths = Column(Integer, nullable=True)

    # Relationship back to Team
    team = relationship("Team", back_populates="players")

    # One player can have stats from many matches
    match_stats = relationship(
        "PlayerMatchStat",
        back_populates="player"
    )