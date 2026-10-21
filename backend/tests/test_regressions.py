import os
os.environ['DATABASE_URL'] = 'sqlite://'
import unittest
from collections import Counter
from unittest.mock import patch
from datetime import datetime, timezone
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from pydantic import ValidationError
from app.database import Base
from app.models import Team, Player, Fixture, PlayerMatchStat
from app.models.fpl_data import FPLImport, FPLMatchStat
from app.schemas.recommendation import TransferStrategyRequest
from app.services.player_analytics_service import get_player_summary
from app.services.player_scoring_service import calculate_fixture_score
from app.services.fixture_difficulty_service import get_all_team_strengths
from app.services.recommendation_service import single_options, double_options, build_strategy_reason, get_transfer_strategy
from app.services.fpl_import_service import build_stat_rows
from app.services.fpl_forecast_service import build_forecasts


def record(pid, team, score, price=50, position='Midfielder'):
    return dict(player_id=pid, team_id=team, overall_score=score, price_tenths=price,
                name=f'Player {pid}', team_name=f'Team {team}', position=position, can_buy=True)


def context(owned, incoming, bank=0):
    return {'owned': owned, 'owned_ids': {p['player_id'] for p in owned},
            'bank': bank, 'selling': {p['player_id']: p['price_tenths'] for p in owned},
            'team_counts': Counter(p['team_id'] for p in owned),
            'rankings': {pos: sorted([p for p in incoming if p['position']==pos], key=lambda p: -p['overall_score'])
                         for pos in {p['position'] for p in incoming}}}


class QueryRegressionTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://')
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.db.add_all([Team(id=1, name='A', fpl_season='2026/27'), Team(id=2, name='B', fpl_season='2026/27')])
        self.db.add(Player(id=1, name='P', team_id=1, position='Midfielder', fpl_position='Midfielder', fpl_season='2026/27',
                           price_tenths=50, availability_status='a', price_updated_at=datetime.now(timezone.utc)))
        self.db.add_all([Fixture(id=1, external_api_id=11, season=2026, gameweek=1, fixture_date=datetime(2026,8,1),
                                status='FT', home_team_id=1, away_team_id=2, home_score=1, away_score=0),
                         Fixture(id=2, external_api_id=12, season=2025, gameweek=1, fixture_date=datetime(2025,8,1),
                                status='FT', home_team_id=1, away_team_id=2, home_score=9, away_score=0)])
        self.db.flush()
        self.db.add_all([PlayerMatchStat(player_id=1, fixture_id=1, minutes=90, goals=1),
                         PlayerMatchStat(player_id=1, fixture_id=2, minutes=90, goals=9)])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_summary_join_and_season(self):
        result = get_player_summary(1, 1, db=self.db)
        self.assertNotIn('error', result)
        self.assertEqual(result['total_goals'], 1)
        self.assertEqual(result['total_minutes'], 90)

    def test_team_strength_is_season_scoped(self):
        result = get_all_team_strengths(1, db=self.db)
        self.assertEqual(result[0]['total_goals_scored'], 1)
        self.assertEqual(result[0]['matches_played'], 1)

    def test_empty_fixture_score(self):
        self.assertEqual(calculate_fixture_score(None), 0)

    def test_missing_official_history_is_explicit(self):
        result = build_forecasts(self.db, 1)
        self.assertIn('error', result)
        self.assertEqual(result['missing_gameweeks'], [1])

    def test_forecast_points_and_dnp_denominator(self):
        self.db.add(FPLImport(season=2026, gameweek=1, source_sha256='0'*64, observed_at=datetime.now(timezone.utc), player_count=1, fixture_count=1))
        self.db.add(FPLMatchStat(player_id=1, fixture_id=1, minutes=90, total_points=5, stats={}, observed_at=datetime.now(timezone.utc)))
        self.db.add(Fixture(id=3, external_api_id=13, season=2026, gameweek=2, fixture_date=datetime(2026,8,9), status='NS', home_team_id=2, away_team_id=1))
        self.db.commit()
        result = build_forecasts(self.db, 1)
        self.assertEqual(result['by_id'][1]['expected_points'], 5)
        self.assertEqual(result['score_units'], 'expected_fpl_points')


class RequestTests(unittest.TestCase):
    def test_bounds_duplicates_and_selling_ids(self):
        base = {'current_gameweek': 6, 'owned_player_ids': list(range(1,16))}
        for changes in [dict(current_gameweek=-1), dict(current_gameweek=39), dict(bank_tenths=-1),
                        dict(free_transfers=-1), dict(free_transfers=6), dict(candidates_per_player=0),
                        dict(owned_player_ids=[1]*15), dict(selling_prices_tenths={20:50}),
                        dict(current_gameweek=True)]:
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                TransferStrategyRequest(**(base | changes))

    def test_json_selling_price_keys(self):
        import json
        value = TransferStrategyRequest.model_validate_json(json.dumps(dict(current_gameweek=6, owned_player_ids=list(range(1,16)), selling_prices_tenths={'1':45})))
        self.assertEqual(value.selling_prices_tenths, {1:45})


class OptimizerTests(unittest.TestCase):
    def test_cheap_enabler_beyond_old_top_ten(self):
        owned = [record(1, 1, 10), record(2, 2, 10, position='Attacker')]
        incoming = [record(100+i, 3, 30-i/10, price=90) for i in range(12)]
        incoming += [record(200, 3, 1, price=10), record(300, 4, 40, price=90, position='Attacker')]
        result = double_options(context(owned, incoming))
        self.assertEqual({m['player_in']['player_id'] for m in result[0]['transfers']}, {200,300})
        self.assertEqual(result[0]['combined_score_gain'], 21)

    def test_distinct_incoming_and_club_limit(self):
        owned = [record(1, 1, 1), record(2, 1, 1), record(3, 1, 1)]
        incoming = [record(4,1,10), record(5,1,9), record(6,2,8)]
        for pair in double_options(context(owned,incoming)):
            ids = [m['player_in']['player_id'] for m in pair['transfers']]
            self.assertEqual(len(set(ids)),2)
        self.assertTrue(all(m['player_in']['player_id'] not in {1,2,3} for m in single_options(context(owned,incoming))))

    def test_actual_selling_value_controls_budget(self):
        c = context([record(1,1,1,70)], [record(2,2,10,70)])
        c['selling'][1] = 60
        self.assertEqual(single_options(c), [])

    def test_reason_when_only_single_exists(self):
        single = {'raw_score_gain': 2, 'net_score_gain': 2, 'transfer': {'player_out': {'name':'A'},'player_in':{'name':'B'}}}
        self.assertIn('2.00', build_strategy_reason('single_transfer',single,None)['decision_detail'])

    def test_point_hits_and_ties(self):
        c = {'model':'test','score_units':'expected_fpl_points','horizon_gameweeks':5,'lookback_gameweeks':[1,5],
             'warnings':[],'data_quality':{},'selling_price_assumptions':[]}
        single = {'score_gain':5}
        double = {'combined_score_gain':8}
        with patch('app.services.recommendation_service.prepare_context',return_value=c), \
             patch('app.services.recommendation_service.single_options',return_value=[single]), \
             patch('app.services.recommendation_service.double_options',return_value=[double]), \
             patch('app.services.recommendation_service.build_strategy_reason',return_value={}):
            self.assertEqual(get_transfer_strategy(5,[],free_transfers=1)['recommended_strategy'],'single_transfer')
            self.assertEqual(get_transfer_strategy(5,[],free_transfers=2)['recommended_strategy'],'double_transfer')


class ImportValidationTests(unittest.TestCase):
    def fixture(self):
        return {1: {'id':1,'event':6,'finished':True,'team_h':1,'team_a':2,
                    'stats':[{'identifier':'bps','h':[{'element':10,'value':20}],'a':[]}]}}

    def element(self):
        return {'elements':[{'id':10,'stats':{'minutes':90,'total_points':2},
                'explain':[{'fixture':1,'stats':[{'identifier':'minutes','value':90,'points':2}]}]}]}

    def test_fixture_identity_and_historical_club(self):
        rows = build_stat_rows(self.element(),self.fixture(),{10},6)
        self.assertEqual(rows[0]['fpl_team_id'],1)
        with self.assertRaises(ValueError):
            build_stat_rows(self.element(),self.fixture(),{10},7)

    def test_reject_unmapped_and_bad_points(self):
        with self.assertRaises(ValueError):
            build_stat_rows(self.element(),self.fixture(),set(),6)
        payload = self.element(); payload['elements'][0]['stats']['total_points'] = 99
        with self.assertRaises(ValueError):
            build_stat_rows(payload,self.fixture(),{10},6)


if __name__ == '__main__':
    unittest.main()
