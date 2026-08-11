"""
Semantic Evaluators for all Clue Types.
Evaluates truth value of clues directly against complete Boolean assignments (without CNF/SAT conversion).
Used for verification and cross-testing against the CNF encoder.
"""

from typing import Dict, List, Any
from griductive.core.models import Status, ClueData, ClueType, ParityType, Region, RegionType, Character
from griductive.core.var_map import VariableManager
from griductive.logic.clues import resolve_region_characters


def evaluate_fact(clue: ClueData, assignment: Dict[int, bool], var_mgr: VariableManager) -> bool:
    person = clue.params["person"]
    expected_status = Status(clue.params["status"])
    var_id = var_mgr.get_var(person)
    actual_is_criminal = assignment[var_id]
    return actual_is_criminal == (expected_status == Status.CRIMINAL)


def evaluate_same(clue: ClueData, assignment: Dict[int, bool], var_mgr: VariableManager) -> bool:
    p1 = clue.params["person1"]
    p2 = clue.params["person2"]
    v1 = assignment[var_mgr.get_var(p1)]
    v2 = assignment[var_mgr.get_var(p2)]
    return v1 == v2


def evaluate_different(clue: ClueData, assignment: Dict[int, bool], var_mgr: VariableManager) -> bool:
    p1 = clue.params["person1"]
    p2 = clue.params["person2"]
    v1 = assignment[var_mgr.get_var(p1)]
    v2 = assignment[var_mgr.get_var(p2)]
    return v1 != v2


def evaluate_exactly(
    clue: ClueData,
    assignment: Dict[int, bool],
    var_mgr: VariableManager,
    characters: Dict[str, Character],
    grid_size: int
) -> bool:
    k = clue.params["k"]
    region = Region.from_dict(clue.params["region"])
    char_ids = resolve_region_characters(region, characters, grid_size)
    criminal_count = sum(1 for cid in char_ids if assignment[var_mgr.get_var(cid)])
    return criminal_count == k


def evaluate_at_least(
    clue: ClueData,
    assignment: Dict[int, bool],
    var_mgr: VariableManager,
    characters: Dict[str, Character],
    grid_size: int
) -> bool:
    k = clue.params["k"]
    region = Region.from_dict(clue.params["region"])
    char_ids = resolve_region_characters(region, characters, grid_size)
    criminal_count = sum(1 for cid in char_ids if assignment[var_mgr.get_var(cid)])
    return criminal_count >= k


def evaluate_at_most(
    clue: ClueData,
    assignment: Dict[int, bool],
    var_mgr: VariableManager,
    characters: Dict[str, Character],
    grid_size: int
) -> bool:
    k = clue.params["k"]
    region = Region.from_dict(clue.params["region"])
    char_ids = resolve_region_characters(region, characters, grid_size)
    criminal_count = sum(1 for cid in char_ids if assignment[var_mgr.get_var(cid)])
    return criminal_count <= k


def evaluate_parity(
    clue: ClueData,
    assignment: Dict[int, bool],
    var_mgr: VariableManager,
    characters: Dict[str, Character],
    grid_size: int
) -> bool:
    parity = ParityType(clue.params["parity_type"])
    region = Region.from_dict(clue.params["region"])
    char_ids = resolve_region_characters(region, characters, grid_size)
    criminal_count = sum(1 for cid in char_ids if assignment[var_mgr.get_var(cid)])
    if parity == ParityType.EVEN:
        return criminal_count % 2 == 0
    else:
        return criminal_count % 2 == 1


def evaluate_between(
    clue: ClueData,
    assignment: Dict[int, bool],
    var_mgr: VariableManager,
    characters: Dict[str, Character],
    grid_size: int
) -> bool:
    char1 = clue.params["char1"]
    char2 = clue.params["char2"]
    target_status = Status(clue.params["target_status"])
    region = Region(RegionType.BETWEEN_CELLS, [char1, char2])
    char_ids = resolve_region_characters(region, characters, grid_size)
    
    expected_criminal = (target_status == Status.CRIMINAL)
    return all(assignment[var_mgr.get_var(cid)] == expected_criminal for cid in char_ids)


def evaluate_clue_semantically(
    clue: ClueData,
    assignment: Dict[int, bool],
    var_mgr: VariableManager,
    characters: Dict[str, Character],
    grid_size: int
) -> bool:
    """Master evaluator dispatching clue evaluation directly based on clue type."""
    t = clue.clue_type
    if t == ClueType.FACT:
        return evaluate_fact(clue, assignment, var_mgr)
    elif t == ClueType.SAME:
        return evaluate_same(clue, assignment, var_mgr)
    elif t == ClueType.DIFFERENT:
        return evaluate_different(clue, assignment, var_mgr)
    elif t == ClueType.EXACTLY:
        return evaluate_exactly(clue, assignment, var_mgr, characters, grid_size)
    elif t == ClueType.AT_LEAST:
        return evaluate_at_least(clue, assignment, var_mgr, characters, grid_size)
    elif t == ClueType.AT_MOST:
        return evaluate_at_most(clue, assignment, var_mgr, characters, grid_size)
    elif t == ClueType.PARITY:
        return evaluate_parity(clue, assignment, var_mgr, characters, grid_size)
    elif t == ClueType.BETWEEN:
        return evaluate_between(clue, assignment, var_mgr, characters, grid_size)
    else:
        raise ValueError(f"Unsupported clue type for semantic evaluation: {t}")
