"""Validate archived official FPL JSON before making one atomic import."""
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import select
from app.models import Team, Player, Fixture, PlayerMatchStat
from app.models.fpl_data import FPLMatchStat, FPLImport, PlayerPriceSnapshot
from app.services.football_api import SEASON
from app.services.fpl_price_service import FPL_SEASON, get_fpl_players

OFFICIAL_ROOT = 'https://fantasy.premierleague.com/api/'


def load_archive(directory, through_gameweek):
    directory = Path(directory)
    manifest = json.loads((directory / 'manifest.json').read_text())
    observed_at = datetime.fromisoformat(manifest['downloaded_at'])
    if observed_at.tzinfo is None:
        raise ValueError('Archive timestamp must include timezone')
    names = ['bootstrap', 'fixtures'] + [f'event-{gw}' for gw in range(1, through_gameweek + 1)]
    payloads = {}
    expected_urls = {'bootstrap': OFFICIAL_ROOT + 'bootstrap-static/', 'fixtures': OFFICIAL_ROOT + 'fixtures/'}
    expected_urls.update({f'event-{gw}': OFFICIAL_ROOT + f'event/{gw}/live/' for gw in range(1, through_gameweek + 1)})
    for name in names:
        raw = (directory / f'{name}.json').read_bytes()
        source = manifest['sources'][name]
        if source['url'] != expected_urls[name] or hashlib.sha256(raw).hexdigest() != source['sha256']:
            raise ValueError(f'Archive provenance/hash mismatch: {name}')
        payloads[name] = json.loads(raw)
    for name, source in manifest['sources'].items():
        if not name.startswith('player-'):
            continue
        pid = int(name.split('-')[1])
        raw = (directory / f'{name}.json').read_bytes()
        if source['url'] != OFFICIAL_ROOT + f'element-summary/{pid}/' or hashlib.sha256(raw).hexdigest() != source['sha256']:
            raise ValueError(f'Archive player-history provenance mismatch: {name}')
        payloads[name] = json.loads(raw)
    bootstrap = payloads['bootstrap']
    if int(bootstrap['events'][0]['deadline_time'][:4]) != SEASON:
        raise ValueError('FPL archive season does not match configuration')
    events = {event['id']: event for event in bootstrap['events']}
    if any(not events[gw]['finished'] for gw in range(1, through_gameweek + 1)):
        raise ValueError('Only finalized gameweeks can be imported')
    fixtures = payloads['fixtures']
    if len(fixtures) != 380 or len({f['id'] for f in fixtures}) != len(fixtures):
        raise ValueError('Expected 380 distinct official fixtures')
    if len({(f['team_h'], f['team_a']) for f in fixtures}) != 380:
        raise ValueError('Duplicate official home/away pair')
    return payloads, manifest, observed_at


def fixture_memberships(source):
    result = {}
    for group in source['stats']:
        for side, club in [('h', source['team_h']), ('a', source['team_a'])]:
            for entry in group[side]:
                pid = entry['element']
                if pid in result and result[pid] != club:
                    raise ValueError('Player appears on both sides of a fixture')
                result[pid] = club
    return result


def build_stat_rows(payload, official_fixtures, player_ids, gameweek, historical_memberships=None):
    elements = payload['elements']
    if not elements or len({e['id'] for e in elements}) != len(elements):
        raise ValueError('Empty or duplicate gameweek player IDs')
    memberships = {fid: fixture_memberships(f) for fid, f in official_fixtures.items()}
    for fid, entries in (historical_memberships or {}).items():
        for pid, club in entries.items():
            existing = memberships[fid].get(pid)
            if existing is not None and existing != club:
                raise ValueError('Conflicting historical club evidence')
            memberships[fid][pid] = club
    rows = []
    covered = set()
    for element in elements:
        pid = element['id']
        if pid not in player_ids:
            raise ValueError(f'Unmapped FPL player {pid}; refresh roster before import')
        explanations = element['explain']
        if len({e['fixture'] for e in explanations}) != len(explanations):
            raise ValueError('Duplicate player/fixture explanation')
        if sum(s['points'] for e in explanations for s in e['stats']) != element['stats']['total_points']:
            raise ValueError('Explanation points do not match event points')
        if sum(s['value'] for e in explanations for s in e['stats'] if s['identifier'] == 'minutes') != element['stats']['minutes']:
            raise ValueError('Explanation minutes do not match event minutes')
        for explanation in explanations:
            fid = explanation['fixture']
            fixture = official_fixtures.get(fid)
            if not fixture or fixture['event'] != gameweek or not fixture['finished']:
                raise ValueError('Explanation refers to an unfinished or wrong-gameweek fixture')
            values = {s['identifier']: s['value'] for s in explanation['stats']}
            minutes = values.get('minutes', 0)
            if not isinstance(minutes, int) or not 0 <= minutes <= 130:
                raise ValueError('Invalid minutes')
            # Never assign historical club from the latest roster.
            club = memberships[fid].get(pid)
            if minutes > 0 and club is None:
                raise ValueError(f'No historical club evidence for participating player {pid}')
            rows.append({'fpl_player_id': pid, 'fpl_fixture_id': fid,
                         'fpl_team_id': club, 'minutes': minutes,
                         'total_points': sum(s['points'] for s in explanation['stats']),
                         'stats': element['stats'] if len(explanations) == 1 else values})
            covered.add(fid)
    expected = {f['id'] for f in official_fixtures.values() if f['event'] == gameweek}
    if covered != expected:
        raise ValueError('Gameweek player data does not cover all official fixtures')
    return rows


def import_archive(db, directory, through_gameweek, apply=False):
    if not 1 <= through_gameweek <= 38:
        raise ValueError('Gameweek must be 1–38')
    payloads, manifest, observed_at = load_archive(directory, through_gameweek)
    roster = get_fpl_players(payloads['bootstrap'])
    source_teams = {t['id']: t for t in payloads['bootstrap']['teams']}
    teams = {t.fpl_team_id: t for t in db.scalars(select(Team).where(Team.fpl_season == FPL_SEASON))}
    if len(teams) != 20 or set(teams) != set(source_teams):
        raise ValueError('Existing clubs must match all 20 official FPL clubs')
    players = {p.fpl_player_id: p for p in db.scalars(select(Player).where(Player.fpl_season == FPL_SEASON))}
    source_ids = {p['fpl_player_id'] for p in roster}
    fixtures = list(db.scalars(select(Fixture).where(Fixture.season == SEASON)))
    by_pair = {(f.home_team_id, f.away_team_id): f for f in fixtures}
    if len(fixtures) != 380 or len(by_pair) != 380:
        raise ValueError('Existing season must contain 380 unique fixtures')
    official = {f['id']: f for f in payloads['fixtures']}
    mapped = {}
    for fid, source in official.items():
        pair = (teams[source['team_h']].id, teams[source['team_a']].id)
        fixture = by_pair.get(pair)
        if fixture is None or fixture.fpl_fixture_id not in (None, fid):
            raise ValueError('Conflicting official fixture identity')
        if source['finished'] and (source['team_h_score'] is None or source['team_a_score'] is None):
            raise ValueError('Finished fixture is missing a score')
        mapped[fid] = fixture
    historical = defaultdict(dict)
    for name, history in payloads.items():
        if not name.startswith('player-'):
            continue
        pid = int(name.split('-')[1])
        for row in history['history']:
            source = official.get(row['fixture'])
            if source is None or row['round'] != source['event']:
                raise ValueError('Historical player fixture/gameweek mismatch')
            represented = source['team_h'] if row['was_home'] else source['team_a']
            opponent = source['team_a'] if row['was_home'] else source['team_h']
            if row['opponent_team'] != opponent:
                raise ValueError('Historical player opponent mismatch')
            historical[source['id']][pid] = represented
    stat_rows = {gw: build_stat_rows(payloads[f'event-{gw}'], official, source_ids | set(players), gw, historical)
                 for gw in range(1, through_gameweek + 1)}
    preview = {'season': FPL_SEASON, 'through_gameweek': through_gameweek,
               'roster_players': len(roster), 'new_players': len(source_ids - set(players)),
               'fixtures_refreshed': len(mapped),
               'finished_fixtures': sum(bool(f['finished']) for f in official.values()),
               'gameweek_6_finished': sum(f['event'] == 6 and f['finished'] for f in official.values()),
               'official_stat_rows': sum(map(len, stat_rows.values())),
               'unassigned_historical_club_rows': sum(r['fpl_team_id'] is None for rows in stat_rows.values() for r in rows),
               'observed_at': observed_at.isoformat()}
    if not apply:
        return {'mode': 'preview', **preview}
    # Caller commits once, after all sources and identities have been validated.
    raw_players = {p['id']: p for p in payloads['bootstrap']['elements']}
    for item in roster:
        pid = item['fpl_player_id']
        player = players.get(pid)
        if player is None:
            player = Player(fpl_player_id=pid, fpl_season=FPL_SEASON)
            db.add(player)
            players[pid] = player
        raw = raw_players[pid]
        player.name = item['name']
        player.team_id = teams[item['fpl_team_id']].id
        player.position = player.fpl_position = item['position']
        player.price_tenths = item['price_tenths']
        player.fpl_price_gameweek = None
        player.price_updated_at = observed_at
        player.availability_status = raw.get('status')
        player.chance_of_playing = raw.get('chance_of_playing_next_round')
    db.flush()
    # Retain old players for historical foreign keys, but exclude unavailable ones from buying.
    for pid, player in players.items():
        if pid not in source_ids:
            player.availability_status = 'u'
    observed_snapshots = set(db.execute(select(PlayerPriceSnapshot.player_id).where(PlayerPriceSnapshot.observed_at == observed_at)).scalars())
    for item in roster:
        player = players[item['fpl_player_id']]
        if player.id not in observed_snapshots:
            db.add(PlayerPriceSnapshot(player_id=player.id, team_id=player.team_id, position=player.position,
                      price_tenths=player.price_tenths, observed_at=observed_at, source='official_fpl_bootstrap'))
    for fid, fixture in mapped.items():
        source = official[fid]
        fixture.fpl_fixture_id = fid
        fixture.gameweek = source['event']
        if source.get('kickoff_time'):
            fixture.fixture_date = datetime.fromisoformat(source['kickoff_time'].replace('Z', '+00:00')).astimezone(timezone.utc).replace(tzinfo=None)
        fixture.status = 'FT' if source['finished'] else ('LIVE' if source['started'] else 'NS')
        fixture.home_score = source['team_h_score']
        fixture.away_score = source['team_a_score']
    existing = {(s.player_id, s.fixture_id): s for s in db.scalars(select(FPLMatchStat).join(Fixture).where(Fixture.season == SEASON))}
    api_stats = {(s.player_id, s.fixture_id): s for s in db.scalars(select(PlayerMatchStat).join(Fixture).where(Fixture.season == SEASON))}
    imports = {s.gameweek: s for s in db.scalars(select(FPLImport).where(FPLImport.season == SEASON))}
    backfilled_clubs = 0
    for gw, rows in stat_rows.items():
        for row in rows:
            player = players[row['fpl_player_id']]
            fixture = mapped[row['fpl_fixture_id']]
            key = (player.id, fixture.id)
            stat = existing.get(key)
            if stat is None:
                stat = FPLMatchStat(player_id=player.id, fixture_id=fixture.id)
                db.add(stat)
            stat.team_id = teams[row['fpl_team_id']].id if row['fpl_team_id'] is not None else None
            stat.minutes, stat.total_points, stat.stats = row['minutes'], row['total_points'], row['stats']
            stat.observed_at = observed_at
            old = api_stats.get(key)
            if old and stat.team_id is not None and old.team_id is None:
                old.team_id = stat.team_id
                backfilled_clubs += 1
        record = imports.get(gw)
        if record is None:
            record = FPLImport(season=SEASON, gameweek=gw)
            db.add(record)
        record.source_sha256 = manifest['sources'][f'event-{gw}']['sha256']
        record.observed_at = observed_at
        record.player_count = len(payloads[f'event-{gw}']['elements'])
        record.fixture_count = len({r['fpl_fixture_id'] for r in rows})
    db.flush()
    return {'mode': 'applied', **preview, 'api_stat_clubs_backfilled': backfilled_clubs}
