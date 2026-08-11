"""
Abstract Protocol / Interface for exposing Public Knowledge Base to LogicAgent.
Guarantees that LogicAgent NEVER accesses secret / unrevealed puzzle data.
"""

from typing import Protocol, List, Dict, Optional
from griductive.core.models import Character, ClueData, Status, PublicKBState


class PublicKBInterface(Protocol):
    """
    Abstract Protocol defining the read-only view of public puzzle data.
    GameEngine implements this protocol. LogicAgent only consumes this protocol.
    """

    def get_grid_size(self) -> int:
        """Returns N (grid dimension)."""
        ...

    def get_public_characters(self) -> Dict[str, Character]:
        """Returns dictionary of characters showing only public/revealed status."""
        ...

    def get_revealed_clues(self) -> List[ClueData]:
        """Returns list of currently revealed clues."""
        ...

    def get_proven_verdicts(self) -> Dict[str, Status]:
        """Returns dictionary of character_id -> proven Status."""
        ...

    def get_public_kb_state(self) -> PublicKBState:
        """Returns complete snapshot of public knowledge base."""
        ...
