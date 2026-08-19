"""
Dedicated test cases verifying entailment and status classifications:
- Status.NOT_PROVABLE / VerdictStatus.NOT_PROVABLE
- Status.INCONSISTENT (when public KB contains contradictory clauses)
- Status.UNKNOWN (when both positive and negative assignments are SAT)
- Status.CRIMINAL (when KB ^ NOT_Ci is UNSAT)
- Status.INNOCENT (when KB ^ Ci is UNSAT)
"""

import pytest
from griductive.core.models import Status, VerdictStatus, Character, ClueData, ClueType
from griductive.engine.game_engine import GameEngine
from griductive.agent.logic_agent import LogicAgent


def create_mock_engine(characters_data, clues_data):
    """Helper creating an in-memory GameEngine with specific characters and clues."""
    engine = GameEngine()
    data = {
        "grid_size": 3,
        "characters": characters_data,
        "clues": clues_data
    }
    engine.load_puzzle_data(data)
    return engine


@pytest.mark.unit
def test_status_criminal_forced():
    """Test Status.CRIMINAL classification when KB forces character to be CRIMINAL."""
    chars = [
        {"id": "A1", "name": "Alice", "job": "Job1", "row": 1, "col": 1, "true_status": "CRIMINAL"},
        {"id": "B1", "name": "Bob", "job": "Job2", "row": 1, "col": 2, "true_status": "INNOCENT"},
        {"id": "C1", "name": "Charlie", "job": "Job3", "row": 1, "col": 3, "true_status": "INNOCENT"}
    ]
    clues = [
        {
            "id": "c1",
            "type": "FACT",
            "params": {"person": "A1", "status": "CRIMINAL"},
            "description": "A1 is CRIMINAL",
            "owner_id": "A1",
            "is_initially_revealed": True
        }
    ]
    engine = create_mock_engine(chars, clues)
    agent = LogicAgent(engine)

    status, stats, debug = agent.classify_character("A1")
    assert status == Status.CRIMINAL
    assert debug["sat_neg"] is False
    assert debug["sat_pos"] is True

    verdict_res = engine.submit_verdict("A1", Status.CRIMINAL)
    assert verdict_res.status == VerdictStatus.ACCEPTED


@pytest.mark.unit
def test_status_innocent_forced():
    """Test Status.INNOCENT classification when KB forces character to be INNOCENT."""
    chars = [
        {"id": "A1", "name": "Alice", "job": "Job1", "row": 1, "col": 1, "true_status": "INNOCENT"},
        {"id": "B1", "name": "Bob", "job": "Job2", "row": 1, "col": 2, "true_status": "INNOCENT"},
        {"id": "C1", "name": "Charlie", "job": "Job3", "row": 1, "col": 3, "true_status": "INNOCENT"}
    ]
    clues = [
        {
            "id": "c1",
            "type": "FACT",
            "params": {"person": "A1", "status": "INNOCENT"},
            "description": "A1 is INNOCENT",
            "owner_id": "A1",
            "is_initially_revealed": True
        }
    ]
    engine = create_mock_engine(chars, clues)
    agent = LogicAgent(engine)

    status, stats, debug = agent.classify_character("A1")
    assert status == Status.INNOCENT
    assert debug["sat_neg"] is True
    assert debug["sat_pos"] is False

    verdict_res = engine.submit_verdict("A1", Status.INNOCENT)
    assert verdict_res.status == VerdictStatus.ACCEPTED


@pytest.mark.unit
def test_status_unknown_and_not_provable():
    """Test Status.UNKNOWN and VerdictStatus.NOT_PROVABLE when clues are insufficient."""
    chars = [
        {"id": "A1", "name": "Alice", "job": "Job1", "row": 1, "col": 1, "true_status": "INNOCENT"},
        {"id": "B1", "name": "Bob", "job": "Job2", "row": 1, "col": 2, "true_status": "CRIMINAL"},
        {"id": "C1", "name": "Charlie", "job": "Job3", "row": 1, "col": 3, "true_status": "INNOCENT"}
    ]
    # Clue only says A1 and B1 have DIFFERENT statuses. Neither A1 nor B1 is fixed on its own.
    clues = [
        {
            "id": "c1",
            "type": "DIFFERENT",
            "params": {"person1": "A1", "person2": "B1"},
            "description": "A1 and B1 are DIFFERENT",
            "owner_id": "A1",
            "is_initially_revealed": True
        }
    ]
    engine = create_mock_engine(chars, clues)
    agent = LogicAgent(engine)

    # Classifying A1: could be CRIMINAL or INNOCENT
    status, stats, debug = agent.classify_character("A1")
    assert status == Status.UNKNOWN
    assert debug["sat_neg"] is True
    assert debug["sat_pos"] is True

    # Submitting verdict for A1 must return NOT_PROVABLE
    verdict_res = engine.submit_verdict("A1", Status.CRIMINAL)
    assert verdict_res.status == VerdictStatus.NOT_PROVABLE

    verdict_res2 = engine.submit_verdict("A1", Status.INNOCENT)
    assert verdict_res2.status == VerdictStatus.NOT_PROVABLE


@pytest.mark.unit
def test_status_inconsistent_base_kb():
    """Test Status.INCONSISTENT when public KB has contradictory clues (Base KB UNSAT)."""
    chars = [
        {"id": "A1", "name": "Alice", "job": "Job1", "row": 1, "col": 1, "true_status": "INNOCENT"},
        {"id": "B1", "name": "Bob", "job": "Job2", "row": 1, "col": 2, "true_status": "INNOCENT"}
    ]
    # Two contradictory FACT clues revealed at once
    clues = [
        {
            "id": "c1",
            "type": "FACT",
            "params": {"person": "A1", "status": "INNOCENT"},
            "description": "A1 is INNOCENT",
            "owner_id": "A1",
            "is_initially_revealed": True
        },
        {
            "id": "c2",
            "type": "FACT",
            "params": {"person": "A1", "status": "CRIMINAL"},
            "description": "A1 is CRIMINAL",
            "owner_id": "A1",
            "is_initially_revealed": True
        }
    ]
    engine = create_mock_engine(chars, clues)
    agent = LogicAgent(engine)

    status, stats, debug = agent.classify_character("A1")
    assert status == Status.INCONSISTENT
    assert debug["reason"] == "Base KB is UNSAT"


@pytest.mark.unit
def test_verdict_contradicted_explicit():
    """Test VerdictStatus.CONTRADICTED when submitting status that directly contradicts entailment."""
    chars = [
        {"id": "A1", "name": "Alice", "job": "Job1", "row": 1, "col": 1, "true_status": "CRIMINAL"},
        {"id": "B1", "name": "Bob", "job": "Job2", "row": 1, "col": 2, "true_status": "INNOCENT"}
    ]
    clues = [
        {
            "id": "c1",
            "type": "FACT",
            "params": {"person": "A1", "status": "CRIMINAL"},
            "description": "A1 is CRIMINAL",
            "owner_id": "A1",
            "is_initially_revealed": True
        }
    ]
    engine = create_mock_engine(chars, clues)

    # Claiming INNOCENT when CRIMINAL is entailed
    verdict_res = engine.submit_verdict("A1", Status.INNOCENT)
    assert verdict_res.status == VerdictStatus.CONTRADICTED
    assert "CONTRADICTED" in verdict_res.message
