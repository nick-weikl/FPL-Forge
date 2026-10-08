from collections import Counter
from app.services.fpl_price_service import FPL_SEASON
from app.database import SessionLocal
from app.models.player import Player


def validate_squad(owned_player_ids):
    db = SessionLocal()

    try:
        # Prevent duplicate player IDs
        if len(owned_player_ids) != len(set(owned_player_ids)):
            return {
                "valid": False,
                "errors": [
                    "Squad contains duplicate players"
                ]
            }

        # A full FPL squad must contain 15 players
        if len(owned_player_ids) != 15:
            return {
                "valid": False,
                "errors": [
                    "Squad must contain exactly 15 players"
                ]
            }

        players = (
            db.query(Player)
            .filter(
                Player.id.in_(owned_player_ids),
                Player.fpl_season == FPL_SEASON
            )
            .all()
        )

        errors = []

        # Make sure every supplied ID exists
        if len(players) != 15:
            found_ids = {
                player.id
                for player in players
            }

            missing_ids = [
                player_id
                for player_id in owned_player_ids
                if player_id not in found_ids
            ]

            errors.append(
                f"Player IDs not found: {missing_ids}"
            )

        position_counts = Counter(
            player.position
            for player in players
        )

        required_positions = {
            "Goalkeeper": 2,
            "Defender": 5,
            "Midfielder": 5,
            "Attacker": 3
        }

        for position, required_count in required_positions.items():
            actual_count = position_counts.get(position, 0)

            if actual_count != required_count:
                errors.append(
                    f"{position}: expected {required_count}, "
                    f"found {actual_count}"
                )

        team_counts = Counter(
            player.team_id
            for player in players
        )

        for team_id, count in team_counts.items():
            if count > 3:
                errors.append(
                    f"Team {team_id} has {count} players; "
                    "maximum allowed is 3"
                )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "player_count": len(players),
            "position_counts": dict(position_counts),
            "team_counts": dict(team_counts)
        }

    finally:
        db.close()