from app.database import SessionLocal
from app.models import PlayerMatchStat
from app.models import fixture
from app.models.fixture import Fixture
from app.services.fixture_analytics_service import get_upcoming_fixtures


def get_player_summary(player_id):
    db = SessionLocal()


    try:
        player_stats = (
            db.query(PlayerMatchStat)
            .filter(PlayerMatchStat.player_id == player_id)
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
            "shots_on_target_per_90": round(shots_on_target_per_90, 2)
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()


def get_player_recent_form(player_id, num_matches=5):
    db = SessionLocal()

    try:
        player_stats = (
            db.query(PlayerMatchStat, Fixture)
            .join(Fixture, PlayerMatchStat.fixture_id == Fixture.id)
            .filter(PlayerMatchStat.player_id == player_id)
            .order_by(Fixture.fixture_date.desc())
            .limit(num_matches)
            .all()
        )

        if not player_stats:
            return {"error": "No stats found for the player"}

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
        return {"error": str(e)}
    finally:
        db.close()


def get_player_analytics(
        player_id,
        current_gameweek,
        recent_matches=5,
        fixture_limit=5
    ):
    summary = get_player_summary(player_id)

    recent_form = get_player_recent_form(
        player_id,
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

