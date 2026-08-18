"""
Comprehensive unit and integration tests for Flask REST API and routes.
"""

import json
import pytest
from griductive.core.models import Status


@pytest.mark.api
def test_index_route(client):
    """Test index HTML route."""
    rv = client.get('/')
    assert rv.status_code == 200
    assert b"Griductive" in rv.data or b"html" in rv.data.lower()


@pytest.mark.api
def test_list_puzzles(client):
    """Test GET /api/puzzles lists puzzles and excludes schema."""
    rv = client.get('/api/puzzles')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert 'puzzles' in data
    assert len(data['puzzles']) >= 7
    for p in data['puzzles']:
        assert 'filename' in p
        assert 'title' in p
        assert p['filename'] != 'puzzle_schema.json'


@pytest.mark.api
def test_load_puzzle_success(client):
    """Test POST /api/load with valid puzzle."""
    rv = client.post('/api/load', json={'filename': 'puzzle_01_3x3_easy.json'})
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data['grid_size'] == 3
    assert len(data['characters']) == 9
    assert len(data['revealed_clues']) > 0
    assert data['is_unique'] is True
    assert data['uniqueness_count'] == 1


@pytest.mark.api
def test_load_puzzle_nonexistent(client):
    """Test POST /api/load with nonexistent file returns 404."""
    rv = client.post('/api/load', json={'filename': 'nonexistent_puzzle.json'})
    assert rv.status_code == 404
    data = json.loads(rv.data)
    assert 'error' in data


@pytest.mark.api
def test_load_puzzle_default_payload(client):
    """Test POST /api/load with empty payload falls back to default puzzle."""
    rv = client.post('/api/load', json={})
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert 'characters' in data


@pytest.mark.api
def test_get_state(client):
    """Test GET /api/state returns current board state."""
    client.post('/api/load', json={'filename': 'puzzle_01_3x3_easy.json'})
    rv = client.get('/api/state')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert 'grid_size' in data
    assert 'characters' in data
    assert 'revealed_clues' in data
    assert len(data['characters']) == 9


@pytest.mark.api
def test_restart_puzzle(client):
    """Test POST /api/restart resets board to initial state."""
    client.post('/api/load', json={'filename': 'puzzle_01_3x3_easy.json'})
    # Submit a verdict to change state
    client.post('/api/verdict', json={'character_id': 'C1', 'status': 'INNOCENT'})
    
    # Restart
    rv = client.post('/api/restart')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data['message'] == "Puzzle restarted."
    # C1 should be UNKNOWN again
    c1_char = next(c for c in data['characters'] if c['id'] == 'C1')
    assert c1_char['revealed_status'] == 'UNKNOWN'


@pytest.mark.api
def test_verdict_accepted(client):
    """Test POST /api/verdict with logically entailed status (ACCEPTED)."""
    client.post('/api/load', json={'filename': 'puzzle_01_3x3_easy.json'})
    # C1 is entailed INNOCENT
    rv = client.post('/api/verdict', json={'character_id': 'C1', 'status': 'INNOCENT'})
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data['verdict_status'] == 'ACCEPTED'
    assert data['character_id'] == 'C1'
    assert data['claimed_status'] == 'INNOCENT'
    assert len(data['newly_revealed_clues']) > 0


@pytest.mark.api
def test_verdict_contradicted(client):
    """Test POST /api/verdict with opposite status (CONTRADICTED)."""
    client.post('/api/load', json={'filename': 'puzzle_01_3x3_easy.json'})
    # C1 is entailed INNOCENT, submitting CRIMINAL should be CONTRADICTED
    rv = client.post('/api/verdict', json={'character_id': 'C1', 'status': 'CRIMINAL'})
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data['verdict_status'] == 'CONTRADICTED'


@pytest.mark.api
def test_verdict_not_provable(client):
    """Test POST /api/verdict on unprovable character returns NOT_PROVABLE."""
    client.post('/api/load', json={'filename': 'puzzle_01_3x3_easy.json'})
    # C3 is not yet provable in initial state
    rv = client.post('/api/verdict', json={'character_id': 'C3', 'status': 'INNOCENT'})
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data['verdict_status'] == 'NOT_PROVABLE'


@pytest.mark.api
def test_verdict_already_revealed(client):
    """Test submitting verdict for already revealed character."""
    client.post('/api/load', json={'filename': 'puzzle_01_3x3_easy.json'})
    # Submit first verdict to reveal A1
    client.post('/api/verdict', json={'character_id': 'A1', 'status': 'INNOCENT'})
    # Submit again for A1
    rv = client.post('/api/verdict', json={'character_id': 'A1', 'status': 'INNOCENT'})
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data['verdict_status'] == 'ACCEPTED'
    assert "already revealed" in data['message']


@pytest.mark.api
def test_verdict_missing_params(client):
    """Test POST /api/verdict with missing parameters returns 400."""
    rv1 = client.post('/api/verdict', json={'character_id': 'A1'})
    assert rv1.status_code == 400
    rv2 = client.post('/api/verdict', json={'status': 'INNOCENT'})
    assert rv2.status_code == 400
    rv3 = client.post('/api/verdict', json={})
    assert rv3.status_code == 400


@pytest.mark.api
def test_verdict_invalid_character(client):
    """Test POST /api/verdict with invalid character_id returns 400."""
    rv = client.post('/api/verdict', json={'character_id': 'INVALID_ID', 'status': 'INNOCENT'})
    assert rv.status_code == 400
    data = json.loads(rv.data)
    assert 'error' in data


@pytest.mark.api
def test_hint_endpoint(client):
    """Test GET /api/hint generates valid hint structure."""
    client.post('/api/load', json={'filename': 'puzzle_01_3x3_easy.json'})
    rv = client.get('/api/hint')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert 'hint' in data
    hint = data['hint']
    assert hint is not None
    assert 'character_id' in hint
    assert 'coord' in hint
    assert 'suggested_status' in hint
    assert 'explanation' in hint
    assert 'relevant_clues' in hint
    assert 'dpll_stats' in hint


@pytest.mark.api
def test_hint_endpoint_when_solved(client):
    """Test GET /api/hint when board is fully solved returns hint: None."""
    client.post('/api/load', json={'filename': 'puzzle_01_3x3_easy.json'})
    # Solve fully
    client.post('/api/auto-solve')
    rv = client.get('/api/hint')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data['hint'] is None


@pytest.mark.api
def test_auto_step_endpoint(client):
    """Test POST /api/auto-step performs 1 deduction step."""
    client.post('/api/load', json={'filename': 'puzzle_01_3x3_easy.json'})
    rv = client.post('/api/auto-step')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert 'step_result' in data
    step = data['step_result']
    assert step is not None
    assert 'character_id' in step
    assert 'forced_status' in step
    assert 'verdict_status' in step
    assert step['verdict_status'] == 'ACCEPTED'


@pytest.mark.api
def test_auto_solve_endpoint(client):
    """Test POST /api/auto-solve solves puzzle completely."""
    client.post('/api/load', json={'filename': 'puzzle_01_3x3_easy.json'})
    rv = client.post('/api/auto-solve')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert 'trace' in data
    assert 'total_steps' in data
    assert data['total_steps'] > 0
    # All characters should now be revealed
    for char in data['characters']:
        assert char['revealed_status'] != 'UNKNOWN'
