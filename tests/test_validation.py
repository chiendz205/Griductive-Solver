"""
Unit tests for deep semantic validation of clue parameters.

The JSON schema only checks that `params` is an object; these tests verify the
GameEngine's additional `_validate_puzzle_semantics` / `validate_clue_semantics`
layer catches malformed clues and out-of-range / overlapping characters.
"""

import copy
import pytest
from griductive.engine.game_engine import GameEngine


def _base_puzzle():
    """A minimal, valid 3x3 puzzle used as a template to inject faults into."""
    return {
        "title": "Validation Template",
        "grid_size": 3,
        "characters": [
            {"id": "A1", "name": "Alice", "job": "J", "row": 1, "col": 1, "true_status": "INNOCENT"},
            {"id": "B1", "name": "Bob", "job": "J", "row": 1, "col": 2, "true_status": "CRIMINAL"},
            {"id": "A2", "name": "Cara", "job": "J", "row": 2, "col": 1, "true_status": "INNOCENT"},
        ],
        "clues": [
            {"id": "c1", "type": "FACT", "params": {"person": "A1", "status": "INNOCENT"},
             "description": "A1 innocent", "owner_id": "A1", "is_initially_revealed": True},
        ],
    }


def _load_with_clue(clue):
    data = _base_puzzle()
    data["clues"] = [clue]
    engine = GameEngine()
    engine.load_puzzle_data(data)  # dict path -> triggers deep validation
    return engine


@pytest.mark.engine
def test_valid_puzzle_loads():
    """The base template must load without raising."""
    engine = GameEngine()
    engine.load_puzzle_data(_base_puzzle())
    assert engine.get_grid_size() == 3


@pytest.mark.engine
def test_fact_missing_person():
    with pytest.raises(ValueError, match="missing required param 'person'"):
        _load_with_clue({"id": "x", "type": "FACT", "params": {"status": "INNOCENT"},
                         "description": "d", "owner_id": "A1"})


@pytest.mark.engine
def test_fact_unknown_person():
    with pytest.raises(ValueError, match="unknown character"):
        _load_with_clue({"id": "x", "type": "FACT", "params": {"person": "Z9", "status": "INNOCENT"},
                         "description": "d", "owner_id": "A1"})


@pytest.mark.engine
def test_fact_invalid_status():
    with pytest.raises(ValueError, match="invalid status"):
        _load_with_clue({"id": "x", "type": "FACT", "params": {"person": "A1", "status": "MAYBE"},
                         "description": "d", "owner_id": "A1"})


@pytest.mark.engine
def test_same_missing_person2():
    with pytest.raises(ValueError, match="missing required param 'person2'"):
        _load_with_clue({"id": "x", "type": "SAME", "params": {"person1": "A1"},
                         "description": "d", "owner_id": "A1"})


@pytest.mark.engine
def test_exactly_missing_k():
    with pytest.raises(ValueError, match="missing required param 'k'"):
        _load_with_clue({"id": "x", "type": "EXACTLY",
                         "params": {"region": {"type": "ROW", "param": 1}},
                         "description": "d", "owner_id": "A1"})


@pytest.mark.engine
def test_exactly_row_out_of_range():
    with pytest.raises(ValueError, match="ROW region"):
        _load_with_clue({"id": "x", "type": "EXACTLY",
                         "params": {"k": 1, "region": {"type": "ROW", "param": 9}},
                         "description": "d", "owner_id": "A1"})


@pytest.mark.engine
def test_explicit_region_unknown_char():
    with pytest.raises(ValueError, match="EXPLICIT region references unknown"):
        _load_with_clue({"id": "x", "type": "AT_LEAST",
                         "params": {"k": 1, "region": {"type": "EXPLICIT", "param": ["A1", "ZZ"]}},
                         "description": "d", "owner_id": "A1"})


@pytest.mark.engine
def test_parity_invalid_type():
    with pytest.raises(ValueError, match="invalid parity_type"):
        _load_with_clue({"id": "x", "type": "PARITY",
                         "params": {"parity_type": "NONE", "region": {"type": "ROW", "param": 1}},
                         "description": "d", "owner_id": "A1"})


@pytest.mark.engine
def test_between_invalid_status():
    with pytest.raises(ValueError, match="invalid target_status"):
        _load_with_clue({"id": "x", "type": "BETWEEN",
                         "params": {"char1": "A1", "char2": "B1", "target_status": "X"},
                         "description": "d", "owner_id": "A1"})


@pytest.mark.engine
def test_unknown_owner():
    with pytest.raises(ValueError, match="unknown owner_id"):
        _load_with_clue({"id": "x", "type": "FACT", "params": {"person": "A1", "status": "INNOCENT"},
                         "description": "d", "owner_id": "ZZ"})


@pytest.mark.engine
def test_duplicate_coordinates():
    data = _base_puzzle()
    data["characters"][1]["row"] = 1
    data["characters"][1]["col"] = 1  # collide with A1
    engine = GameEngine()
    with pytest.raises(ValueError, match="same cell"):
        engine.load_puzzle_data(data)


@pytest.mark.engine
def test_out_of_range_coordinate():
    data = _base_puzzle()
    data["characters"][0]["col"] = 9  # outside 3x3
    engine = GameEngine()
    with pytest.raises(ValueError, match="out-of-range coordinate"):
        engine.load_puzzle_data(data)
