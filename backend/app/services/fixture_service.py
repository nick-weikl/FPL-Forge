from datetime import datetime, timezone

from app.database import SessionLocal
from app.models.team import Team
from app.models.fixture import Fixture
from app.services.football_api import (
    LEAGUE_ID,
    SEASON,
    get_premier_league_fixtures
)
from app.services.fpl_price_service import (
    FPL_SEASON,
    get_fpl_fixtures
)


def sync_premier_league_fixtures():
    fpl_fixtures = get_fpl_fixtures()
    data = get_premier_league_fixtures()

    if data.get("errors"):
        raise ValueError(
            f"API-Sports returned errors: {data['errors']}"
        )

    rows = data.get("response")

    if not isinstance(rows, list) or not rows:
        raise ValueError("API-Sports returned no fixtures")

    fpl_by_pair = {
        (item["team_h"], item["team_a"]): item
        for item in fpl_fixtures
    }

    if len(fpl_by_pair) != len(fpl_fixtures):
        raise ValueError("Duplicate FPL home/away fixture pairs")

    db = SessionLocal()
    added = 0
    updated = 0
    unassigned_gameweeks = 0
    seen_api_ids = set()
    seen_pairs = set()

    try:
        teams = (
            db.query(Team)
            .filter(Team.fpl_season == FPL_SEASON)
            .all()
        )

        if (
            len(teams) != 20
            or any(team.external_api_id is None for team in teams)
        ):
            raise ValueError("Link all 20 clubs before importing fixtures")

        teams_by_api_id = {
            team.external_api_id: team
            for team in teams
        }

        existing_fixtures = (
            db.query(Fixture)
            .filter(Fixture.season == SEASON)
            .all()
        )

        fixtures_by_api_id = {
            fixture.external_api_id: fixture
            for fixture in existing_fixtures
        }

        for item in rows:
            league = item["league"]

            if (
                league["id"] != LEAGUE_ID
                or league["season"] != SEASON
            ):
                raise ValueError("API-Sports returned another league or season")

            source = item["fixture"]
            api_id = source["id"]

            if api_id in seen_api_ids:
                raise ValueError(f"Duplicate API fixture ID: {api_id}")

            seen_api_ids.add(api_id)

            home = teams_by_api_id.get(item["teams"]["home"]["id"])
            away = teams_by_api_id.get(item["teams"]["away"]["id"])

            if home is None or away is None:
                raise ValueError(f"Unlinked club in fixture {api_id}")

            pair = (home.fpl_team_id, away.fpl_team_id)
            fpl_fixture = fpl_by_pair.get(pair)

            if fpl_fixture is None:
                raise ValueError(f"No FPL counterpart for fixture {api_id}")

            seen_pairs.add(pair)
            gameweek = fpl_fixture["event"]

            if gameweek is None:
                unassigned_gameweeks += 1
            elif not isinstance(gameweek, int) or not 1 <= gameweek <= 38:
                raise ValueError(f"Invalid FPL gameweek for fixture {api_id}")

            date_text = (
                fpl_fixture.get("kickoff_time")
                or source["date"]
            )

            # Existing DateTime column stores timestamps without timezone.
            fixture_date = (
                datetime.fromisoformat(
                    date_text.replace("Z", "+00:00")
                )
                .astimezone(timezone.utc)
                .replace(tzinfo=None)
            )

            fixture = fixtures_by_api_id.get(api_id)

            if fixture is None:
                fixture = Fixture(
                    external_api_id=api_id,
                    season=SEASON
                )
                db.add(fixture)
                fixtures_by_api_id[api_id] = fixture
                added += 1
            else:
                updated += 1

            fixture.gameweek = gameweek
            fixture.fixture_date = fixture_date
            fixture.status = source["status"]["short"]
            fixture.home_team_id = home.id
            fixture.away_team_id = away.id
            fixture.home_score = item["goals"]["home"]
            fixture.away_score = item["goals"]["away"]

        db.commit()

        return {
            "season": SEASON,
            "added": added,
            "updated": updated,
            "skipped": 0,
            "unassigned_gameweeks": unassigned_gameweeks,
            "fpl_fixtures_without_api_match": len(
                set(fpl_by_pair) - seen_pairs
            )
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()