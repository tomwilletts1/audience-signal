import sys
import types
import json
from flask import Flask
import pytest

# Provide dummy openai module before importing project modules
class DummyChat:
    def __init__(self):
        self.completions = types.SimpleNamespace(create=lambda *args, **kwargs: types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="dummy"))]))

class DummyImage:
    def create(self, *args, **kwargs):
        return {'data': [{'url': 'http://example.com/image.png'}]}

dummy_openai = types.SimpleNamespace(chat=DummyChat(), Image=DummyImage())
sys.modules.setdefault('openai', dummy_openai)

from src.routes.analyze import create_analyze_blueprint
from src.routes.history import create_history_blueprint
from src.utils.history_manager import HistoryManager

# Fixtures -------------------------------------------------------------------
@pytest.fixture
def app(monkeypatch):
    # Patch service functions to avoid any external calls
    monkeypatch.setattr('src.services.persona.generate_persona_response', lambda message, persona_details, model=None, temperature=None: f"response for {persona_details}")
    monkeypatch.setattr('src.services.vision.analyze_image', lambda image_data, persona_details, model=None, temperature=None: "image response")
    monkeypatch.setattr('src.services.vision.analyze_combined', lambda image_data, message, persona_details, model=None, temperature=None: "combined response")

    history_manager = HistoryManager()
    flask_app = Flask(__name__)
    flask_app.register_blueprint(create_analyze_blueprint(history_manager))
    flask_app.register_blueprint(create_history_blueprint(history_manager))
    flask_app.config['TESTING'] = True
    return flask_app

@pytest.fixture
def client(app):
    return app.test_client()

# Tests ----------------------------------------------------------------------
def test_analyze_endpoint(client):
    payload = {
        'message': 'Hello',
        'personas': ['Test Persona']
    }
    response = client.post('/api/analyze', data=json.dumps(payload), content_type='application/json')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['results'][0]['response'] == 'response for Test Persona'

def test_history_endpoint(client):
    payload = {
        'message': 'Hello again',
        'personas': ['Persona']
    }
    client.post('/api/analyze', data=json.dumps(payload), content_type='application/json')
    history_resp = client.get('/api/history')
    assert history_resp.status_code == 200
    history = history_resp.get_json()
    assert isinstance(history, list)
    assert len(history) == 1
    assert history[0]['message'] == 'Hello again'
