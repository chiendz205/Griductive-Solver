"""
Unit tests for scratch DPLL SAT Solver.
"""

import pytest
from griductive.logic.dpll import DPLLSolver


def test_dpll_simple_sat():
    solver = DPLLSolver()
    # (x1 v x2) ^ (-x1 v x2)
    clauses = [[1, 2], [-1, 2]]
    sat, model, stats = solver.solve(clauses, all_variables=[1, 2])
    assert sat is True
    assert model[2] is True


def test_dpll_simple_unsat():
    solver = DPLLSolver()
    # (x1) ^ (-x1)
    clauses = [[1], [-1]]
    sat, model, stats = solver.solve(clauses, all_variables=[1])
    assert sat is False
    assert model is None


def test_dpll_assumptions():
    solver = DPLLSolver()
    # (x1 v x2)
    clauses = [[1, 2]]
    
    # Assumption x1 = False => x2 must be True
    sat, model, stats = solver.solve(clauses, all_variables=[1, 2], assumptions=[-1])
    assert sat is True
    assert model[1] is False
    assert model[2] is True

    # Assumption x1 = False and x2 = False => UNSAT
    sat, model, stats = solver.solve(clauses, all_variables=[1, 2], assumptions=[-1, -2])
    assert sat is False
