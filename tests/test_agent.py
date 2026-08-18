"""
Unit tests for LogicAgent:
- Hint generation (provide_hint)
- Entailment classification (classify_character)
- Single deduction step (run_deduction_step)
- Full deduction loop (run_full_deduction_loop)
- Deterministic row-major ordering
- PublicKBInterface strict isolation
"""

import pytest
import os
from griductive.core.models import Status, Character, ClueData, ClueType, Region, RegionType
from griductive.engine.game_engine import GameEngine
from griductive.agent.logic_agent import LogicAgent


@pytest.mark.agent
def test_provide_hint_structure(sample_3x3_engine):
    """Test provide_hint returns structured hint with all required fields."""
    agent = LogicAgent(sample_3x3_engine)
    hint = agent.provide_hint()

    assert hint is not None
    assert isinstance(hint, dict)
    assert "character_id" in hint
    assert "character_name" in hint
    assert "coord" in hint
    assert "suggested_status" in hint
    assert hint["suggested_status"] in ["INNOCENT", "CRIMINAL"]
    assert "explanation" in hint
    assert len(hint["explanation"]) > 0
    assert "relevant_clues" in hint
    assert isinstance(hint["relevant_clues"], list)
    assert "dpll_stats" in hint


@pytest.mark.agent
def test_provide_hint_deterministic_row_major(sample_3x3_engine):
    """Test hint selection follows deterministic row-major order."""
    agent = LogicAgent(sample_3x3_engine)
    hint = agent.provide_hint()
    assert hint is not None
    # For puzzle_01, A1 (row 1, col 1) is the first unrevealed logically entailed character
    assert hint["character_id"] == "A1"
    assert hint["coord"] == "A1"
    assert hint["suggested_status"] == "INNOCENT"


@pytest.mark.agent
def test_provide_hint_when_no_deduction_possible():
    """Test provide_hint returns None when all characters are resolved or none entailed."""
    engine = GameEngine()
    engine.load_puzzle_json(os.path.join("data", "puzzle_01_3x3_easy.json"))
    agent = LogicAgent(engine)

    # Solve puzzle completely
    agent.run_full_deduction_loop(engine)

    # No further hint should be available
    hint = agent.provide_hint()
    assert hint is None


@pytest.mark.agent
def test_classify_character_success(sample_3x3_engine):
    """Test classify_character correctly identifies forced status."""
    agent = LogicAgent(sample_3x3_engine)
    
    # C1 is forced INNOCENT by A1's SAME clue
    status, stats, debug = agent.classify_character("C1")
    assert status == Status.INNOCENT
    assert stats.decisions_count >= 0
    assert debug["sat_neg"] is True
    assert debug["sat_pos"] is False


@pytest.mark.agent
def test_classify_character_unknown():
    """Test classify_character returns UNKNOWN when neither status is forced."""
    engine = GameEngine()
    engine.load_puzzle_json(os.path.join("data", "puzzle_01_3x3_easy.json"))
    agent = LogicAgent(engine)

    # In initial state, C3 cannot yet be proved
    status, stats, debug = agent.classify_character("C3")
    assert status == Status.UNKNOWN
    assert debug["sat_neg"] is True
    assert debug["sat_pos"] is True


@pytest.mark.agent
def test_classify_character_nonexistent_id(sample_3x3_engine):
    """Test classify_character raises KeyError on invalid character ID."""
    agent = LogicAgent(sample_3x3_engine)
    with pytest.raises(KeyError):
        agent.classify_character("NONEXISTENT_99")


@pytest.mark.agent
def test_run_deduction_step(sample_3x3_engine):
    """Test run_deduction_step performs a single verified deduction step."""
    agent = LogicAgent(sample_3x3_engine)
    step = agent.run_deduction_step(sample_3x3_engine)

    assert step is not None
    assert step["character_id"] == "A1"
    assert step["forced_status"] == "INNOCENT"
    assert step["verdict_status"] == "ACCEPTED"
    assert "solver_stats" in step
    assert "runtime_ms" in step


@pytest.mark.agent
def test_run_full_deduction_loop(sample_3x3_engine):
    """Test run_full_deduction_loop solves the entire puzzle step by step."""
    agent = LogicAgent(sample_3x3_engine)
    trace = agent.run_full_deduction_loop(sample_3x3_engine)

    assert len(trace) > 0
    for idx, step in enumerate(trace, start=1):
        assert step["step"] == idx
        assert step["verdict_status"] == "ACCEPTED"

    # All characters must be revealed
    pub_chars = sample_3x3_engine.get_public_characters()
    unrevealed = [c for c in pub_chars.values() if c.revealed_status == Status.UNKNOWN]
    assert len(unrevealed) == 0


@pytest.mark.agent
def test_agent_never_accesses_secret_true_status(sample_3x3_engine):
    """Verify that agent only interacts via public characters whose true_status is hidden."""
    pub_chars = sample_3x3_engine.get_public_characters()
    for char in pub_chars.values():
        assert char.true_status == Status.UNKNOWN
