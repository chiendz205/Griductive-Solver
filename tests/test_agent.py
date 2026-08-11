"""
Unit tests for LogicAgent entailment classification and deduction loop.
"""

import pytest
import os
from griductive.core.models import Status
from griductive.engine.game_engine import GameEngine
from griductive.agent.logic_agent import LogicAgent


def test_logic_agent_deduction_loop():
    engine = GameEngine()
    puzzle_path = os.path.join("data", "puzzle_01_3x3_easy.json")
    engine.load_puzzle_json(puzzle_path)

    agent = LogicAgent(engine)
    trace = agent.run_full_deduction_loop(engine)

    assert len(trace) > 0
    
    # Verify all characters solved
    pub_chars = engine.get_public_characters()
    unrevealed = [c for c in pub_chars.values() if c.revealed_status == Status.UNKNOWN]
    assert len(unrevealed) == 0
