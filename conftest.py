import sys
import os
import glob
import pytest

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app
from griductive.engine.game_engine import GameEngine
from griductive.agent.logic_agent import LogicAgent


@pytest.fixture
def client():
    """Flask test client fixture with TESTING mode enabled."""
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture
def clean_engine():
    """Provides a fresh GameEngine instance."""
    return GameEngine()


@pytest.fixture
def sample_3x3_engine():
    """Provides a GameEngine loaded with puzzle_01_3x3_easy.json."""
    engine = GameEngine()
    engine.load_puzzle_json(os.path.join("data", "puzzle_01_3x3_easy.json"))
    return engine


@pytest.fixture
def sample_3x3_agent(sample_3x3_engine):
    """Provides a LogicAgent connected to sample_3x3_engine."""
    return LogicAgent(sample_3x3_engine)


@pytest.fixture
def all_puzzle_files():
    """Returns all puzzle JSON paths in data/ excluding schema."""
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    puzzle_files = [
        f for f in sorted(glob.glob(os.path.join(data_dir, "puzzle_*.json")))
        if not f.endswith("puzzle_schema.json")
    ]
    return puzzle_files