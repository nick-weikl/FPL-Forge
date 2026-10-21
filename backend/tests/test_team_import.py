import os
os.environ.setdefault('DATABASE_URL', 'sqlite://')
import copy
import unittest
from datetime import datetime, timezone
from unittest.mock import patch, Mock
import requests
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.models import Player, Team
from app.models.fpl_data import FPLImport
from app.services.team_import_service import preview_team_import, fetch_public_json
from app.routes.team_import import router


class TeamImportTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread':False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.db.add_all([Team(id=i,name=f'Club {i}',fpl_season='2026/27') for i in range(1,6)])
        positions=['Goalkeeper']*2+['Defender']*5+['Midfielder']*5+['Attacker']*3
        for index,position in enumerate(positions):
            self.db.add(Player(id=index+11,fpl_player_id=index+101,fpl_season='2026/27',name=f'Player {index}',team_id=index//3+1,position=position,price_tenths=100))
        self.db.add(FPLImport(season=2026,gameweek=7,source_sha256='0'*64,observed_at=datetime.now(timezone.utc),player_count=15,fixture_count=10))
        self.db.commit()
        self.bootstrap={'events':[{'id':1,'deadline_time':'2026-08-01T10:00:00Z'}, {'id':7,'deadline_time':'2026-10-17T10:00:00Z'}, {'id':8,'deadline_time':'2099-10-24T10:00:00Z'}]}
        self.entry={'id':123,'name':'My imported team','current_event':7}
        self.picks={'entry_history':{'event':7,'bank':0},'picks':[{'element':i+101,'position':i+1} for i in range(15)]}
        app=FastAPI();app.include_router(router)
        app.dependency_overrides[get_db]=lambda:self.db
        self.client=TestClient(app)

    def tearDown(self):
        self.db.close();self.engine.dispose()

    def fetch(self):
        return patch('app.services.team_import_service.fetch_public_json',side_effect=[copy.deepcopy(self.bootstrap),copy.deepcopy(self.entry),copy.deepcopy(self.picks)])

    def test_public_http_preview_maps_fpl_ids_and_preserves_recorded_bank(self):
        before=self.db.scalar(select(func.count()).select_from(Player))
        with self.fetch() as fetch:
            response=self.client.get('/api/fpl/teams/123/preview')
        self.assertEqual(response.status_code,200,response.text)
        result=response.json()
        self.assertEqual(result['bank_tenths'],0)
        self.assertEqual(result['gameweek'],7)
        self.assertEqual(result['analysis_gameweek'],7)
        self.assertEqual([p['id'] for p in result['players']],list(range(11,26)))
        self.assertEqual(sum(p['price_tenths'] for p in result['players']),1500)
        self.assertEqual(self.db.scalar(select(func.count()).select_from(Player)),before)
        self.assertEqual(fetch.call_args_list[-1].args[0],'entry/123/event/7/picks/')
        self.assertTrue(any('selling' in warning for warning in result['warnings']))

    def test_missing_player_blocks_partial_import(self):
        self.db.query(Player).filter(Player.id==11).delete();self.db.commit()
        with self.fetch():response=self.client.get('/api/fpl/teams/123/preview')
        self.assertEqual(response.status_code,409)
        self.assertEqual(response.json()['detail']['missing_fpl_player_ids'],[101])

    def test_malformed_squad_and_bank_fail(self):
        for corruption in ['duplicate','short','bank','event']:
            with self.subTest(corruption=corruption):
                old=copy.deepcopy(self.picks)
                if corruption=='duplicate':self.picks['picks'][1]['element']=101
                elif corruption=='short':self.picks['picks'].pop()
                elif corruption=='bank':self.picks['entry_history']['bank']=-1
                else:self.picks['entry_history']['event']=6
                with self.fetch():response=self.client.get('/api/fpl/teams/123/preview')
                self.assertEqual(response.status_code,502)
                self.picks=old

    def test_not_started_team_and_season_mismatch(self):
        self.entry['current_event']=None
        with self.fetch():self.assertEqual(self.client.get('/api/fpl/teams/123/preview').status_code,409)
        self.entry['current_event']=7;self.bootstrap['events'][0]['deadline_time']='2025-08-01T10:00:00Z'
        with self.fetch():self.assertEqual(self.client.get('/api/fpl/teams/123/preview').status_code,409)

    def test_invalid_id_never_reaches_provider(self):
        with patch('app.services.team_import_service.fetch_public_json') as fetch:
            for id in ['0','-1','abc','2147483648']:
                self.assertEqual(self.client.get(f'/api/fpl/teams/{id}/preview').status_code,422)
            fetch.assert_not_called()

    def test_older_backend_data_is_explicit(self):
        self.db.query(FPLImport).update({'gameweek':6});self.db.commit()
        with self.fetch():result=preview_team_import(self.db,123)
        self.assertEqual(result['analysis_gameweek'],6)
        self.assertTrue(any('match data' in warning for warning in result['warnings']))


class PublicProviderFailureTests(unittest.TestCase):
    def test_timeout_and_not_found_are_actionable(self):
        with patch('app.services.team_import_service.requests.get',side_effect=requests.Timeout):
            with self.assertRaises(HTTPException) as error:fetch_public_json('entry/123/')
            self.assertEqual(error.exception.status_code,504)
        with patch('app.services.team_import_service.requests.get',return_value=Mock(status_code=404)):
            with self.assertRaises(HTTPException) as error:fetch_public_json('entry/123/')
            self.assertEqual(error.exception.status_code,404)
