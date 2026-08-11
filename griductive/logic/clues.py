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
