from app.database import SessionLocal
from app.models import PlayerMatchStat
from app.models.fixture import Fixture
from app.models import Player
from app.services.football_api import get_player_match_stats
import time
import requests

from app.services.football_api import SEASON
from app.services.fpl_price_service import FPL_SEASON


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

        if fixture.season != SEASON:
            return {"error": "Fixture belongs to another season"}

        if fixture.status != "FT":
            return {"error": "Fixture has not finished"}

        external_id = fixture.external_api_id

        data = get_player_match_stats(external_id)

        if data.get("errors"):
            raise ValueError(
                f"API-Sports returned errors: {data['errors']}"
            )

        if not isinstance(data.get("response"), list) or not data["response"]:
            return {
                "error": f"No match statistics returned for fixture {fixture_id}"
            }

        for team_item in data["response"]:
            for player_item in team_item["players"]:

                player_data = player_item["player"]
                api_player_id = player_data["id"]

                player = (
                    db.query(Player)
                    .filter(
                        Player.external_api_id == api_player_id,
                        Player.fpl_season == FPL_SEASON
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

    try:
        fixtures = (
            db.query(Fixture)
            .filter(
                Fixture.season == SEASON,
                Fixture.status == "FT",
                Fixture.gameweek <= current_gameweek
            )
            .order_by(Fixture.fixture_date, Fixture.id)
            .all()
        )

        fixture_ids = [fixture.id for fixture in fixtures]

    finally:
        db.close()

    totals = {
        "season": SEASON,
        "through_gameweek": current_gameweek,
        "fixtures_selected": len(fixture_ids),
        "fixtures_processed": 0,
        "added": 0,
        "updated": 0,
        "skipped": 0,
        "failed_fixtures": []
    }

    for index, fixture_id in enumerate(fixture_ids, start=1):
        print(
            f"Importing fixture {index}/{len(fixture_ids)} "
            f"(database ID {fixture_id})"
        )

        for attempt in range(3):
            try:
                result = sync_player_match_stats(fixture_id)
                break

            except requests.exceptions.HTTPError as error:
                rate_limited = (
                    error.response is not None
                    and error.response.status_code == 429
                )

                if not rate_limited or attempt == 2:
                    raise

                print("Rate limited. Retrying in 30 seconds...")
                time.sleep(30)

        if "error" in result:
            totals["failed_fixtures"].append({
                "fixture_id": fixture_id,
                "error": result["error"]
            })
            continue

        totals["fixtures_processed"] += 1

        for key in ("added", "updated", "skipped"):
            totals[key] += result.get(key, 0)

        time.sleep(0.5)

    return totals