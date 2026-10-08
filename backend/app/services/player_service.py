from app.database import SessionLocal
from app.models.player import Player
from app.models.team import Team
from app.services.fpl_price_service import (
    FPL_SEASON,
    get_fpl_bootstrap,
    get_fpl_players
)
import re
import unicodedata
from collections import defaultdict
from sqlalchemy.orm import joinedload

from app.services.football_api import (
    LEAGUE_ID,
    SEASON,
    get_premier_league_players
)
import html

# Verified FPL spellings, keyed by API-Sports player ID.
API_PLAYER_NAME_ALIASES = {
    453101: ["Bradley Burrowes"],
    331832: ["António João Pereira de Albuquerque Tavares da Silva"],
    363333: ["Julio Soler Barreto"],
    153066: ["Fábio Freitas Gouveia Carvalho"],
    263538: ["Yehor Yarmoliuk"],
    278370: ["Diego Gómez Amarilla"],
    19599: ["Emiliano Martínez Romero"],
    116117: ["Moisés Caicedo Corozo"],
    366735: ["Josh Acheampong"],
    419582: ["Geovany Quenda"],
    475575: ["Caleb Yirenkyi"],
    2490: ["Jefferson Lerma Solís"],
    184226: ["Yéremy Pino Santos"],
    195993: ["Carlos Alcaraz Durán"],
    389315: ["Josh King"],
    32966: ["Tanaka Ao"],
    8500: ["Endo Wataru"],
    886: ["Diogo Dalot Teixeira"],
    6610: ["Marcos Senesi Barón"],
    18883: ["Dominic Solanke-Mitchell"]
}


def sync_premier_league_players(data=None, db=None):
    if data is None:
        data = get_fpl_bootstrap()

    fpl_players = get_fpl_players(data)

    owns_db = db is None

    if owns_db:
        db = SessionLocal()

    added = 0
    updated = 0

    try:
        teams = (
            db.query(Team)
            .filter(Team.fpl_season == FPL_SEASON)
            .all()
        )

        teams_by_fpl_id = {
            team.fpl_team_id: team
            for team in teams
        }

        missing_team_ids = {
            item["fpl_team_id"]
            for item in fpl_players
            if item["fpl_team_id"] not in teams_by_fpl_id
        }

        if missing_team_ids:
            raise ValueError(
                "Import FPL teams first. Missing club IDs: "
                f"{sorted(missing_team_ids)}"
            )

        existing_players = (
            db.query(Player)
            .filter(Player.fpl_season == FPL_SEASON)
            .all()
        )

        players_by_fpl_id = {
            player.fpl_player_id: player
            for player in existing_players
        }

        for item in fpl_players:
            player = players_by_fpl_id.get(
                item["fpl_player_id"]
            )

            if player is None:
                player = Player(
                    fpl_player_id=item["fpl_player_id"],
                    fpl_season=FPL_SEASON
                )
                db.add(player)
                players_by_fpl_id[item["fpl_player_id"]] = player
                added += 1
            else:
                updated += 1

            player.name = item["name"]
            player.position = item["position"]
            player.fpl_position = item["position"]
            player.team_id = teams_by_fpl_id[
                item["fpl_team_id"]
            ].id
            player.price_tenths = item["price_tenths"]

            # These are current prices, not a historical GW snapshot.
            player.fpl_price_gameweek = None

        db.flush()

        if owns_db:
            db.commit()

        return {
            "season": FPL_SEASON,
            "added": added,
            "updated": updated,
            "skipped": 0
        }

    except Exception:
        if owns_db:
            db.rollback()
        raise

    finally:
        if owns_db:
            db.close()


def normalize_player_name(name):
    name = unicodedata.normalize(
        "NFKD",
        html.unescape(name or "")
    )
    name = "".join(
        character
        for character in name
        if not unicodedata.combining(character)
    )
    return re.sub(
        r"[^a-z0-9]+",
        " ",
        name.casefold()
    ).strip()


def is_initial_name_match(short_name, full_name):
    short_parts = short_name.split()
    full_parts = full_name.split()

    if (
        len(short_parts) < 2
        or len(short_parts[0]) != 1
        or len(full_parts) < len(short_parts)
    ):
        return False

    surname = short_parts[1:]

    return (
        len(full_parts[0]) > 1
        and short_parts[0] == full_parts[0][0]
        and surname == full_parts[-len(surname):]
    )


def link_premier_league_players(apply=False):
    fpl_players = get_fpl_players(get_fpl_bootstrap())

    fpl_names = {
        player["fpl_player_id"]: {
            normalize_player_name(player["name"]),
            normalize_player_name(player["web_name"])
        } - {""}
        for player in fpl_players
    }

    api_players_by_team = defaultdict(dict)
    seen_api_ids = set()
    page = 1

    while True:
        data = get_premier_league_players(page=page)

        if data.get("errors"):
            raise ValueError(
                f"API-Sports errors on page {page}: "
                f"{data['errors']}"
            )

        rows = data.get("response")

        if not isinstance(rows, list):
            raise ValueError("Invalid API-Sports player response")

        for item in rows:
            player = item["player"]
            api_id = player["id"]
            seen_api_ids.add(api_id)

            full_name = (
                f"{player.get('firstname') or ''} "
                f"{player.get('lastname') or ''}"
            ).strip()

            names = {
                normalize_player_name(player.get("name")),
                normalize_player_name(full_name)
            } - {""}

            names.update(
                normalize_player_name(alias)
                for alias in API_PLAYER_NAME_ALIASES.get(api_id, [])
            )

            for stats in item.get("statistics", []):
                league = stats.get("league") or {}

                if (
                    league.get("id") != LEAGUE_ID
                    or league.get("season") != SEASON
                ):
                    continue

                team_id = (stats.get("team") or {}).get("id")

                if team_id is None:
                    continue

                record = api_players_by_team[team_id].setdefault(
                    api_id,
                    {
                        "external_api_id": api_id,
                        "name": player.get("name"),
                        "names": set()
                    }
                )
                record["names"].update(names)

        paging = data.get("paging") or {}
        current = int(paging.get("current", 0))
        total = int(paging.get("total", 0))

        if current != page or total < current:
            raise ValueError("Invalid API-Sports pagination")

        if current == total:
            break

        page += 1

    report = {
        "api_players_loaded": len(seen_api_ids),
        "pages_processed": page,
        "matched": [],
        "unmatched": [],
        "ambiguous": [],
        "duplicate_api_ids": []
    }

    db = SessionLocal()

    try:
        players = (
            db.query(Player)
            .options(joinedload(Player.team))
            .filter(Player.fpl_season == FPL_SEASON)
            .order_by(Player.id)
            .all()
        )

        for player in players:
            if not player.team or player.team.external_api_id is None:
                raise ValueError("Link all FPL clubs first")

            names = {
                normalize_player_name(player.name),
                *fpl_names.get(player.fpl_player_id, set())
            } - {""}

            candidates = list(
                api_players_by_team[
                    player.team.external_api_id
                ].values()
            )

            matches = [
                candidate
                for candidate in candidates
                if names & candidate["names"]
            ]
            method = "name_or_alias"

            if not matches:
                matches = [
                    candidate
                    for candidate in candidates
                    if any(
                        is_initial_name_match(left, right)
                        or is_initial_name_match(right, left)
                        for left in names
                        for right in candidate["names"]
                    )
                ]
                method = "initial_and_surname"

            entry = {
                "db_player_id": player.id,
                "fpl_name": player.name,
                "team_name": player.team.name
            }

            if len(matches) == 1:
                entry.update({
                    "api_name": matches[0]["name"],
                    "external_api_id": matches[0]["external_api_id"],
                    "match_method": method
                })
                report["matched"].append(entry)

            elif matches:
                entry["candidates"] = [
                    {
                        "name": candidate["name"],
                        "external_api_id": candidate["external_api_id"]
                    }
                    for candidate in matches
                ]
                report["ambiguous"].append(entry)

            else:
                report["unmatched"].append(entry)

        grouped = defaultdict(list)

        for match in report["matched"]:
            grouped[match["external_api_id"]].append(match)

        report["duplicate_api_ids"] = [
            {
                "external_api_id": api_id,
                "fpl_players": matches
            }
            for api_id, matches in grouped.items()
            if len(matches) > 1
        ]

        claimed_ids = {
            match["external_api_id"]
            for match in report["matched"]
        } | {
            player.external_api_id
            for player in players
            if player.external_api_id is not None
        }

        clubs_by_api_id = {
            player.team.external_api_id: player.team
            for player in players
        }

        report["unmatched_api_players"] = [
            {
                "team_name": club.name,
                "api_name": candidate["name"],
                "external_api_id": candidate["external_api_id"],
                "normalized_names": sorted(candidate["names"])
            }
            for api_team_id, club in clubs_by_api_id.items()
            for candidate in api_players_by_team[api_team_id].values()
            if candidate["external_api_id"] not in claimed_ids
        ]

        if apply:
            if (
                report["ambiguous"]
                or report["duplicate_api_ids"]
            ):
                raise ValueError(
                    "Resolve ambiguous or duplicate player links first"
                )

            if not report["matched"]:
                raise ValueError("No player matches to save")

            players_by_id = {
                player.id: player
                for player in players
            }

            for match in report["matched"]:
                player = players_by_id[match["db_player_id"]]
                api_id = match["external_api_id"]

                if player.external_api_id not in (None, api_id):
                    raise ValueError(
                        f"Conflicting API-Sports link for {player.name}"
                    )

                player.external_api_id = api_id

            db.commit()
            report["linked_players"] = len(report["matched"])

        return report

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()