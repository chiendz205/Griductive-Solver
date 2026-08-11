"""
Pure Python DPLL SAT Solver from scratch.
Supports Unit Propagation, Heuristic Variable Selection, Branching & Backtracking,
detailed Solver Statistics logging, and temporary assumptions for entailment checks.
"""

import time
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field


@dataclass
class DPLLStats:
    decisions_count: int = 0
    propagations_count: int = 0
    backtracks_count: int = 0
    runtime_ms: float = 0.0

    def summary(self) -> str:
        return (f"DPLL Stats: {self.decisions_count} decisions, "
                f"{self.propagations_count} propagations, "
                f"{self.backtracks_count} backtracks, "
                f"{self.runtime_ms:.2f} ms runtime.")


class DPLLSolver:
    """
    DPLL SAT Solver built strictly from scratch using pure Python.
    """

    def __init__(self):
        self.stats = DPLLStats()

    def solve(
        self,
        clauses: List[List[int]],
        all_variables: List[int],
        assumptions: Optional[List[int]] = None
    ) -> Tuple[bool, Optional[Dict[int, bool]], DPLLStats]:
        """
        Solves a CNF formula with optional unit assumptions.

        Args:
            clauses: List of CNF clauses (list of integers).
            all_variables: Complete list of positive variable IDs to be assigned.
            assumptions: Optional list of unit literals (e.g. [1, -3]) assumed true.

        Returns:
            (is_sat, model, stats)
        """
        self.stats = DPLLStats()
        start_time = time.perf_counter()

        # Deep copy clauses so solver doesn't mutate original
        working_clauses = [list(c) for c in clauses]

        # Apply assumptions as initial unit clauses
        if assumptions:
            for ass in assumptions:
                working_clauses.append([ass])

        initial_assignment: Dict[int, bool] = {}

        is_sat, model = self._dpll_rec(working_clauses, initial_assignment, set(all_variables))

        self.stats.runtime_ms = (time.perf_counter() - start_time) * 1000.0

        if is_sat and model is not None:
            # Ensure every requested variable has an assignment
            for v in all_variables:
                if v not in model:
                    model[v] = False  # Default unassigned vars to False

        return is_sat, model, self.stats

    def _dpll_rec(
        self,
        clauses: List[List[int]],
        assignment: Dict[int, bool],
        unassigned_vars: Set[int]
    ) -> Tuple[bool, Optional[Dict[int, bool]]]:

        clauses, assignment, unassigned_vars, conflict = self._unit_propagate(
            clauses, assignment, unassigned_vars
        )

        if conflict:
            return False, None

        if not clauses:
            # All clauses satisfied!
            return True, assignment

        # Check for empty clause in current formula
        if any(len(c) == 0 for c in clauses):
            return False, None

        # Select next variable using DLCS (Dynamic Largest Combined Sum) heuristic
        var, preferred_val = self._select_heuristic_variable(clauses, unassigned_vars)
        if var is None:
            return True, assignment

        # Branching step
        self.stats.decisions_count += 1
        new_unassigned = unassigned_vars - {var}

        # Attempt 1: preferred value
        assignment_branch1 = dict(assignment)
        assignment_branch1[var] = preferred_val
        literal1 = var if preferred_val else -var
        clauses_branch1 = [list(c) for c in clauses] + [[literal1]]

        is_sat1, model1 = self._dpll_rec(clauses_branch1, assignment_branch1, new_unassigned)
        if is_sat1:
            return True, model1

        # Backtrack
        self.stats.backtracks_count += 1

        # Attempt 2: opposite value
        assignment_branch2 = dict(assignment)
        assignment_branch2[var] = not preferred_val
        literal2 = -var if preferred_val else var
        clauses_branch2 = [list(c) for c in clauses] + [[literal2]]

        return self._dpll_rec(clauses_branch2, assignment_branch2, new_unassigned)

    def _unit_propagate(
        self,
        clauses: List[List[int]],
        assignment: Dict[int, bool],
        unassigned_vars: Set[int]
    ) -> Tuple[List[List[int]], Dict[int, bool], Set[int], bool]:
        """
        Iteratively performs unit propagation until no unit clauses remain.
        Returns (simplified_clauses, updated_assignment, updated_unassigned_vars, conflict_flag).
        """
        assignment = dict(assignment)
        unassigned = set(unassigned_vars)

        while True:
            unit_literal = None
            for c in clauses:
                if len(c) == 1:
                    unit_literal = c[0]
                    break

            if unit_literal is None:
                break  # No unit clauses left

            self.stats.propagations_count += 1
            var = abs(unit_literal)
            val = (unit_literal > 0)

            if var in assignment:
                if assignment[var] != val:
                    # Contradictory unit clauses!
                    return clauses, assignment, unassigned, True
            else:
                assignment[var] = val
                unassigned.discard(var)

            # Simplify clauses
            new_clauses = []
            for c in clauses:
                if unit_literal in c:
                    continue  # Clause satisfied, omit
                if -unit_literal in c:
                    new_c = [lit for lit in c if lit != -unit_literal]
                    if len(new_c) == 0:
                        return new_clauses, assignment, unassigned, True # Empty clause = conflict
                    new_clauses.append(new_c)
                else:
                    new_clauses.append(c)

            clauses = new_clauses

        return clauses, assignment, unassigned, False

    def _select_heuristic_variable(
        self,
        clauses: List[List[int]],
        unassigned_vars: Set[int]
    ) -> Tuple[Optional[int], bool]:
        """
        DLCS (Dynamic Largest Combined Sum) Heuristic:
        Selects the unassigned variable that appears most frequently in unresolved clauses.
        Returns (var_id, preferred_boolean_value).
        """
        if not unassigned_vars:
            return None, True

        pos_counts: Dict[int, int] = {v: 0 for v in unassigned_vars}
        neg_counts: Dict[int, int] = {v: 0 for v in unassigned_vars}

        for c in clauses:
            for lit in c:
                v = abs(lit)
                if v in unassigned_vars:
                    if lit > 0:
                        pos_counts[v] += 1
                    else:
                        neg_counts[v] += 1

        best_var = None
        max_total = -1
        preferred_val = True

        for v in sorted(unassigned_vars):  # Deterministic iteration
            pos = pos_counts[v]
            neg = neg_counts[v]
            total = pos + neg
            if total > max_total:
                max_total = total
                best_var = v
                preferred_val = (pos >= neg)

        if best_var is None:
            best_var = min(unassigned_vars)
            preferred_val = True

        return best_var, preferred_val
