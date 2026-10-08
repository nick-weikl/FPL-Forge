import os
import requests

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")

BASE_URL = "https://v3.football.api-sports.io"
LEAGUE_ID = 39
SEASON = 2026

headers = {
    "x-apisports-key": API_KEY
}


def get_premier_league_teams():
    url = f"{BASE_URL}/teams"

    params = {
        "league": LEAGUE_ID,
        "season": SEASON
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=20
    )

    response.raise_for_status()

    return response.json()


def get_premier_league_players(page=1):
    url = f"{BASE_URL}/players"

    params = {
        "league": LEAGUE_ID,
        "season": SEASON,
        "page": page
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=20
    )

    response.raise_for_status()

    return response.json()


def get_premier_league_fixtures():
    url = f"{BASE_URL}/fixtures"

    params = {
        "league": LEAGUE_ID,
        "season": SEASON
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=20
    )

    response.raise_for_status()

    return response.json()


def get_player_match_stats(fixture_id):
    url = f"{BASE_URL}/fixtures/players"

    params = {
        "fixture": fixture_id
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=20
    )

    response.raise_for_status()

    return response.json()