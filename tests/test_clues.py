from griductive.logic.clues import resolve_region_characters
from griductive.core.models import Character, Region, RegionType, Status

def test_resolve_neighbors():
    # Setup 3x3 grid
    chars = {
        "A1": Character("A1", "A", "Job", 1, 1, Status.INNOCENT, Status.UNKNOWN, []),
        "A2": Character("A2", "B", "Job", 1, 2, Status.INNOCENT, Status.UNKNOWN, []),
        "B2": Character("B2", "C", "Job", 2, 2, Status.INNOCENT, Status.UNKNOWN, []),
    }
    # Region NEIGHBORS của A1 là A2 và B2
    region = Region(region_type=RegionType.NEIGHBORS, param="A1")
    resolved = resolve_region_characters(region, chars, 3)
    
    assert "A2" in resolved
    assert "B2" in resolved
    assert "A1" not in resolved 
    assert len(resolved) == 2

def test_resolve_row():
    chars = {
        "A1": Character("A1", "Alice", "Job", 1, 1, Status.INNOCENT, Status.UNKNOWN, []),
        "A2": Character("A2", "Bob", "Job", 1, 2, Status.INNOCENT, Status.UNKNOWN, []),
        "B1": Character("B1", "Charlie", "Job", 2, 1, Status.INNOCENT, Status.UNKNOWN, []),
    }
    region = Region(region_type=RegionType.ROW, param=1)
    resolved = resolve_region_characters(region, chars, 3)
    
    assert "A1" in resolved
    assert "A2" in resolved
    assert "B1" not in resolved
    assert len(resolved) == 2