"""
Data models and Enums for Griductive Solver.
"""

from enum import Enum
from typing import List, Dict, Tuple, Optional, Any, Set
from dataclasses import dataclass, field


class Status(str, Enum):
    CRIMINAL = "CRIMINAL"
    INNOCENT = "INNOCENT"
    UNKNOWN = "UNKNOWN"
    INCONSISTENT = "INCONSISTENT"


class VerdictStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    NOT_PROVABLE = "NOT_PROVABLE"
    CONTRADICTED = "CONTRADICTED"


class RegionType(str, Enum):
    ROW = "ROW"                     # param: int (1..N)
    COLUMN = "COLUMN"               # param: str ("A".."Z") or int (1..N)
    NEIGHBORS = "NEIGHBORS"         # param: str (character_id) -> 8 adjacent cells
    EXPLICIT = "EXPLICIT"           # param: List[str] (list of character_ids)
    BETWEEN_CELLS = "BETWEEN_CELLS" # param: Tuple[str, str] (char1_id, char2_id)


@dataclass
class Region:
    region_type: RegionType
    param: Any  # Depends on region_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.region_type.value,
            "param": self.param
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Region":
        return cls(
            region_type=RegionType(d["type"]),
            param=d["param"]
        )


class ClueType(str, Enum):
    # Core 6 clue types
    FACT = "FACT"               # person, status
    SAME = "SAME"               # person1, person2
    DIFFERENT = "DIFFERENT"     # person1, person2
    EXACTLY = "EXACTLY"         # k, region
    AT_LEAST = "AT_LEAST"       # k, region
    AT_MOST = "AT_MOST"         # k, region

    # Extension clue types
    PARITY = "PARITY"           # parity_type (EVEN/ODD), region
    BETWEEN = "BETWEEN"         # char1, char2, target_status


class ParityType(str, Enum):
    EVEN = "EVEN"
    ODD = "ODD"


@dataclass
class ClueData:
    id: str
    clue_type: ClueType
    params: Dict[str, Any]
    description: str
    owner_id: str               # Character ID holding this clue
    is_initially_revealed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.clue_type.value,
            "params": self.params,
            "description": self.description,
            "owner_id": self.owner_id,
            "is_initially_revealed": self.is_initially_revealed
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ClueData":
        return cls(
            id=d["id"],
            clue_type=ClueType(d["type"]),
            params=d["params"],
            description=d["description"],
            owner_id=d["owner_id"],
            is_initially_revealed=d.get("is_initially_revealed", False)
        )


@dataclass
class Character:
    id: str                 # e.g., "A1", "B2"
    name: str               # Display name, e.g., "Alice"
    job: str                # e.g., "Doctor"
    row: int                # 1..N
    col: int                # 1..N (1=A, 2=B, etc.)
    true_status: Status     # Secret status: CRIMINAL or INNOCENT
    revealed_status: Status = Status.UNKNOWN
    clue_ids: List[str] = field(default_factory=list)

    @property
    def col_letter(self) -> str:
        return chr(ord('A') + self.col - 1)

    @property
    def coord(self) -> str:
        return f"{self.col_letter}{self.row}"

    def to_dict(self, include_secret: bool = False) -> Dict[str, Any]:
        res = {
            "id": self.id,
            "name": self.name,
            "job": self.job,
            "row": self.row,
            "col": self.col,
            "coord": self.coord,
            "revealed_status": self.revealed_status.value,
            "clue_ids": self.clue_ids
        }
        if include_secret:
            res["true_status"] = self.true_status.value
        return res


@dataclass
class VerdictResult:
    status: VerdictStatus
    character_id: str
    claimed_status: Status
    message: str
    newly_revealed_clues: List[ClueData] = field(default_factory=list)


@dataclass
class PublicKBState:
    grid_size: int
    characters: Dict[str, Character]            # Public view (revealed_status)
    revealed_clues: List[ClueData]
    proven_verdicts: Dict[str, Status]          # character_id -> proven status

    def get_public_character(self, char_id: str) -> Optional[Character]:
        return self.characters.get(char_id)
