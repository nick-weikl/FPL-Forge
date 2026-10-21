"""Archive official JSON and hashes; this command never connects to PostgreSQL."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from app.services.football_api import SEASON

ROOT = 'https://fantasy.premierleague.com/api/'


def download(directory, through=None):
    directory = Path(directory)
    if directory.exists() and any(directory.iterdir()):
        raise ValueError('Choose a new archive directory to preserve older observations')
    directory.mkdir(parents=True, exist_ok=True)
    sources = {}
    def fetch(name, path):
        url = ROOT + path
        with urlopen(Request(url, headers={'User-Agent': 'FPL-Forge/1.0'}), timeout=30) as response:
            raw = response.read()
        value = json.loads(raw)
        (directory / f'{name}.json').write_bytes(raw)
        sources[name] = {'url': url, 'sha256': hashlib.sha256(raw).hexdigest()}
        return value
    bootstrap = fetch('bootstrap', 'bootstrap-static/')
    if int(bootstrap['events'][0]['deadline_time'][:4]) != SEASON:
        raise ValueError('Official FPL season does not match configuration')
    latest = max(e['id'] for e in bootstrap['events'] if e['finished'])
    through = latest if through is None else through
    if not 1 <= through <= latest:
        raise ValueError('Select a completed gameweek')
    fixtures = {f['id']: f for f in fetch('fixtures', 'fixtures/')}
    missing_club_players = set()
    for gameweek in range(1, through + 1):
        event = fetch(f'event-{gameweek}', f'event/{gameweek}/live/')
        for element in event['elements']:
            for explanation in element['explain']:
                if not any(s['identifier'] == 'minutes' and s['value'] > 0 for s in explanation['stats']):
                    continue
                fixture = fixtures[explanation['fixture']]
                members = {m['element'] for group in fixture['stats'] for side in ['h','a'] for m in group[side]}
                if element['id'] not in members:
                    missing_club_players.add(element['id'])
    for pid in sorted(missing_club_players):
        fetch(f'player-{pid}', f'element-summary/{pid}/')
    manifest = {'downloaded_at': datetime.now(timezone.utc).isoformat(), 'sources': sources}
    (directory / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return {'directory': str(directory), 'latest_finished_gameweek': latest, 'downloaded_through': through}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('directory')
    parser.add_argument('--through-gameweek', type=int)
    args = parser.parse_args()
    print(download(args.directory, args.through_gameweek))
