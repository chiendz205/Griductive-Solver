"""
Clue definition and region resolution helpers.
"""

from typing import List, Dict, Tuple, Set, Any
from griductive.core.models import Character, Region, RegionType, ClueData, ClueType


def resolve_region_characters(
    region: Region,
    characters: Dict[str, Character],
    grid_size: int
) -> List[str]:
    """
    Resolves a Region object into a list of character IDs.
    Returns character IDs in deterministic sorted order.
    """
    result: Set[str] = set()

    if region.region_type == RegionType.ROW:
        target_row = int(region.param)
        for char in characters.values():
            if char.row == target_row:
                result.add(char.id)

    elif region.region_type == RegionType.COLUMN:
        target_col = region.param
        if isinstance(target_col, str):
            col_num = ord(target_col.upper()) - ord('A') + 1
        else:
            col_num = int(target_col)

        for char in characters.values():
            if char.col == col_num:
                result.add(char.id)

    elif region.region_type == RegionType.NEIGHBORS:
        center_id = str(region.param)
        if center_id in characters:
            center = characters[center_id]
            for char in characters.values():
                if char.id == center_id:
                    continue
                # 8-way neighborhood check
                if abs(char.row - center.row) <= 1 and abs(char.col - center.col) <= 1:
                    result.add(char.id)

    elif region.region_type == RegionType.EXPLICIT:
        explicit_ids = list(region.param)
        for char_id in explicit_ids:
            if char_id in characters:
                result.add(char_id)

    elif region.region_type == RegionType.BETWEEN_CELLS:
        char1_id, char2_id = region.param[0], region.param[1]
        if char1_id in characters and char2_id in characters:
            c1 = characters[char1_id]
            c2 = characters[char2_id]
            
            # Check if same row
            if c1.row == c2.row:
                min_c, max_c = min(c1.col, c2.col), max(c1.col, c2.col)
                for char in characters.values():
                    if char.row == c1.row and min_c < char.col < max_c:
                        result.add(char.id)
            # Check if same column
            elif c1.col == c2.col:
                min_r, max_r = min(c1.row, c2.row), max(c1.row, c2.row)
                for char in characters.values():
                    if char.col == c1.col and min_r < char.row < max_r:
                        result.add(char.id)

    # Sort deterministically
    return sorted(list(result))


# --- Deep Semantic Validation of Clue Parameters ---
# The JSON schema only checks that `params` is an object; these helpers verify
# that each clue actually carries the parameters its type requires and that
# every referenced character / region is well-formed. Raise ValueError on any
# malformed clue with a message that pinpoints the offending clue id.

_VALID_STATUSES = {"CRIMINAL", "INNOCENT"}
_VALID_PARITIES = {"EVEN", "ODD"}


def _validate_region(clue: ClueData, params: Dict[str, Any], char_ids: Set[str], grid_size: int):
    if "region" not in params:
        raise ValueError(f"Clue '{clue.id}' ({clue.clue_type.value}) is missing required param 'region'.")
    reg = params["region"]
    if not isinstance(reg, dict) or "type" not in reg:
        raise ValueError(f"Clue '{clue.id}' has a malformed 'region' (expected an object with a 'type').")

    rtype = reg.get("type")
    rparam = reg.get("param")

    if rtype == "ROW":
        if not isinstance(rparam, int) or not (1 <= rparam <= grid_size):
            raise ValueError(f"Clue '{clue.id}' ROW region 'param' must be an int in 1..{grid_size}, got {rparam!r}.")
    elif rtype == "COLUMN":
        ok = (isinstance(rparam, int) and 1 <= rparam <= grid_size)
        if isinstance(rparam, str) and len(rparam) == 1 and 0 <= (ord(rparam.upper()) - ord('A')) < grid_size:
            ok = True
        if not ok:
            raise ValueError(f"Clue '{clue.id}' COLUMN region 'param' must be a valid column (1..{grid_size} or A..), got {rparam!r}.")
    elif rtype == "EXPLICIT":
        if not isinstance(rparam, (list, tuple)) or len(rparam) == 0:
            raise ValueError(f"Clue '{clue.id}' EXPLICIT region 'param' must be a non-empty list of character ids.")
        for cid in rparam:
            if cid not in char_ids:
                raise ValueError(f"Clue '{clue.id}' EXPLICIT region references unknown character '{cid}'.")
    elif rtype == "NEIGHBORS":
        center = rparam if isinstance(rparam, str) else params.get("target_id")
        if center not in char_ids:
            raise ValueError(f"Clue '{clue.id}' NEIGHBORS region references unknown center character '{center}'.")
    elif rtype == "BETWEEN_CELLS":
        if not isinstance(rparam, (list, tuple)) or len(rparam) != 2:
            raise ValueError(f"Clue '{clue.id}' BETWEEN_CELLS region 'param' must be a pair of character ids.")
        for cid in rparam:
            if cid not in char_ids:
                raise ValueError(f"Clue '{clue.id}' BETWEEN_CELLS region references unknown character '{cid}'.")
    else:
        raise ValueError(f"Clue '{clue.id}' has unknown region type '{rtype}'.")


def validate_clue_semantics(clue: ClueData, char_ids: Set[str], grid_size: int):
    """
    Deep-validates a single clue's params against the requirements of its type.
    Raises ValueError (with the clue id) if anything is missing or references an
    unknown character. This runs in addition to (after) JSON-schema validation.
    """
    p = clue.params or {}
    t = clue.clue_type

    def check_person(key: str):
        pid = p.get(key)
        if pid not in char_ids:
            raise ValueError(f"Clue '{clue.id}' ({t.value}) references unknown character {pid!r} in param '{key}'.")

    if t == ClueType.FACT:
        if "person" not in p:
            raise ValueError(f"Clue '{clue.id}' (FACT) is missing required param 'person'.")
        check_person("person")
        status = p.get("status", p.get("person_status"))
        if status not in _VALID_STATUSES:
            raise ValueError(f"Clue '{clue.id}' (FACT) has invalid status {status!r} (expected CRIMINAL or INNOCENT).")

    elif t in (ClueType.SAME, ClueType.DIFFERENT):
        for key in ("person1", "person2"):
            if key not in p:
                raise ValueError(f"Clue '{clue.id}' ({t.value}) is missing required param '{key}'.")
            check_person(key)

    elif t in (ClueType.EXACTLY, ClueType.AT_LEAST, ClueType.AT_MOST):
        if "k" not in p and "count" not in p:
            raise ValueError(f"Clue '{clue.id}' ({t.value}) is missing required param 'k'.")
        k = p.get("k", p.get("count"))
        if not isinstance(k, int) or k < 0:
            raise ValueError(f"Clue '{clue.id}' ({t.value}) has invalid k={k!r} (must be a non-negative int).")
        _validate_region(clue, p, char_ids, grid_size)

    elif t == ClueType.PARITY:
        if "parity_type" not in p:
            raise ValueError(f"Clue '{clue.id}' (PARITY) is missing required param 'parity_type'.")
        if p.get("parity_type") not in _VALID_PARITIES:
            raise ValueError(f"Clue '{clue.id}' (PARITY) has invalid parity_type {p.get('parity_type')!r} (expected EVEN or ODD).")
        _validate_region(clue, p, char_ids, grid_size)

    elif t == ClueType.BETWEEN:
        for key in ("char1", "char2"):
            if key not in p:
                raise ValueError(f"Clue '{clue.id}' (BETWEEN) is missing required param '{key}'.")
            check_person(key)
        if p.get("target_status") not in _VALID_STATUSES:
            raise ValueError(f"Clue '{clue.id}' (BETWEEN) has invalid target_status {p.get('target_status')!r} (expected CRIMINAL or INNOCENT).")

    else:
        raise ValueError(f"Clue '{clue.id}' has unknown clue type '{t}'.")
