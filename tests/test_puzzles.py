"""
Multi-puzzle validation test suite:
- Validates all puzzle JSON files against puzzle_schema.json
- Verifies uniqueness (exactly 1 satisfying assignment) for each puzzle
- Verifies that LogicAgent can fully solve every puzzle with 0 unrevealed characters remaining
"""

import os
import json
import glob
import pytest
from jsonschema import validate, ValidationError
from griductive.core.models import Status
from griductive.engine.game_engine import GameEngine
from griductive.agent.logic_agent import LogicAgent


@pytest.mark.puzzles
def test_all_puzzles_schema_conformance(all_puzzle_files):
    """Verifies that every puzzle JSON in data/ adheres to puzzle_schema.json."""
    schema_path = os.path.join("data", "puzzle_schema.json")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    assert len(all_puzzle_files) >= 7

    for puzzle_path in all_puzzle_files:
        with open(puzzle_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        try:
            validate(instance=data, schema=schema)
        except ValidationError as e:
            pytest.fail(f"Puzzle {os.path.basename(puzzle_path)} failed schema validation: {e.message}")


@pytest.mark.puzzles
def test_all_puzzles_uniqueness(all_puzzle_files):
    """Verifies that every puzzle in data/ has exactly ONE unique solution."""
    for puzzle_path in all_puzzle_files:
        engine = GameEngine()
        engine.load_puzzle_json(puzzle_path)
        is_unique, count = engine.check_full_puzzle_uniqueness()
        assert is_unique is True, f"Puzzle {os.path.basename(puzzle_path)} is NOT unique! Count={count}"
        assert count == 1, f"Puzzle {os.path.basename(puzzle_path)} has {count} solutions, expected 1"


@pytest.mark.puzzles
def test_all_puzzles_solvable_by_agent(all_puzzle_files):
    """Verifies that LogicAgent can completely solve each puzzle via public KB deduction."""
    for puzzle_path in all_puzzle_files:
        engine = GameEngine()
        engine.load_puzzle_json(puzzle_path)
        agent = LogicAgent(engine)

        trace = agent.run_full_deduction_loop(engine)
        assert len(trace) > 0, f"Puzzle {os.path.basename(puzzle_path)} produced empty deduction trace."

        # Verify all characters solved
        pub_chars = engine.get_public_characters()
        unrevealed = [c for c in pub_chars.values() if c.revealed_status == Status.UNKNOWN]
        assert len(unrevealed) == 0, (
            f"Puzzle {os.path.basename(puzzle_path)} was not completely solved. "
            f"Remaining unrevealed: {[c.id for c in unrevealed]}"
        )


@pytest.mark.puzzles
def test_puzzles_grid_size_and_characters_count(all_puzzle_files):
    """Verifies that N x N grid contains exactly N^2 characters."""
    for puzzle_path in all_puzzle_files:
        with open(puzzle_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        grid_size = data["grid_size"]
        expected_chars = grid_size * grid_size
        assert len(data["characters"]) == expected_chars, (
            f"Puzzle {os.path.basename(puzzle_path)} has {len(data['characters'])} chars, "
            f"expected {expected_chars} for {grid_size}x{grid_size}"
        )
