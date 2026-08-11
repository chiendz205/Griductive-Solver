"""
Unit tests for GameEngine.
"""

import pytest
import os
from griductive.core.models import Status, VerdictStatus
from griductive.engine.game_engine import GameEngine


def test_game_engine_load_and_verdict():
    engine = GameEngine()
    puzzle_path = os.path.join("data", "puzzle_01_3x3_easy.json")
    engine.load_puzzle_json(puzzle_path)

    assert engine.get_grid_size() == 3
    pub_chars = engine.get_public_characters()
    assert len(pub_chars) == 9

    # Public characters should NOT reveal true status
    for char in pub_chars.values():
        assert char.true_status == Status.UNKNOWN

    # A1 is already revealed as INNOCENT by initial clue, Charlie C1 is logically forced INNOCENT
    res = engine.submit_verdict("C1", Status.INNOCENT)
    assert res.status == VerdictStatus.ACCEPTED

    # Submitting CONTRADICTED verdict for C1 (claiming CRIMINAL)
    res_wrong = engine.submit_verdict("B1", Status.INNOCENT)  # B1 is forced CRIMINAL
    assert res_wrong.status == VerdictStatus.CONTRADICTED


def test_game_engine_uniqueness():
    engine = GameEngine()
    puzzle_path = os.path.join("data", "puzzle_01_3x3_easy.json")
    engine.load_puzzle_json(puzzle_path)

    is_unique, count = engine.check_full_puzzle_uniqueness()
    assert is_unique is True
    assert count == 1
