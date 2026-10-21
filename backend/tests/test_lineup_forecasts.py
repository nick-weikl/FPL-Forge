import os
os.environ.setdefault('DATABASE_URL', 'sqlite://')
import unittest
from collections import Counter
from unittest.mock import patch
from pydantic import ValidationError
from app.schemas.recommendation import TransferStrategyRequest
from app.services.recommendation_service import configure_lineup, single_options, double_options, lineup_breakdown, get_transfer_strategy


def player(pid, position, points=10, price=50):
    return dict(player_id=pid, name=f'Player {pid}', position=position, team_id=pid, team_name='Club',
                overall_score=points, expected_points=points, price_tenths=price, can_buy=True,
                gameweek_points={8:points / 2, 9:points / 2})


def fixture_context():
    roles = ['Goalkeeper'] * 2 + ['Defender'] * 5 + ['Midfielder'] * 5 + ['Attacker'] * 3
    owned = [player(i + 1, role) for i, role in enumerate(roles)]
    incoming = [player(20, 'Defender', 20), player(21, 'Midfielder', 30), player(22, 'Attacker', 20)]
    return dict(owned=owned, owned_ids={p['player_id'] for p in owned}, bank=0,
                selling={p['player_id']:50 for p in owned}, team_counts=Counter(p['team_id'] for p in owned),
                by_id={p['player_id']:p for p in owned + incoming},
                rankings={role:sorted([p for p in incoming if p['position']==role],key=lambda p:-p['overall_score']) for role in roles},
                warnings=[], model='test', score_units='expected_fpl_points', horizon_gameweeks=2,
                lookback_gameweeks=[3,7], data_quality={}, selling_price_assumptions=[])

STARTERS = [1,3,4,5,8,9,10,11,13,14,15]
BENCH = [2,6,7,12]

class LineupForecastTests(unittest.TestCase):
    def setUp(self):
        self.context = fixture_context()
        self.assertIsNone(configure_lineup(self.context, STARTERS, BENCH, 13, 14))

    def test_bench_upgrade_has_no_starter_gain(self):
        moves = single_options(self.context)
        self.assertTrue(moves)
        self.assertFalse(any(m['player_out']['player_id'] in BENCH for m in moves))
        projection = lineup_breakdown(self.context,[{'player_out': {'player_id':12}, 'player_in': {'player_id':21}}],0)
        self.assertEqual(projection['net_gain'],0)
        self.assertEqual(projection['before_points'],120)
        self.assertEqual(projection['after_points'],120)

    def test_captain_gain_counts_twice_and_hits_apply_once(self):
        move = next(m for m in single_options(self.context) if m['player_out']['player_id']==13)
        self.assertEqual(move['score_gain'],20)
        projection = lineup_breakdown(self.context,[move],4)
        self.assertEqual(projection['after_points'],140)
        self.assertEqual(projection['net_gain'],16)
        self.assertEqual([r['transfer_hit'] for r in projection['gameweeks']],[4,0])
        self.assertEqual(sum(r['net_gain'] for r in projection['gameweeks']),16)

    def test_cheap_bench_enabler_funds_a_starter_without_scoring(self):
        c = self.context
        cheap = player(30,'Defender',0,10)
        expensive = player(31,'Attacker',40,90)
        c['rankings']={'Defender':[cheap], 'Attacker':[expensive]}
        c['by_id'].update({30:cheap,31:expensive})
        best=double_options(c)[0]
        self.assertEqual(best['combined_score_gain'],60)
        self.assertEqual({m['player_in']['player_id'] for m in best['transfers']},{30,31})
        self.assertEqual(lineup_breakdown(c,best['transfers'],4)['net_gain'],56)
        self.assertEqual(next(m for m in best['transfers'] if m['player_in']['player_id']==30)['score_gain'],0)

    def test_invalid_formations_and_captains_rejected(self):
        for starters, bench, captain, vice in [(STARTERS,BENCH,13,13),(STARTERS,BENCH,12,13),
                ([1,3,4,8,9,10,11,12,13,14,15],[2,5,6,7],13,14),
                (STARTERS,[6,2,7,12],13,14),(STARTERS,[2,6,7,7],13,14)]:
            self.assertIn('error',configure_lineup(fixture_context(),starters,bench,captain,vice))

    def test_strategy_ranking_and_breakdown_agree(self):
        with patch('app.services.recommendation_service.prepare_context',return_value=fixture_context()):
            result=get_transfer_strategy(7,list(range(1,16)),free_transfers=0,starting_player_ids=STARTERS,bench_player_ids=BENCH,captain_id=13,vice_captain_id=14)
        for key in ['single_transfer','double_transfer']:
            self.assertEqual(result[key]['net_score_gain'],result[key]['projection']['net_gain'])
        self.assertEqual(result['baseline']['after_points'],120)
        self.assertTrue(any('automatic substitutions' in w for w in result['warnings']))

    def test_blank_and_double_gameweek_breakdown(self):
        c=self.context
        for record in c['by_id'].values(): record['gameweek_points']={8:0,9:record['overall_score']}
        self.assertEqual([row['after_points'] for row in lineup_breakdown(c,[],0)['gameweeks']],[0,120])

    def test_request_lineup_and_captain_validation(self):
        payload=dict(current_gameweek=7,owned_player_ids=list(range(1,16)),starting_player_ids=STARTERS,bench_player_ids=BENCH,captain_id=13,vice_captain_id=14)
        self.assertEqual(TransferStrategyRequest(**payload).captain_id,13)
        for changes in [dict(starting_player_ids=STARTERS[:-1]),dict(bench_player_ids=[2,6,7,7]),dict(captain_id=12),dict(vice_captain_id=13),dict(captain_id=True)]:
            with self.assertRaises(ValidationError): TransferStrategyRequest(**(payload | changes))
