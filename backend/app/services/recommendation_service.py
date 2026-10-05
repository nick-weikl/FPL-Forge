from app.database import SessionLocal
from app.models.player import Player
from app.services.player_scoring_service import (
    get_ranked_players_by_position
)
from app.services.squad_service import validate_squad
from sqlalchemy.orm import joinedload


def build_transfer_result(
    player,
    ranked_players,
    owned_player_ids,
    team_counts,
    bank_tenths=0,
    limit=5
):
    """
    Builds transfer recommendations for one outgoing player
    using rankings that have already been calculated.
    """

    current_player_price = player.price_tenths

    if current_player_price is None:
        return {
            "error": "Current player does not have price data"
        }

    current_player_score = None

    for ranked_player in ranked_players:
        if ranked_player["player_id"] == player.id:
            current_player_score = ranked_player["overall_score"]
            break

    if current_player_score is None:
        return {
            "error": "Current player does not have a valid score"
        }

    available_budget = (
        current_player_price + bank_tenths
    )

    owned_player_ids_set = set(owned_player_ids)

    candidates = []

    for candidate in ranked_players:

        candidate_id = candidate["player_id"]

        # Cannot transfer a player to themselves
        if candidate_id == player.id:
            continue

        # Cannot recommend somebody already owned
        if candidate_id in owned_player_ids_set:
            continue

        candidate_price = candidate.get("price_tenths")
        candidate_team_id = candidate.get("team_id")

        if (
            candidate_price is None
            or candidate_team_id is None
        ):
            continue

        # Budget check
        if candidate_price > available_budget:
            continue

        # Calculate how many players from this club
        # remain AFTER selling the outgoing player.
        existing_team_count = team_counts.get(
            candidate_team_id,
            0
        )

        if candidate_team_id == player.team_id:
            existing_team_count -= 1

        # Incoming player would create a fourth player
        if existing_team_count >= 3:
            continue

        score_gain = round(
            candidate["overall_score"]
            - current_player_score,
            2
        )

        # We only care about actual upgrades
        if score_gain <= 0:
            continue

        candidate_data = candidate.copy()

        candidate_data["score_gain"] = score_gain

        candidate_data["recommendation_strength"] = (
            get_recommendation_strength(
                score_gain
            )
        )

        candidates.append(candidate_data)

    candidates.sort(
        key=lambda candidate: candidate["score_gain"],
        reverse=True
    )

    return {
        "current_player_id": player.id,
        "current_player_score": current_player_score,
        "current_player_price_tenths":
            current_player_price,
        "bank_tenths": bank_tenths,
        "available_budget_tenths":
            available_budget,
        "position": player.position,
        "upgrade_found": len(candidates) > 0,
        "candidates": candidates[:limit]
    }


def get_transfer_candidates(
    current_player_id,
    current_gameweek,
    owned_player_ids,
    bank_tenths=0,
    limit=5
):
    squad_validation = validate_squad(
        owned_player_ids
    )

    if not squad_validation["valid"]:
        return {
            "error": "Invalid squad",
            "validation": squad_validation
        }

    if current_player_id not in owned_player_ids:
        return {
            "error": "Current player is not in the owned squad"
        }

    db = SessionLocal()

    try:
        player = (
            db.query(Player)
            .filter(
                Player.id == current_player_id
            )
            .first()
        )

        if not player:
            return {
                "error": "Player not found"
            }

        # Only calculate this player's positional
        # rankings once.
        ranked_players = (
            get_ranked_players_by_position(
                player.position,
                current_gameweek
            )
        )

        if (
            isinstance(ranked_players, dict)
            and "error" in ranked_players
        ):
            return ranked_players

        # Query the whole squad once.
        owned_players = (
            db.query(Player)
            .options(
                joinedload(Player.team)
            )
            .filter(
                Player.id.in_(owned_player_ids)
            )
            .all()
        )

        team_counts = {}

        for owned_player in owned_players:
            team_id = owned_player.team_id

            team_counts[team_id] = (
                team_counts.get(team_id, 0)
                + 1
            )

        return build_transfer_result(
            player=player,
            ranked_players=ranked_players,
            owned_player_ids=owned_player_ids,
            team_counts=team_counts,
            bank_tenths=bank_tenths,
            limit=limit
        )

    finally:
        db.close()


def get_best_squad_transfer(
    current_gameweek,
    owned_player_ids,
    bank_tenths=0
):
    # Validate once for the entire optimization.
    squad_validation = validate_squad(
        owned_player_ids
    )

    if not squad_validation["valid"]:
        return {
            "error": "Invalid squad",
            "validation": squad_validation
        }

    db = SessionLocal()

    try:
        # Load all 15 players with one query.
        owned_players = (
            db.query(Player)
            .options(
                joinedload(Player.team)
            )
            .filter(
                Player.id.in_(owned_player_ids)
            )
            .all()
        )

        owned_players_by_id = {
            player.id: player
            for player in owned_players
        }

        team_counts = {}

        for player in owned_players:
            team_id = player.team_id

            team_counts[team_id] = (
                team_counts.get(team_id, 0)
                + 1
            )

        # This is the major performance improvement:
        # calculate each position ranking ONCE.
        rankings_by_position = {
            "Goalkeeper":
                get_ranked_players_by_position(
                    "Goalkeeper",
                    current_gameweek
                ),

            "Defender":
                get_ranked_players_by_position(
                    "Defender",
                    current_gameweek
                ),

            "Midfielder":
                get_ranked_players_by_position(
                    "Midfielder",
                    current_gameweek
                ),

            "Attacker":
                get_ranked_players_by_position(
                    "Attacker",
                    current_gameweek
                )
        }

        # Catch scoring errors before processing
        # individual squad members.
        for position, rankings in (
            rankings_by_position.items()
        ):
            if (
                isinstance(rankings, dict)
                and "error" in rankings
            ):
                return {
                    "error":
                        f"Could not rank {position}s",
                    "details": rankings
                }

        transfer_options = []
        skipped_players = []

        for player_id in owned_player_ids:

            player = owned_players_by_id.get(
                player_id
            )

            if not player:
                skipped_players.append({
                    "player_id": player_id,
                    "reason": "Player not found"
                })
                continue

            ranked_players = (
                rankings_by_position.get(
                    player.position
                )
            )

            if ranked_players is None:
                skipped_players.append({
                    "player_id": player_id,
                    "reason":
                        "Unsupported player position"
                })
                continue

            result = build_transfer_result(
                player=player,
                ranked_players=ranked_players,
                owned_player_ids=owned_player_ids,
                team_counts=team_counts,
                bank_tenths=bank_tenths,
                limit=1
            )

            if (
                isinstance(result, dict)
                and "error" in result
            ):
                skipped_players.append({
                    "player_id": player_id,
                    "reason": result["error"]
                })
                continue

            if not result["upgrade_found"]:
                continue

            if not result["candidates"]:
                continue

            best_candidate = (
                result["candidates"][0]
            )

            transfer_options.append({
                "player_out": {
                    "player_id": player.id,
                    "name": player.name,
                    "team_id": player.team_id,
                    "team_name": (
                        player.team.name
                        if player.team
                        else None
                    ),
                    "position": result["position"],
                    "score": result["current_player_score"],
                    "price_tenths":
                        result["current_player_price_tenths"]
                },

                "player_in": {
                    "player_id":
                        best_candidate["player_id"],
                    "name":
                        best_candidate.get("name"),
                    "team_id":
                        best_candidate.get("team_id"),
                    "team_name":
                        best_candidate.get("team_name"),
                    "position":
                        best_candidate.get("position"),
                    "score":
                        best_candidate["overall_score"],
                    "price_tenths":
                        best_candidate.get("price_tenths")
                },

                "score_gain":
                    best_candidate["score_gain"],

                "recommendation_strength":
                    best_candidate[
                        "recommendation_strength"
                    ],

                "available_budget_tenths":
                    result["available_budget_tenths"],

                "remaining_bank_tenths":
                    (
                        result["available_budget_tenths"]
                        - best_candidate["price_tenths"]
                    )
            })

        transfer_options.sort(
            key=lambda transfer:
                transfer["score_gain"],
            reverse=True
        )

        if not transfer_options:
            return {
                "upgrade_found": False,
                "best_transfer": None,
                "alternatives": [],
                "skipped_players":
                    skipped_players
            }

        best_transfer = transfer_options[0]

        alternatives = []

        used_player_in_ids = {
            best_transfer["player_in"]["player_id"]
        }

        for transfer in transfer_options[1:]:
            incoming_player_id = (
                transfer["player_in"]["player_id"]
            )

            if incoming_player_id in used_player_in_ids:
                continue

            alternatives.append(transfer)

            used_player_in_ids.add(
                incoming_player_id
            )

            if len(alternatives) >= 4:
                break

        return {
            "upgrade_found": True,
            "best_transfer": best_transfer,
            "alternatives": alternatives,
            "skipped_players": skipped_players
        }

    finally:
        db.close()


def get_recommendation_strength(
    score_gain
):
    if score_gain <= 0:
        return "none"

    elif score_gain >= 2.0:
        return "strong"

    elif score_gain >= 1.0:
        return "moderate"

    else:
        return "slight"