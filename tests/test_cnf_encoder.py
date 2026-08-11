"""
Unit tests comparing CNF Encoder output against Semantic Evaluators.
"""

import pytest
from typing import Dict
from itertools import product
from griductive.core.models import Status, Character, ClueData, ClueType, ParityType, Region, RegionType
from griductive.core.var_map import VariableManager
from griductive.logic.clues import resolve_region_characters
from griductive.logic.evaluators import evaluate_clue_semantically
from griductive.logic.cnf_encoder import CNFEncoder
from griductive.logic.dpll import DPLLSolver


def create_test_characters() -> Dict[str, Character]:
    return {
        "A1": Character("A1", "Alice", "Job1", 1, 1, Status.INNOCENT),
        "B1": Character("B1", "Bob", "Job2", 1, 2, Status.CRIMINAL),
        "C1": Character("C1", "Charlie", "Job3", 1, 3, Status.INNOCENT),
        "A2": Character("A2", "David", "Job4", 2, 1, Status.CRIMINAL),
        "B2": Character("B2", "Eve", "Job5", 2, 2, Status.INNOCENT),
        "C2": Character("C2", "Frank", "Job6", 2, 3, Status.CRIMINAL)
    }


def test_cnf_vs_semantic_evaluator_all_clues():
    chars = create_test_characters()
    var_mgr = VariableManager(list(chars.values()))
    encoder = CNFEncoder(var_mgr, chars, grid_size=3)
    solver = DPLLSolver()

    clues = [
        ClueData("1", ClueType.FACT, {"person": "A1", "status": "INNOCENT"}, "A1 innocent", "A1", True),
        ClueData("2", ClueType.SAME, {"person1": "A1", "person2": "C1"}, "A1 same C1", "A1", True),
        ClueData("3", ClueType.DIFFERENT, {"person1": "A1", "person2": "B1"}, "A1 diff B1", "A1", True),
        ClueData("4", ClueType.EXACTLY, {"k": 1, "region": {"type": "ROW", "param": 1}}, "Row 1 exact 1", "A1", True),
        ClueData("5", ClueType.AT_LEAST, {"k": 1, "region": {"type": "ROW", "param": 2}}, "Row 2 at least 1", "A1", True),
        ClueData("6", ClueType.AT_MOST, {"k": 2, "region": {"type": "ROW", "param": 2}}, "Row 2 at most 2", "A1", True),
        ClueData("7", ClueType.PARITY, {"parity_type": "EVEN", "region": {"type": "ROW", "param": 1}}, "Row 1 even", "A1", True),
        ClueData("8", ClueType.BETWEEN, {"char1": "A1", "char2": "C1", "target_status": "CRIMINAL"}, "Between A1 C1 is criminal", "A1", True)
    ]

    main_vars = var_mgr.get_all_main_vars()

    for clue in clues:
        cnf_clauses = encoder.encode_clue(clue)
        all_vars = list(range(1, var_mgr.total_vars_count + 1))

        # Check all possible assignments for main variables (2^6 = 64)
        for bool_vals in product([False, True], repeat=len(main_vars)):
            assignment: Dict[int, bool] = dict(zip(main_vars, bool_vals))

            semantic_val = evaluate_clue_semantically(clue, assignment, var_mgr, chars, 3)

            # Enforce main variable assignment in SAT solver as assumptions
            assumptions = [v if assignment[v] else -v for v in main_vars]
            sat, _, _ = solver.solve(cnf_clauses, all_vars, assumptions=assumptions)

            # CNF formula MUST match Semantic Evaluator output 100%
            assert sat == semantic_val, (
                f"Mismatch for clue {clue.clue_type.value} on assignment {assignment}! "
                f"Semantic: {semantic_val}, SAT CNF: {sat}"
            )
