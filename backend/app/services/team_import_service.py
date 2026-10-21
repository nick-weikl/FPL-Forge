"""Read a public FPL deadline snapshot without credentials or database writes."""
from collections import Counter
from datetime import datetime, timezone
import requests
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from fastapi import HTTPException
from app.models import Player
from app.models.fpl_data import FPLImport
from app.services.football_api import SEASON
from app.services.fpl_price_service import FPL_SEASON

ROOT = 'https://fantasy.premierleague.com/api/'


def fetch_public_json(path):
    try:
        response = requests.get(ROOT + path, timeout=15, headers={'User-Agent': 'FPL-Forge/1.0'})
        if response.status_code == 404:
            raise HTTPException(404, 'FPL team or published squad not found. Check the team ID and current season.')
        if response.status_code == 429:
            raise HTTPException(503, 'FPL is receiving too many requests. Please try again shortly.')
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError('Expected an object')
        return data
    except requests.Timeout:
        raise HTTPException(504, 'FPL took too long to respond. Please try again.') from None
    except (requests.RequestException, ValueError):
        raise HTTPException(502, 'Could not read public team data from FPL. Please try again later.') from None


def preview_team_import(db, entry_id):
    bootstrap = fetch_public_json('bootstrap-static/')
    entry = fetch_public_json(f'entry/{entry_id}/')
    try:
        events = bootstrap['events']
        if int(events[0]['deadline_time'][:4]) != SEASON:
            raise HTTPException(409, 'The backend season does not match the live FPL season. Update season data before importing.')
        if entry['id'] != entry_id or not isinstance(entry['name'], str):
            raise ValueError('Unexpected team identity')
        current = entry.get('current_event')
        now = datetime.now(timezone.utc)
        available = [event for event in events if type(event['id']) is int
                     and type(current) is int and event['id'] <= current
                     and datetime.fromisoformat(event['deadline_time'].replace('Z', '+00:00')) <= now]
        if not available:
            raise HTTPException(409, 'This team does not have a published gameweek squad yet. Try after its first deadline.')
        event = max(available, key=lambda event: event['id'])
        gameweek = event['id']
    except (KeyError, TypeError, ValueError, IndexError):
        raise HTTPException(502, 'FPL returned incomplete team or season data. Please try again.') from None
    picks = fetch_public_json(f'entry/{entry_id}/event/{gameweek}/picks/')
    try:
        history = picks['entry_history']
        bank = history['bank']
        rows = picks['picks']
        if history['event'] != gameweek or type(bank) is not int or bank < 0 or not isinstance(rows, list) or len(rows) != 15:
            raise ValueError('Invalid bank or squad')
        fpl_ids = [row['element'] for row in rows]
        positions = [row['position'] for row in rows]
        if any(type(pid) is not int or pid <= 0 for pid in fpl_ids) or len(set(fpl_ids)) != 15:
            raise ValueError('Invalid player IDs')
        if any(type(position) is not int for position in positions) or set(positions) != set(range(1,16)):
            raise ValueError('Invalid squad order')
    except (KeyError, TypeError, ValueError):
        raise HTTPException(502, 'FPL returned an incomplete squad or bank balance. Your existing squad has not been changed.') from None
    players = list(db.scalars(select(Player).options(joinedload(Player.team)).where(
        Player.fpl_season == FPL_SEASON, Player.fpl_player_id.in_(fpl_ids))))
    by_fpl = {player.fpl_player_id: player for player in players}
    missing = sorted(set(fpl_ids) - by_fpl.keys())
    if missing:
        raise HTTPException(409, detail={'error': 'Some imported players are missing from the current database roster. Refresh FPL player data before importing.', 'missing_fpl_player_ids': missing})
    warnings = [
        'This is the published deadline squad. Transfers made since that deadline may not be included.',
        'Purchase prices, selling values and available free transfers are not imported. Review free transfers and selling values before running analysis.',
        'Player prices and clubs below come from the current FPL Forge database, not the historical deadline snapshot.'
    ]
    counts = Counter(player.team_id for player in players)
    if any(count > 3 for count in counts.values()):
        warnings.append('Club changes since the deadline leave more than three players at one club. Review your squad before analysis.')
    latest = db.scalar(select(func.max(FPLImport.gameweek)).where(FPLImport.season == SEASON))
    if latest is None or latest < gameweek:
        warnings.append('Stored match data does not yet cover this deadline gameweek. Analysis will use the latest available completed gameweek.')
    return {'entry_id': entry_id, 'team_name': entry['name'], 'season': FPL_SEASON,
            'gameweek': gameweek, 'deadline_time': event['deadline_time'],
            'bank_tenths': bank, 'analysis_gameweek': min(gameweek, latest) if latest is not None else None,
            'warnings': warnings,
            'players': [{'id': by_fpl[row['element']].id,
                         'external_api_id': by_fpl[row['element']].external_api_id,
                         'name': by_fpl[row['element']].name,
                         'team_id': by_fpl[row['element']].team_id,
                         'team_name': by_fpl[row['element']].team.name,
                         'position': by_fpl[row['element']].position,
                         'price_tenths': by_fpl[row['element']].price_tenths}
                        for row in sorted(rows, key=lambda row: row['position'])]}
