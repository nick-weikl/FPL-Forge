import os
os.environ.setdefault('DATABASE_URL', 'sqlite://')
import unittest
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routes.recommendations import router
from app.schemas.recommendation import TransferStrategyRequest
from pydantic import ValidationError


class SellingPricesHTTPTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(router)
        self.client = TestClient(app)
        self.payload = {
            'current_gameweek': 7, 'free_transfers': 0, 'bank_tenths': 1,
            'owned_player_ids': list(range(1119, 1134)),
            'starting_player_ids': list(range(1119, 1130)),
            'bench_player_ids': list(range(1130, 1134)),
            'captain_id': 1119, 'vice_captain_id': 1120,
            'selling_prices_tenths': {str(pid): price for pid, price in zip(range(1119, 1134), [45,49,52,57,50,50,55,66,97,55,49,79,156,78,60])},
        }

    def test_entered_selling_values_reach_strategy_as_integer_ids(self):
        with patch('app.routes.recommendations.get_transfer_strategy', return_value={'accepted': True}) as strategy:
            response = self.client.post('/api/recommendations/strategy', json=self.payload)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(strategy.call_args.kwargs['selling_prices_tenths'],
                         {int(key): price for key, price in self.payload['selling_prices_tenths'].items()})
        self.assertEqual(strategy.call_args.kwargs['free_transfers'], 0)
        self.assertEqual(strategy.call_args.kwargs['bank_tenths'], 1)

    def test_blank_selling_values_still_use_defaults(self):
        self.payload['selling_prices_tenths'] = {}
        with patch('app.routes.recommendations.get_transfer_strategy', return_value={'accepted': True}):
            self.assertEqual(self.client.post('/api/recommendations/strategy', json=self.payload).status_code, 200)

    def test_invalid_keys_and_non_integer_prices_still_fail(self):
        for selling in [{'1119': -1}, {'1119': 45.5}, {'1119': '45'}, {'1119': True}, {'9999': 45}, {'1119.0':45}, {'01119':45}, {'name':45}, {'0':45}]:
            with self.subTest(selling=selling), patch('app.routes.recommendations.get_transfer_strategy') as strategy:
                response = self.client.post('/api/recommendations/strategy', json=self.payload | {'selling_prices_tenths': selling})
                self.assertEqual(response.status_code, 422, response.text)
                strategy.assert_not_called()

    def test_normalization_does_not_allow_duplicate_python_keys(self):
        with self.assertRaises(ValidationError):
            TransferStrategyRequest.model_validate(self.payload | {'selling_prices_tenths': {1119:45, '1119':46}})
