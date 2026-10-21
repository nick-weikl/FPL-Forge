import os
os.environ.setdefault('DATABASE_URL', 'sqlite://')
import unittest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.database import Base
from app.models import Team, Player, Fixture
from app.models.fpl_data import FPLImport, FPLMatchStat
from app.services.dashboard_service import get_dashboard


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://')
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.db.add_all([Team(id=1,name='Club A',short_name='AAA',fpl_season='2026/27'),Team(id=2,name='Club B',short_name='BBB',fpl_season='2026/27'),Team(id=3,name='Old club',fpl_season='2025/26'),Team(id=4,name='Club C',short_name='CCC',fpl_season='2026/27')])
        self.db.add_all([Player(id=1,name='Scorer',team_id=1,position='Attacker',fpl_season='2026/27',price_tenths=79),Player(id=2,name='No history',team_id=2,position='Defender',fpl_season='2026/27',price_tenths=40),Player(id=3,name='Old player',team_id=3,position='Defender',fpl_season='2025/26',price_tenths=45)])
        self.db.add_all([Fixture(id=1,external_api_id=1,season=2026,gameweek=1,status='FT',fixture_date=datetime(2026,8,1),home_team_id=1,away_team_id=2,home_score=1,away_score=0),Fixture(id=2,external_api_id=2,season=2026,gameweek=7,status='FT',fixture_date=datetime(2026,10,17),home_team_id=2,away_team_id=1,home_score=0,away_score=2),Fixture(id=3,external_api_id=3,season=2026,gameweek=8,status='NS',fixture_date=datetime(2026,10,24),home_team_id=1,away_team_id=4),Fixture(id=4,external_api_id=4,season=2025,gameweek=1,status='FT',fixture_date=datetime(2025,8,1),home_team_id=1,away_team_id=2,home_score=9,away_score=0)])
        self.db.flush()
        for gw in [1,7]:
            self.db.add(FPLImport(season=2026,gameweek=gw,source_sha256='0'*64,observed_at=datetime.now(timezone.utc),player_count=1,fixture_count=1))
        for fid,points,minutes,goals in [(1,5,90,1),(2,10,75,2),(4,99,90,9)]:
            self.db.add(FPLMatchStat(player_id=1,fixture_id=fid,minutes=minutes,total_points=points,stats={'goals_scored':goals,'assists':1},observed_at=datetime.now(timezone.utc)))
        self.db.commit()

    def tearDown(self):
        self.db.close();self.engine.dispose()

    def test_actual_stats_prices_and_season_scope(self):
        result=get_dashboard(self.db)
        self.assertEqual(result['latest_completed_gameweek'],7)
        self.assertEqual(result['next_gameweek'],8)
        self.assertEqual(len(result['teams']),3)
        self.assertEqual(len(result['fixtures']),3)
        p=next(p for p in result['players'] if p['id']==1)
        self.assertEqual((p['points'],p['goals'],p['minutes'],p['price_tenths']),(10,2,75,79))
        self.assertEqual(p['recent_minutes'][-1],{'gameweek':7,'minutes':75})
        self.assertIsNone(next(p for p in result['players'] if p['id']==2)['points'])
        self.assertTrue(all(f['fixture_date'].endswith('Z') for f in result['fixtures']))

    def test_season_window_and_season_end(self):
        result=get_dashboard(self.db,38)
        self.assertEqual(next(p for p in result['players'] if p['id']==1)['points'],15)
        self.db.query(Fixture).filter(Fixture.id==3).delete();self.db.commit()
        self.assertIsNone(get_dashboard(self.db)['next_gameweek'])

    def test_empty_history_keeps_unknown_values(self):
        self.db.query(FPLImport).delete();self.db.commit()
        result=get_dashboard(self.db)
        self.assertIsNone(result['latest_completed_gameweek'])
        self.assertTrue(all(p['points'] is None for p in result['players']))
        self.assertTrue(all(f['home_difficulty'] is None for f in result['fixtures']))
