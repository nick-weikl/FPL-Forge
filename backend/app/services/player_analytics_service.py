from app.database import SessionLocal
from app.models import PlayerMatchStat
from app.models import fixture
from app.models.fixture import Fixture
from app.services.fixture_analytics_service import get_upcoming_fixtures
from sqlalchemy import func
from app.services.football_api import SEASON


def get_player_summary(
    player_id,
    current_gameweek,
    db=None
):
    owns_db = db is None

    if owns_db:
        db = SessionLocal()


    try:
        player_stats = (
            db.query(PlayerMatchStat)
            .join(
                Fixture,
                PlayerMatchStat.fixture_id == Fixture.id,
                Fixture.season == SEASON,
            )
            .filter(
                PlayerMatchStat.player_id == player_id,
                Fixture.gameweek <= current_gameweek
            )
            .all()
        )

        if not player_stats:
            return {"error": "No stats found for the player"}

        total_goals = sum(stat.goals for stat in player_stats)
        total_assists = sum(stat.assists for stat in player_stats)
        total_minutes = sum(stat.minutes for stat in player_stats)
        total_shots = sum(stat.shots for stat in player_stats)
        total_shots_on_target = sum(stat.shots_on_target for stat in player_stats)
        total_key_passes = sum(stat.key_passes for stat in player_stats)
        total_tackles = sum(stat.tackles for stat in player_stats)
        total_interceptions = sum(stat.interceptions for stat in player_stats)
        total_yellow_cards = sum(stat.yellow_cards for stat in player_stats)
        total_red_cards = sum(stat.red_cards for stat in player_stats)
        matches_played = len(player_stats)

        ratings = [
            stat.rating
            for stat in player_stats
            if stat.rating is not None
        ]

        average_rating = (
            sum(ratings) / len(ratings)
            if ratings 
            else None
        )

        goals_per_90 = (total_goals / total_minutes * 90) if total_minutes > 0 else 0
        assists_per_90 = (total_assists / total_minutes * 90) if total_minutes > 0 else 0
        shots_per_90 = (total_shots / total_minutes * 90) if total_minutes > 0 else 0
        shots_on_target_per_90 = (total_shots_on_target / total_minutes * 90) if total_minutes > 0 else 0
        key_passes_per_90 = (total_key_passes / total_minutes * 90) if total_minutes > 0 else 0
        tackles_per_90 = (total_tackles / total_minutes * 90) if total_minutes > 0 else 0
        interceptions_per_90 = (total_interceptions / total_minutes * 90) if total_minutes > 0 else 0

        return {
            "player_id": player_id,
            "total_goals": total_goals,
            "total_assists": total_assists,
            "total_minutes": total_minutes,
            "total_shots": total_shots,
            "total_shots_on_target": total_shots_on_target,
            "total_key_passes": total_key_passes,
            "total_tackles": total_tackles,
            "total_interceptions": total_interceptions,
            "total_yellow_cards": total_yellow_cards,
            "total_red_cards": total_red_cards,
            "matches_played": matches_played,
            "average_rating": round(average_rating, 2) if average_rating is not None else None,
            "goals_per_90": round(goals_per_90, 2),
            "assists_per_90": round(assists_per_90, 2),
            "shots_per_90": round(shots_per_90, 2),
            "shots_on_target_per_90": round(shots_on_target_per_90, 2),
            "key_passes_per_90" : round(key_passes_per_90, 2),
            "tackles_per_90": round(tackles_per_90, 2),
            "interceptions_per_90": round(interceptions_per_90, 2),
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        if owns_db:
            db.close()


def get_all_player_summaries(
    current_gameweek,
    player_ids=None,
    db=None
):
    owns_db = db is None

    if owns_db:
        db = SessionLocal()

    try:
        query = (
            db.query(
                PlayerMatchStat.player_id,

                func.sum(
                    PlayerMatchStat.goals
                ).label("total_goals"),

                func.sum(
                    PlayerMatchStat.assists
                ).label("total_assists"),

                func.sum(
                    PlayerMatchStat.minutes
                ).label("total_minutes"),

                func.sum(
                    PlayerMatchStat.shots
                ).label("total_shots"),

                func.sum(
                    PlayerMatchStat.shots_on_target
                ).label("total_shots_on_target"),

                func.sum(
                    PlayerMatchStat.key_passes
                ).label("total_key_passes"),

                func.sum(
                    PlayerMatchStat.tackles
                ).label("total_tackles"),

                func.sum(
                    PlayerMatchStat.interceptions
                ).label("total_interceptions"),

                func.sum(
                    PlayerMatchStat.yellow_cards
                ).label("total_yellow_cards"),

                func.sum(
                    PlayerMatchStat.red_cards
                ).label("total_red_cards"),

                func.count(
                    PlayerMatchStat.id
                ).label("matches_played"),

                func.avg(
                    PlayerMatchStat.rating
                ).label("average_rating")
            )
            .join(
                Fixture,
                PlayerMatchStat.fixture_id
                == Fixture.id
            )
            .filter(
                Fixture.gameweek
                <= current_gameweek,
                Fixture.season == SEASON,
            )
        )

        if player_ids:
            query = query.filter(
                PlayerMatchStat.player_id.in_(
                    player_ids
                )
            )

        rows = (
            query
            .group_by(
                PlayerMatchStat.player_id
            )
            .all()
        )

        summaries = {}

        for row in rows:
            total_minutes = (
                row.total_minutes or 0
            )

            def per_90(value):
                if total_minutes <= 0:
                    return 0

                return round(
                    (
                        (value or 0)
                        / total_minutes
                    ) * 90,
                    2
                )

            summaries[row.player_id] = {
                "player_id":
                    row.player_id,

                "total_goals":
                    row.total_goals or 0,

                "total_assists":
                    row.total_assists or 0,

                "total_minutes":
                    total_minutes,

                "total_shots":
                    row.total_shots or 0,

                "total_shots_on_target":
                    row.total_shots_on_target
                    or 0,

                "total_key_passes":
                    row.total_key_passes or 0,

                "total_tackles":
                    row.total_tackles or 0,

                "total_interceptions":
                    row.total_interceptions
                    or 0,

                "total_yellow_cards":
                    row.total_yellow_cards or 0,

                "total_red_cards":
                    row.total_red_cards or 0,

                "matches_played":
                    row.matches_played,

                "average_rating": (
                    round(
                        float(row.average_rating),
                        2
                    )
                    if row.average_rating
                    is not None
                    else None
                ),

                "goals_per_90":
                    per_90(
                        row.total_goals
                    ),

                "assists_per_90":
                    per_90(
                        row.total_assists
                    ),

                "shots_per_90":
                    per_90(
                        row.total_shots
                    ),

                "shots_on_target_per_90":
                    per_90(
                        row.total_shots_on_target
                    ),

                "key_passes_per_90":
                    per_90(
                        row.total_key_passes
                    ),

                "tackles_per_90":
                    per_90(
                        row.total_tackles
                    ),

                "interceptions_per_90":
                    per_90(
                        row.total_interceptions
                    )
            }

        return summaries

    finally:
        if owns_db:
            db.close()


def get_player_recent_form(
    player_id,
    current_gameweek,
    num_matches=5,
    db=None
):
    owns_db = db is None

    if owns_db:
        db = SessionLocal()

    try:
        player_stats = (
            db.query(PlayerMatchStat, Fixture)
            .join(
                Fixture,
                PlayerMatchStat.fixture_id == Fixture.id
            )
            .filter(
                PlayerMatchStat.player_id == player_id,
                Fixture.gameweek <= current_gameweek,
                Fixture.season == SEASON,
            )
            .order_by(Fixture.fixture_date.desc())
            .limit(num_matches)
            .all()
        )

        if not player_stats:
            return {
                "error": "No stats found for the player"
            }

        recent_form = [
            {
                "match_date": fixture.fixture_date,
                "goals": stat.goals,
                "assists": stat.assists,
                "minutes": stat.minutes,
                "rating": stat.rating
            }
            for stat, fixture in player_stats
        ]

        return {
            "player_id": player_id,
            "recent_form": recent_form
        }

    except Exception as e:
        return {
            "error": str(e)
        }

    finally:
        if owns_db:
            db.close()


def get_player_analytics(
        player_id,
        current_gameweek,
        recent_matches=5,
        fixture_limit=5
    ):

    summary = get_player_summary(
    player_id,
    current_gameweek
    )

    recent_form = get_player_recent_form(
        player_id,
        current_gameweek,
        recent_matches
    )

    upcoming_fixtures = get_upcoming_fixtures(
        player_id,
        current_gameweek,
        fixture_limit
    )

    return {
        "player_id": player_id,
        "summary": summary,
        "recent_form": recent_form,
        "upcoming_fixtures": upcoming_fixtures
    }
