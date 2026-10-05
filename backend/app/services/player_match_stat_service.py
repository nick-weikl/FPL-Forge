from app.database import SessionLocal
from app.models import PlayerMatchStat
from app.models.fixture import Fixture
from app.models import Player
from app.services.football_api import get_player_match_stats
import time
import requests


def sync_player_match_stats(fixture_id):
    db = SessionLocal()

    added = 0
    updated = 0
    skipped = 0

    try:
        fixture = (
            db.query(Fixture)
            .filter(Fixture.id == fixture_id)
            .first()
        )

        if not fixture:
            return {
                "error": "Fixture not found"
            }

        external_id = fixture.external_api_id

        data = get_player_match_stats(external_id)

        for team_item in data["response"]:
            for player_item in team_item["players"]:

                player_data = player_item["player"]
                api_player_id = player_data["id"]

                player = (
                    db.query(Player)
                    .filter(
                        Player.external_api_id == api_player_id
                    )
                    .first()
                )

                if not player:
                    skipped += 1
                    continue

                stats_data = player_item.get(
                    "statistics",
                    []
                )

                if not stats_data:
                    skipped += 1
                    continue

                stats = stats_data[0]

                rating = stats["games"]["rating"]

                if rating is not None:
                    rating = float(rating)

                existing_stat = (
                    db.query(PlayerMatchStat)
                    .filter(
                        PlayerMatchStat.player_id == player.id,
                        PlayerMatchStat.fixture_id == fixture.id
                    )
                    .first()
                )

                if existing_stat:
                    existing_stat.minutes = (
                        stats["games"]["minutes"] or 0
                    )

                    existing_stat.goals = (
                        stats["goals"]["total"] or 0
                    )

                    existing_stat.assists = (
                        stats["goals"]["assists"] or 0
                    )

                    existing_stat.shots = (
                        stats["shots"]["total"] or 0
                    )

                    existing_stat.shots_on_target = (
                        stats["shots"]["on"] or 0
                    )

                    existing_stat.key_passes = (
                        stats["passes"]["key"] or 0
                    )

                    existing_stat.tackles = (
                        stats["tackles"]["total"] or 0
                    )

                    existing_stat.interceptions = (
                        stats["tackles"]["interceptions"] or 0
                    )

                    existing_stat.yellow_cards = (
                        stats["cards"]["yellow"] or 0
                    )

                    existing_stat.red_cards = (
                        stats["cards"]["red"] or 0
                    )

                    existing_stat.rating = rating

                    updated += 1

                else:
                    new_stat = PlayerMatchStat(
                        player_id=player.id,
                        fixture_id=fixture.id,
                        minutes=stats["games"]["minutes"] or 0,
                        goals=stats["goals"]["total"] or 0,
                        assists=stats["goals"]["assists"] or 0,
                        shots=stats["shots"]["total"] or 0,
                        shots_on_target=stats["shots"]["on"] or 0,
                        key_passes=stats["passes"]["key"] or 0,
                        tackles=stats["tackles"]["total"] or 0,
                        interceptions=(
                            stats["tackles"]["interceptions"] or 0
                        ),
                        yellow_cards=(
                            stats["cards"]["yellow"] or 0
                        ),
                        red_cards=(
                            stats["cards"]["red"] or 0
                        ),
                        rating=rating
                    )

                    db.add(new_stat)
                    added += 1

        db.commit()

        return {
            "added": added,
            "updated": updated,
            "skipped": skipped
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


import time
import requests


def sync_completed_fixture_stats(current_gameweek):
    db = SessionLocal()

    total_added = 0
    total_updated = 0
    total_skipped = 0

    try:
        completed_fixtures = (
            db.query(Fixture)
            .filter(
                Fixture.status == "FT",
                Fixture.gameweek <= current_gameweek
            )
            .order_by(
                Fixture.gameweek,
                Fixture.fixture_date
            )
            .all()
        )

        fixture_ids = [
            fixture.id
            for fixture in completed_fixtures
        ]

    finally:
        db.close()

    for fixture_id in fixture_ids:
        while True:
            try:
                result = sync_player_match_stats(
                    fixture_id
                )

                if "error" in result:
                    break

                total_added += result.get("added", 0)
                total_updated += result.get("updated", 0)
                total_skipped += result.get("skipped", 0)

                # Conservative delay for lower-tier API limits
                time.sleep(0.5)

                break

            except requests.exceptions.HTTPError as e:
                if e.response is not None and e.response.status_code == 429:
                    print(
                        f"Rate limit reached on fixture {fixture_id}. "
                        "Waiting 60 seconds before retrying..."
                    )

                    time.sleep(0.5)
                    continue

                raise

    return {
        "fixtures_processed": len(fixture_ids),
        "added": total_added,
        "updated": total_updated,
        "skipped": total_skipped
    }