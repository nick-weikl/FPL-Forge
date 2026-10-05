from app.database import SessionLocal
from app.models.player import Player
from app.services.fixture_analytics_service import get_player_fixture_outlook
from app.services.player_analytics_service import (
    get_player_recent_form,
    get_player_summary
)


def normalize_metric(players, metric_name):
    if not players:
        return []

    metric_values = [
        player[metric_name]
        for player in players
    ]
    min_value = min(metric_values)
    max_value = max(metric_values)

    for player in players:
        value = player[metric_name]
        if max_value == min_value:
            normalized_value = 0.5
        else:
            normalized_value = (
                (value - min_value) / (max_value - min_value)
            )
        player[f"normalized_{metric_name}"] = normalized_value

    return players


def get_player_metrics(player_id, current_gameweek):
    db = SessionLocal()

    try:
        player = (
            db.query(Player)
            .filter(Player.id == player_id)
            .first()
        )

        if not player:
            return {
                "error": "Player not found"
            }

        summary = get_player_summary(player_id, current_gameweek)

        if "error" in summary:
            return summary

        if summary.get("total_minutes", 0) <= 0:
            return {
                "error": "Player has no usable match data"
            }

        recent_form = get_player_recent_form(
            player_id,
            current_gameweek,
            num_matches=5
        )

        fixture_outlook = get_player_fixture_outlook(
            player_id,
            current_gameweek,
            limit=5
        )

        return {
            "player_id": player_id,
            "position": player.position,
            "total_minutes": summary.get("total_minutes"),
            "goals_per_90": summary.get("goals_per_90"),
            "assists_per_90": summary.get("assists_per_90"),
            "shots_per_90": summary.get("shots_per_90"),
            "shots_on_target_per_90": summary.get("shots_on_target_per_90"),
            "average_rating": summary.get("average_rating"),    
            "recent_form": recent_form,
            "upcoming_fixtures": fixture_outlook
        }

    finally:
        db.close()


def get_all_player_metrics(current_gameweek, position=None):
    db = SessionLocal()

    try:
        query = db.query(Player)

        if position:
            query = query.filter(Player.position == position)

        players = query.all()

        player_metrics = []

        for player in players:
            metrics = get_player_metrics(
                player.id,
                current_gameweek
            )

            if (
                "error" not in metrics
                and metrics["total_minutes"] >= 90
            ):
                player_metrics.append(metrics)

        return player_metrics

    finally:
        db.close()


def get_forward_scores(current_gameweek):
    players = get_all_player_metrics(
        current_gameweek,
        position="Attacker"
    )

    players = normalize_metric(players, "goals_per_90")
    players = normalize_metric(players, "assists_per_90")
    players = normalize_metric(players, "shots_per_90")
    players = normalize_metric(players, "shots_on_target_per_90")

    for player in players:
        score = (
            player["normalized_goals_per_90"] * 0.35
            + player["normalized_assists_per_90"] * 0.15
            + player["normalized_shots_per_90"] * 0.25
            + player["normalized_shots_on_target_per_90"] * 0.25
        )

        player["performance_score"] = round(score * 10, 2)

    players.sort(key=lambda x: x["performance_score"], reverse=True)

    return players

