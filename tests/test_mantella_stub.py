"""
Tests for Mantella native server on Linux with Stub LLM and Stub TTS.
Verifies all SKSE HTTP protocol endpoints:
- mantella_initialize
- mantella_start_conversation
- mantella_continue_conversation
- mantella_player_input
- mantella_end_conversation
"""

import os
import sys
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "upstream", "Mantella"))

from src.setup import MantellaSetup
from src.http.routes.mantella_route import mantella_route
from src.http.communication_constants import communication_constants as c


@pytest.fixture(scope="module")
def api_client():
    setup = MantellaSetup()
    config, language_info = setup.initialise(
        config_file='config.ini',
        logging_file='logging.log',
        language_file=os.path.join(REPO_ROOT, "upstream", "Mantella", "data", "language_support.csv"),
        mantella_version='0.14'
    )
    route = mantella_route(config=config, language_info=language_info)
    app = FastAPI()
    route.add_route_to_server(app)
    return TestClient(app)


def test_mantella_initialize(api_client):
    res = api_client.post('/mantella', json={c.KEY_REQUESTTYPE: c.KEY_REQUESTTYPE_INIT})
    assert res.status_code == 200
    data = res.json()
    assert data.get(c.KEY_REPLYTYPE) == c.KEY_REPLYTTYPE_INITCOMPLETED


def test_mantella_conversation_flow(api_client):
    npc_actor = {
        c.KEY_ACTOR_BASEID: '112196',
        c.KEY_ACTOR_REFID: '112196',
        c.KEY_ACTOR_NAME: 'Sarkaar Bhaiya',
        c.KEY_ACTOR_GENDER: 0,
        c.KEY_ACTOR_RACE: 'Nord',
        c.KEY_ACTOR_VOICETYPE: 'MaleNord',
        c.KEY_ACTOR_ISINCOMBAT: False,
        c.KEY_ACTOR_ISENEMY: False,
        c.KEY_ACTOR_RELATIONSHIPRANK: 1,
        c.KEY_ACTOR_ISPLAYER: False,
    }
    player_actor = {
        c.KEY_ACTOR_BASEID: '20',
        c.KEY_ACTOR_REFID: '20',
        c.KEY_ACTOR_NAME: 'Prisoner',
        c.KEY_ACTOR_GENDER: 0,
        c.KEY_ACTOR_RACE: 'Nord',
        c.KEY_ACTOR_VOICETYPE: 'MaleNord',
        c.KEY_ACTOR_ISINCOMBAT: False,
        c.KEY_ACTOR_ISENEMY: False,
        c.KEY_ACTOR_RELATIONSHIPRANK: 0,
        c.KEY_ACTOR_ISPLAYER: True,
    }
    context = {
        c.KEY_CONTEXT_LOCATION: 'Whiterun Bannered Mare',
        c.KEY_CONTEXT_TIME: 14,
        c.KEY_CONTEXT_GAMEDAYS: 1.5,
        c.KEY_CONTEXT_WEATHER: 'Clear'
    }

    # 1. Start conversation
    res_start = api_client.post('/mantella', json={
        c.KEY_REQUESTTYPE: c.KEY_REQUESTTYPE_STARTCONVERSATION,
        c.KEY_INPUTTYPE: c.KEY_INPUTTYPE_TEXT,
        c.KEY_ACTORS: [npc_actor, player_actor],
        c.KEY_CONTEXT: context
    })
    assert res_start.status_code == 200
    assert res_start.json().get(c.KEY_REPLYTYPE) == c.KEY_REPLYTTYPE_STARTCONVERSATIONCOMPLETED

    # 2. Player Input
    res_input = api_client.post('/mantella', json={
        c.KEY_REQUESTTYPE: c.KEY_REQUESTTYPE_PLAYERINPUT,
        c.KEY_REQUESTTYPE_PLAYERINPUT: 'Pranaam Bhaiya ji!',
        c.KEY_CONTINUECONVERSATION_TOPICINFOFILE: 1,
        c.KEY_CONTEXT: context
    })
    assert res_input.status_code == 200
    assert res_input.json().get(c.KEY_REPLYTYPE) == c.KEY_REPLYTYPE_NPCTALK

    # 3. Continue conversation (receive spoken response)
    res_cont = api_client.post('/mantella', json={
        c.KEY_REQUESTTYPE: c.KEY_REQUESTTYPE_CONTINUECONVERSATION,
        c.KEY_CONTINUECONVERSATION_TOPICINFOFILE: 1,
        c.KEY_CONTEXT: context
    })
    assert res_cont.status_code == 200
    data_cont = res_cont.json()
    assert data_cont.get(c.KEY_REPLYTYPE) == c.KEY_REPLYTYPE_NPCTALK
    npc_talk = data_cont.get(c.KEY_REPLYTYPE_NPCTALK, {})
    assert npc_talk.get(c.KEY_ACTOR_SPEAKER) == 'Sarkaar Bhaiya'
    assert 'Bhaiyo aur behno' in npc_talk.get(c.KEY_ACTOR_LINETOSPEAK, '')
    assert npc_talk.get(c.KEY_ACTOR_DURATION) == 1.0

    # 4. End conversation
    res_end = api_client.post('/mantella', json={
        c.KEY_REQUESTTYPE: c.KEY_REQUESTTYPE_ENDCONVERSATION
    })
    assert res_end.status_code == 200
    assert res_end.json().get(c.KEY_REPLYTYPE) == c.KEY_REPLYTYPE_ENDCONVERSATION
