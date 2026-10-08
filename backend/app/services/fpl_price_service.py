import json
from urllib.request import urlopen

from app.services.football_api import SEASON


FPL_URL = (
    "https://fantasy.premierleague.com/api/bootstrap-static/"
)

FPL_SEASON = f"{SEASON}/{(SEASON + 1) % 100:02d}"

POSITION_MAP = {
    1: "Goalkeeper",
    2: "Defender",
    3: "Midfielder",
    4: "Attacker"
}


def get_fpl_bootstrap():
    with urlopen(FPL_URL, timeout=20) as response:
        data = json.load(response)

    for key in ("teams", "elements", "events"):
        if not isinstance(data.get(key), list) or not data[key]:
            raise ValueError(
                f"FPL response has missing or invalid {key}"
            )

    # Check that FPL and API-Sports target the same season.
    first_deadline = data["events"][0]["deadline_time"]
    start_year = int(first_deadline[:4])

    if start_year != SEASON:
        raise ValueError(
            f"FPL season starts in {start_year}, "
            f"but API-Sports is configured for {SEASON}"
        )

    return data


def get_fpl_players(data):
    teams_by_id = {
        team["id"]: team
        for team in data["teams"]
    }

    players = []
    seen_ids = set()

    for element in data["elements"]:
        player_id = element["id"]
        position = POSITION_MAP.get(element["element_type"])
        team = teams_by_id.get(element["team"])
        price = element["now_cost"]

        if player_id in seen_ids:
            raise ValueError(f"Duplicate FPL player ID: {player_id}")

        if position is None or team is None:
            raise ValueError(
                f"Invalid position or club for FPL player {player_id}"
            )

        if not isinstance(price, int) or price <= 0:
            raise ValueError(
                f"Invalid price for FPL player {player_id}"
            )

        seen_ids.add(player_id)

        players.append({
            "fpl_player_id": player_id,
            "name": (
                f"{element['first_name']} "
                f"{element['second_name']}"
            ).strip(),
            "web_name": element["web_name"],
            "fpl_team_id": team["id"],
            "team_name": team["name"],
            "position": position,
            "price_tenths": price,
            "fpl_season": FPL_SEASON
        })

    return players

def get_fpl_fixtures():
    # Verify the live FPL season matches our configuration.
    get_fpl_bootstrap()

    url = "https://fantasy.premierleague.com/api/fixtures/"

    with urlopen(url, timeout=20) as response:
        fixtures = json.load(response)

    if not isinstance(fixtures, list) or not fixtures:
        raise ValueError("FPL returned no fixtures")

    return fixtures


if __name__ == "__main__":
    data = get_fpl_bootstrap()
    players = get_fpl_players(data)

    print(json.dumps({
        "season": FPL_SEASON,
        "teams_loaded": len(data["teams"]),
        "players_loaded": len(players),
        "sample": players[:5]
    }, indent=2, ensure_ascii=False))