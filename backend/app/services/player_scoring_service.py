from app.database import SessionLocal
from app.models.player import Player
from app.services.fixture_analytics_service import get_player_fixture_outlook
from app.services.player_analytics_service import (
    get_player_recent_form,
    get_player_summary,
    get_all_player_summaries
)
from sqlalchemy.orm import joinedload
from app.services.fixture_difficulty_service import (
    get_all_team_strengths
)


def normalize_metric(players, metric_name):
    if not players:
        return []

    metric_values = [
        player[metric_name]
        for player in players
        if player[metric_name] is not None
    ]

    if not metric_values:
        for player in players:
            player[f"normalized_{metric_name}"] = None
        return players

    min_value = min(metric_values)
    max_value = max(metric_values)

    for player in players:
        value = player[metric_name]

        if value is None:
            player[f"normalized_{metric_name}"] = None
            continue

        if max_value == min_value:
            normalized_value = 0.0 if max_value == 0 else 0.5
        else:
            normalized_value = (
                (value - min_value) / (max_value - min_value)
            )
        player[f"normalized_{metric_name}"] = normalized_value

    return players


def get_player_metrics(
    player_id,
    current_gameweek,
    db=None,
    player=None,
    team_strengths=None,
    fixture_outlook_cache=None,
    summary=None
):
    owns_db = db is None

    if owns_db:
        db = SessionLocal()

    try:
        if player is None:
            player = (
                db.query(Player)
                .options(
                    joinedload(Player.team)
                )
                .filter(Player.id == player_id)
                .first()
            )

        if not player:
            return {
                "error": "Player not found"
            }

        if summary is None:
            summary = get_player_summary(
                player_id,
                current_gameweek,
                db=db
            )

        if "error" in summary:
            return summary

        if summary.get(
            "total_minutes",
            0
        ) <= 0:
            return {
                "error":
                    "Player has no usable match data"
            }

        recent_form = get_player_recent_form(
            player_id,
            current_gameweek,
            num_matches=5,
            db=db
        )

        recent_form_summary = (
            summarize_recent_form(
                recent_form
            )
        )

        # Every player on the same club and in the
        # same position has the same fixture outlook.
        cache_key = (
            player.team_id,
            player.position
        )

        cached_outlook = None

        if fixture_outlook_cache is not None:
            cached_outlook = (
                fixture_outlook_cache.get(
                    cache_key
                )
            )

        if cached_outlook is None:
            raw_outlook = (
                get_player_fixture_outlook(
                    player_id=player_id,
                    current_gameweek=
                        current_gameweek,
                    limit=5,
                    db=db,
                    player=player,
                    team_strengths=
                        team_strengths
                )
            )

            if "error" in raw_outlook:
                return raw_outlook

            cached_outlook = {
                "average_fixture_difficulty":
                    raw_outlook[
                        "average_fixture_difficulty"
                    ],
                "fixtures":
                    raw_outlook["fixtures"]
            }

            if fixture_outlook_cache is not None:
                fixture_outlook_cache[
                    cache_key
                ] = cached_outlook

        fixture_outlook = {
            "player_id": player_id,
            "average_fixture_difficulty":
                cached_outlook[
                    "average_fixture_difficulty"
                ],
            "fixtures":
                cached_outlook["fixtures"]
        }

        return {
            "player_id": player_id,
            "position": player.position,
            "total_minutes":
                summary.get(
                    "total_minutes",
                    0
                ),
            "goals_per_90":
                summary.get(
                    "goals_per_90",
                    0
                ),
            "assists_per_90":
                summary.get(
                    "assists_per_90",
                    0
                ),
            "shots_per_90":
                summary.get(
                    "shots_per_90",
                    0
                ),
            "shots_on_target_per_90":
                summary.get(
                    "shots_on_target_per_90",
                    0
                ),
            "key_passes_per_90":
                summary.get(
                    "key_passes_per_90",
                    0
                ),
            "tackles_per_90":
                summary.get(
                    "tackles_per_90",
                    0
                ),
            "interceptions_per_90":
                summary.get(
                    "interceptions_per_90",
                    0
                ),
            "average_rating":
                summary.get(
                    "average_rating"
                ),
            "recent_goals":
                recent_form_summary[
                    "recent_goals"
                ],
            "recent_assists":
                recent_form_summary[
                    "recent_assists"
                ],
            "recent_minutes":
                recent_form_summary[
                    "recent_minutes"
                ],
            "average_recent_rating":
                recent_form_summary[
                    "average_recent_rating"
                ],
            "recent_form": recent_form,
            "upcoming_fixtures":
                fixture_outlook,
            "price_tenths":
                player.price_tenths,
            "team_id":
                player.team_id,
            "team_name":
                (
                    player.team.name
                    if player.team
                    else None
                )
        }

    finally:
        if owns_db:
            db.close()


def get_all_player_metrics(
    current_gameweek,
    position=None
):
    db = SessionLocal()

    try:
        query = (
            db.query(Player)
            .options(
                joinedload(Player.team)
            )
        )

        if position:
            query = query.filter(
                Player.position == position
            )

        players = query.all()

        player_ids = [
            player.id
            for player in players
        ]

        summaries_by_player_id = (
            get_all_player_summaries(
                current_gameweek=current_gameweek,
                player_ids=player_ids,
                db=db
            )
        )

        # Calculate league strength ONCE.
        team_strengths = (
            get_all_team_strengths(
                current_gameweek,
                db=db
            )
        )

        # Same team + same position = same
        # future fixture difficulty.
        fixture_outlook_cache = {}

        player_metrics = []

        for player in players:

            summary = (
                summaries_by_player_id.get(
                    player.id
                )
            )

            if not summary:
                continue

            metrics = get_player_metrics(
                player_id=player.id,
                current_gameweek=
                    current_gameweek,
                db=db,
                player=player,
                team_strengths=
                    team_strengths,
                fixture_outlook_cache=
                    fixture_outlook_cache,
                summary=summary
            )

            if (
                "error" not in metrics
                and metrics[
                    "total_minutes"
                ] >= 90
            ):
                player_metrics.append(
                    metrics
                )

        return player_metrics

    finally:
        db.close()


def calculate_fixture_score(average_fixture_difficulty):
    fixture_score = (
        (5 - average_fixture_difficulty) / 4
    ) * 10

    return round(fixture_score, 2)


def summarize_recent_form(recent_form_data):
    matches = recent_form_data.get("recent_form", [])

    if not matches:
        return {
            "recent_goals": 0,
            "recent_assists": 0,
            "recent_minutes": 0,
            "average_recent_rating": None
        }

    recent_goals = sum(
        match["goals"] or 0
        for match in matches
    )

    recent_assists = sum(
        match["assists"] or 0
        for match in matches
    )

    recent_minutes = sum(
        match["minutes"] or 0
        for match in matches
    )

    ratings = [
        match["rating"]
        for match in matches
        if match["rating"] is not None
    ]

    average_recent_rating = (
        sum(ratings) / len(ratings)
        if ratings
        else None
    )

    return {
        "recent_goals": recent_goals,
        "recent_assists": recent_assists,
        "recent_minutes": recent_minutes,
        "average_recent_rating": (
            round(average_recent_rating, 2)
            if average_recent_rating is not None
            else None
        )
    }


def get_forward_scores(current_gameweek):
    players = get_all_player_metrics(
        current_gameweek,
        position="Attacker"
    )

    players = normalize_metric(players, "goals_per_90")
    players = normalize_metric(players, "assists_per_90")
    players = normalize_metric(players, "shots_per_90")
    players = normalize_metric(players, "shots_on_target_per_90")
    players = normalize_metric(players, "average_rating")

    players = normalize_metric(players, "recent_goals")
    players = normalize_metric(players, "recent_assists")
    players = normalize_metric(players, "recent_minutes")
    players = normalize_metric(players, "average_recent_rating")

    for player in players:
        normalized_performance_rating = (
            player["normalized_average_rating"]
            if player["normalized_average_rating"] is not None
            else 0.5
        )

        score = (
            player["normalized_goals_per_90"] * 0.30
            + player["normalized_assists_per_90"] * 0.15
            + player["normalized_shots_per_90"] * 0.20
            + player["normalized_shots_on_target_per_90"] * 0.20
            + normalized_performance_rating * 0.15
        )

        player["performance_score"] = round(score * 10, 2)

        normalized_rating = (
            player["normalized_average_recent_rating"]
            if player["normalized_average_recent_rating"] is not None
            else 0.5
        )

        form_score = (
            player["normalized_recent_goals"] * 0.35
            + player["normalized_recent_assists"] * 0.25
            + normalized_rating * 0.25
            + player["normalized_recent_minutes"] * 0.15
        )

        player["form_score"] = round(form_score * 10, 2)

        average_fixture_difficulty = (
            player["upcoming_fixtures"]["average_fixture_difficulty"]
        )

        player["fixture_score"] = calculate_fixture_score(
            average_fixture_difficulty
        )

        overall_score = (
            player["performance_score"] * 0.40
            + player["form_score"] * 0.35
            + player["fixture_score"] * 0.25
        )

        player["overall_score"] = round(overall_score, 2)

    players.sort(key=lambda x: x["overall_score"], reverse=True)

    return players


def get_midfielder_scores(current_gameweek):
    players = get_all_player_metrics(
        current_gameweek,
        position="Midfielder"
    )

    players = normalize_metric(players, "goals_per_90")
    players = normalize_metric(players, "assists_per_90")
    players = normalize_metric(players, "shots_per_90")
    players = normalize_metric(players, "key_passes_per_90")
    players = normalize_metric(players, "average_rating")

    players = normalize_metric(players, "recent_goals")
    players = normalize_metric(players, "recent_assists")
    players = normalize_metric(players, "recent_minutes")
    players = normalize_metric(players, "average_recent_rating")

    for player in players:
        normalized_performance_rating = (
            player["normalized_average_rating"]
            if player["normalized_average_rating"] is not None
            else 0.5
        )

        score = (
            player["normalized_goals_per_90"] * 0.25
            + player["normalized_assists_per_90"] * 0.25
            + player["normalized_shots_per_90"] * 0.15
            + player["normalized_key_passes_per_90"] * 0.20
            + normalized_performance_rating * 0.15
        )

        player["performance_score"] = round(score * 10, 2)

        normalized_recent_rating = (
            player["normalized_average_recent_rating"]
            if player["normalized_average_recent_rating"] is not None
            else 0.5
        )

        form_score = (
            player["normalized_recent_goals"] * 0.30
            + player["normalized_recent_assists"] * 0.25
            + normalized_recent_rating * 0.25
            + player["normalized_recent_minutes"] * 0.20
        )

        player["form_score"] = round(form_score * 10, 2)

        average_fixture_difficulty = (
            player["upcoming_fixtures"]["average_fixture_difficulty"]
        )

        player["fixture_score"] = calculate_fixture_score(
            average_fixture_difficulty
        )

        overall_score = (
            player["performance_score"] * 0.40
            + player["form_score"] * 0.35
            + player["fixture_score"] * 0.25
        )

        player["overall_score"] = round(overall_score, 2)

    players.sort(key=lambda x: x["overall_score"], reverse=True)

    return players


def get_defender_scores(current_gameweek):
    players = get_all_player_metrics(
        current_gameweek,
        position="Defender"
    )

    players = normalize_metric(players, "tackles_per_90")
    players = normalize_metric(players, "interceptions_per_90")
    players = normalize_metric(players, "average_rating")
    players = normalize_metric(players, "goals_per_90")
    players = normalize_metric(players, "assists_per_90")

    players = normalize_metric(players, "recent_goals")
    players = normalize_metric(players, "recent_assists")
    players = normalize_metric(players, "recent_minutes")
    players = normalize_metric(players, "average_recent_rating")

    for player in players:
        normalized_performance_rating = (
            player["normalized_average_rating"]
            if player["normalized_average_rating"] is not None
            else 0.5
        )

        score = (
            player["normalized_tackles_per_90"] * 0.25
            + player["normalized_interceptions_per_90"] * 0.25
            + normalized_performance_rating * 0.20
            + player["normalized_goals_per_90"] * 0.15
            + player["normalized_assists_per_90"] * 0.15
        )

        player["performance_score"] = round(score * 10, 2)

        normalized_recent_rating = (
            player["normalized_average_recent_rating"]
            if player["normalized_average_recent_rating"] is not None
            else 0.5
        )

        form_score = (
            player["normalized_recent_goals"] * 0.15
            + player["normalized_recent_assists"] * 0.10
            + normalized_recent_rating * 0.45
            + player["normalized_recent_minutes"] * 0.30
        )

        player["form_score"] = round(form_score * 10, 2)

        average_fixture_difficulty = (
            player["upcoming_fixtures"]["average_fixture_difficulty"]
        )

        player["fixture_score"] = calculate_fixture_score(
            average_fixture_difficulty
        )

        overall_score = (
            player["performance_score"] * 0.40
            + player["form_score"] * 0.35
            + player["fixture_score"] * 0.25
        )

        player["overall_score"] = round(overall_score, 2)

    players.sort(key=lambda x: x["overall_score"], reverse=True)

    return players


def get_goalkeeper_scores(current_gameweek):
    players = get_all_player_metrics(
        current_gameweek,
        position="Goalkeeper"
    )

    players = normalize_metric(players, "average_rating")

    players = normalize_metric(players, "recent_minutes")
    players = normalize_metric(players, "average_recent_rating")

    for player in players:
        normalized_performance_rating = (
            player["normalized_average_rating"]
            if player["normalized_average_rating"] is not None
            else 0.5
        )

        performance_score = (normalized_performance_rating * 1.0)

        player["performance_score"] = round(performance_score * 10, 2)

        normalized_recent_rating = (
            player["normalized_average_recent_rating"]
            if player["normalized_average_recent_rating"] is not None
            else 0.5
        )

        form_score = (
            normalized_recent_rating * 0.60
            + player["normalized_recent_minutes"] * 0.40
        )

        player["form_score"] = round(form_score * 10, 2)

        average_fixture_difficulty = (
            player["upcoming_fixtures"][
                "average_fixture_difficulty"
            ]
        )

        player["fixture_score"] = calculate_fixture_score(
            average_fixture_difficulty
        )

        overall_score = (
            player["performance_score"] * 0.35
            + player["form_score"] * 0.30
            + player["fixture_score"] * 0.35
        )

        player["overall_score"] = round(overall_score, 2)

    players.sort(key=lambda x: x["overall_score"], reverse=True)

    return players


def get_ranked_players_by_position(position, current_gameweek):
    normalized_position = position.strip().lower()

    position_map = {
    "goalkeeper": get_goalkeeper_scores,
    "defender": get_defender_scores,
    "midfielder": get_midfielder_scores,
    "attacker": get_forward_scores
}

    scoring_function = position_map.get(normalized_position)

    if not scoring_function:
        return {
            "error": "Invalid position"
        }

    return scoring_function(current_gameweek)
    
