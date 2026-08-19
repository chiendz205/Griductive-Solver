"""
Unit tests for GameEngine:
- Puzzle loading and JSON Schema validation
- Public KB isolation (hiding true_status)
- Verdict submission (ACCEPTED, CONTRADICTED, NOT_PROVABLE, ALREADY_REVEALED)
- Puzzle restart
- Secret full puzzle uniqueness validation
"""

import pytest
import os
from griductive.core.models import Status, VerdictStatus
from griductive.engine.game_engine import GameEngine


@pytest.mark.engine
def test_game_engine_load_puzzle():
    """Test loading valid puzzle populates grid size and characters."""
    engine = GameEngine()
    puzzle_path = os.path.join("data", "puzzle_01_3x3_easy.json")
    engine.load_puzzle_json(puzzle_path)

    assert engine.get_grid_size() == 3
    pub_chars = engine.get_public_characters()
    assert len(pub_chars) == 9

    # Public characters must hide true status
    for char in pub_chars.values():
        assert char.true_status == Status.UNKNOWN


@pytest.mark.engine
def test_game_engine_invalid_schema():
    """Test loading invalid puzzle data via JSON file raises ValueError."""
    engine = GameEngine()
    invalid_data = {
        "grid_size": 2,  # Minimum is 3 according to schema
        "characters": [],
        "clues": []
    }
    temp_json_path = os.path.join("data", "temp_invalid_test.json")
    import json
    with open(temp_json_path, "w", encoding="utf-8") as f:
        json.dump(invalid_data, f)
    
    try:
        with pytest.raises(ValueError) as excinfo:
            engine.load_puzzle_json(temp_json_path)
        assert "Invalid puzzle format" in str(excinfo.value)
    finally:
        if os.path.exists(temp_json_path):
            os.remove(temp_json_path)


@pytest.mark.engine
def test_submit_verdict_accepted(sample_3x3_engine):
    """Test submitting logically entailed verdict results in ACCEPTED."""
    # A1 is entailed INNOCENT
    res = sample_3x3_engine.submit_verdict("A1", Status.INNOCENT)
    assert res.status == VerdictStatus.ACCEPTED
    assert res.character_id == "A1"
    assert res.claimed_status == Status.INNOCENT


@pytest.mark.engine
def test_submit_verdict_contradicted(sample_3x3_engine):
    """Test submitting opposite status results in CONTRADICTED."""
    # A1 is forced INNOCENT; claiming CRIMINAL must contradict
    res = sample_3x3_engine.submit_verdict("A1", Status.CRIMINAL)
    assert res.status == VerdictStatus.CONTRADICTED
    assert res.character_id == "A1"
    assert "CONTRADICTED" in res.message


@pytest.mark.engine
def test_submit_verdict_not_provable(sample_3x3_engine):
    """Test submitting verdict for unprovable character returns NOT_PROVABLE."""
    # C3 is not yet forced
    res = sample_3x3_engine.submit_verdict("C3", Status.INNOCENT)
    assert res.status == VerdictStatus.NOT_PROVABLE
    assert "NOT_PROVABLE" in res.message


@pytest.mark.engine
def test_submit_verdict_already_revealed(sample_3x3_engine):
    """Test submitting verdict for already revealed character returns ACCEPTED."""
    # Submit first verdict to reveal A1
    sample_3x3_engine.submit_verdict("A1", Status.INNOCENT)
    # Submit again
    res = sample_3x3_engine.submit_verdict("A1", Status.INNOCENT)
    assert res.status == VerdictStatus.ACCEPTED
    assert "already revealed" in res.message


@pytest.mark.engine
def test_submit_verdict_unknown_character(sample_3x3_engine):
    """Test submitting verdict for non-existent character raises ValueError."""
    with pytest.raises(ValueError) as excinfo:
        sample_3x3_engine.submit_verdict("Z99", Status.INNOCENT)
    assert "Unknown character ID" in str(excinfo.value)


@pytest.mark.engine
def test_game_engine_restart(sample_3x3_engine):
    """Test restart reverts proven verdicts and unrevealed statuses."""
    # Prove C1
    sample_3x3_engine.submit_verdict("C1", Status.INNOCENT)
    assert "C1" in sample_3x3_engine.get_proven_verdicts()

    # Restart
    sample_3x3_engine.restart()
    assert len(sample_3x3_engine.get_proven_verdicts()) == 0
    pub_chars = sample_3x3_engine.get_public_characters()
    assert pub_chars["C1"].revealed_status == Status.UNKNOWN


@pytest.mark.engine
def test_game_engine_uniqueness_check(sample_3x3_engine):
    """Test check_full_puzzle_uniqueness returns True and 1 for valid unique puzzle."""
    is_unique, count = sample_3x3_engine.check_full_puzzle_uniqueness()
    assert is_unique is True
    assert count == 1
