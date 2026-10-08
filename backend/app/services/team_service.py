from app.database import SessionLocal
from app.models.team import Team
from app.services.fpl_price_service import (
    FPL_SEASON,
    get_fpl_bootstrap
)
import re
from collections import defaultdict

from app.services.football_api import get_premier_league_teams


def sync_premier_league_teams(data=None, db=None):
    if data is None:
        data = get_fpl_bootstrap()

    owns_db = db is None

    if owns_db:
        db = SessionLocal()

    added = 0
    updated = 0

    try:
        existing_teams = (
            db.query(Team)
            .filter(Team.fpl_season == FPL_SEASON)
            .all()
        )

        teams_by_fpl_id = {
            team.fpl_team_id: team
            for team in existing_teams
        }

        for item in data["teams"]:
            team = teams_by_fpl_id.get(item["id"])

            if team is None:
                team = Team(
                    fpl_team_id=item["id"],
                    fpl_season=FPL_SEASON
                )
                db.add(team)
                teams_by_fpl_id[item["id"]] = team
                added += 1
            else:
                updated += 1

            team.name = item["name"]
            team.short_name = item["short_name"]

        db.flush()

        if owns_db:
            db.commit()

        return {
            "season": FPL_SEASON,
            "added": added,
            "updated": updated
        }

    except Exception:
        if owns_db:
            db.rollback()
        raise

    finally:
        if owns_db:
            db.close()


def normalize_club(name):
    key = re.sub(
        r"[^a-z0-9]+",
        " ",
        name.casefold()
    ).strip()

    aliases = {
        "man city": "manchester city",
        "man utd": "manchester united",
        "man united": "manchester united",
        "spurs": "tottenham",
        "tottenham hotspur": "tottenham",
        "nott m forest": "nottingham forest",
        "nottm forest": "nottingham forest",
        "brighton hove albion": "brighton",
        "brighton and hove albion": "brighton",
        "wolverhampton wanderers": "wolves",
        "newcastle united": "newcastle",
        "west ham united": "west ham",
        "afc bournemouth": "bournemouth",
        "leicester city": "leicester",
        "leeds united": "leeds",
        "ipswich town": "ipswich",
        "sunderland afc": "sunderland",
        "coventry city": "coventry",
    }

    return aliases.get(key, key)


def link_premier_league_teams(apply=False):
    data = get_premier_league_teams()

    if data.get("errors"):
        raise ValueError(
            f"API-Sports returned errors: {data['errors']}"
        )

    api_teams = data.get("response")

    if not isinstance(api_teams, list) or not api_teams:
        raise ValueError("API-Sports returned no clubs")

    lookup = defaultdict(list)

    for item in api_teams:
        team = item["team"]
        lookup[normalize_club(team["name"])].append(team)

    report = {
        "matched": [],
        "unmatched": [],
        "ambiguous": []
    }

    db = SessionLocal()

    try:
        teams = (
            db.query(Team)
            .filter(Team.fpl_season == FPL_SEASON)
            .order_by(Team.id)
            .all()
        )

        teams_by_id = {
            team.id: team
            for team in teams
        }

        for team in teams:
            candidates = lookup.get(
                normalize_club(team.name),
                []
            )

            if not candidates:
                report["unmatched"].append(team.name)
                continue

            if len(candidates) != 1:
                report["ambiguous"].append({
                    "fpl_name": team.name,
                    "candidates": candidates
                })
                continue

            candidate = candidates[0]

            if team.external_api_id not in (
                None,
                candidate["id"]
            ):
                raise ValueError(
                    f"Conflicting API-Sports link for {team.name}"
                )

            report["matched"].append({
                "db_team_id": team.id,
                "fpl_name": team.name,
                "api_name": candidate["name"],
                "external_api_id": candidate["id"]
            })

        if not apply:
            return report

        external_ids = {
            match["external_api_id"]
            for match in report["matched"]
        }

        if (
            len(teams) != 20
            or len(report["matched"]) != 20
            or len(external_ids) != 20
            or report["unmatched"]
            or report["ambiguous"]
        ):
            raise ValueError(
                "Resolve club matches before saving API-Sports links"
            )

        for match in report["matched"]:
            team = teams_by_id[match["db_team_id"]]
            team.external_api_id = match["external_api_id"]

        db.commit()

        return {
            "season": FPL_SEASON,
            "linked_teams": len(report["matched"])
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()