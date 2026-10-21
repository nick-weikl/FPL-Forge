"""Read-only database view shared by the frontend's overview and research pages."""
from collections import defaultdict
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from app.models import Player, Team, Fixture
from app.models.fpl_data import FPLMatchStat, FPLImport
from app.services.football_api import SEASON
from app.services.fpl_price_service import FPL_SEASON
from app.services.fixture_difficulty_service import get_all_team_strengths, get_fixture_difficulty
from app.services.data_quality_service import get_data_quality


def get_dashboard(db, lookback_gameweeks=5):
    latest = db.scalar(select(func.max(FPLImport.gameweek)).where(FPLImport.season == SEASON))
    start = max(1, (latest or 1) - lookback_gameweeks + 1)
    teams = list(db.scalars(select(Team).where(Team.fpl_season == FPL_SEASON).order_by(Team.name)))
    players = list(db.scalars(select(Player).options(joinedload(Player.team)).where(Player.fpl_season == FPL_SEASON)))
    fixtures = list(db.scalars(select(Fixture).where(Fixture.season == SEASON).order_by(Fixture.fixture_date, Fixture.id)))
    totals = defaultdict(lambda: {'minutes': 0, 'goals': 0, 'assists': 0, 'points': 0, 'matches': 0})
    recent = defaultdict(lambda: defaultdict(int))
    # One batched history query, rather than a request or query per player.
    if latest is not None:
        rows = db.execute(select(FPLMatchStat, Fixture.gameweek).join(Fixture).where(
            Fixture.season == SEASON, Fixture.status == 'FT',
            Fixture.gameweek.between(start, latest))).all()
        for stat, gameweek in rows:
            total = totals[stat.player_id]
            total['minutes'] += stat.minutes
            total['goals'] += stat.stats.get('goals_scored', 0)
            total['assists'] += stat.stats.get('assists', 0)
            total['points'] += stat.total_points
            total['matches'] += 1
            recent[stat.player_id][gameweek] += stat.minutes
    strengths = get_all_team_strengths(latest or 0, db=db)
    difficulty = {}
    for team in teams:
        attack = get_fixture_difficulty(team.id, 'MID', latest or 0, team_strengths=strengths, db=db)
        defense = get_fixture_difficulty(team.id, 'GK', latest or 0, team_strengths=strengths, db=db)
        difficulty[team.id] = None if 'error' in attack or 'error' in defense else round(
            (attack['difficulty_score'] + defense['difficulty_score']) / 2)
    upcoming = [f.gameweek for f in fixtures if f.status != 'FT' and f.gameweek is not None
                and (latest is None or f.gameweek > latest)]
    return {
        'season': FPL_SEASON, 'latest_completed_gameweek': latest,
        'next_gameweek': min(upcoming) if upcoming else None,
        'window': {'start': start if latest else None, 'end': latest, 'gameweeks': lookback_gameweeks},
        'data_quality': get_data_quality(db),
        'difficulty_description': 'Estimated from opponent goals scored and conceded in stored results; 1 is easier and 5 is harder. This is not official FPL difficulty.',
        'teams': [{'id': t.id, 'name': t.name, 'short_name': t.short_name or t.name[:3].upper()} for t in teams],
        'fixtures': [{'id': f.id, 'gameweek': f.gameweek,
                      'fixture_date': f.fixture_date.isoformat() + 'Z',
                      'status': f.status, 'home_team_id': f.home_team_id, 'away_team_id': f.away_team_id,
                      'home_score': f.home_score, 'away_score': f.away_score,
                      'home_difficulty': difficulty.get(f.away_team_id),
                      'away_difficulty': difficulty.get(f.home_team_id)} for f in fixtures],
        'players': [{
            'id': p.id, 'external_api_id': p.external_api_id, 'name': p.name,
            'team_id': p.team_id, 'team_name': p.team.name, 'position': p.position,
            'price_tenths': p.price_tenths, 'price_updated_at': p.price_updated_at,
            'availability_status': p.availability_status,
            'has_stats': p.id in totals,
            'minutes': totals[p.id]['minutes'] if p.id in totals else None,
            'goals': totals[p.id]['goals'] if p.id in totals else None,
            'assists': totals[p.id]['assists'] if p.id in totals else None,
            'points': totals[p.id]['points'] if p.id in totals else None,
            'points_per_match': round(totals[p.id]['points'] / totals[p.id]['matches'], 2) if p.id in totals else None,
            'recent_minutes': [{'gameweek': gw, 'minutes': recent[p.id].get(gw)}
                               for gw in range(max(start, (latest or 1) - 4), (latest or 0) + 1)]
        } for p in sorted(players, key=lambda p: p.name)]
    }
