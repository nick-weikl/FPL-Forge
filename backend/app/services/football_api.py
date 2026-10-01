import os
import requests

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")

BASE_URL = "https://v3.football.api-sports.io"

headers = {
    "x-apisports-key": API_KEY
}


def get_premier_league_teams():
    url = f"{BASE_URL}/teams"

    params = {
        "league": 39,
        "season": 2024
    }

    response = requests.get(
        url,
        headers=headers,
        params=params
    )

    response.raise_for_status()

    return response.json()


def get_premier_league_players(page=1):
    url = f"{BASE_URL}/players"

    params = {
        "league": 39,
        "season": 2024,
        "page": page
    }

    response = requests.get(
        url,
        headers=headers,
        params=params
    )

    response.raise_for_status()

    return response.json()