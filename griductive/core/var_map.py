"""
Deterministic Boolean Variable Manager for Griductive Solver.
Maps character variables C_i to positive integers (1..N) and allocates auxiliary variables.
"""

from typing import Dict, List, Optional, Set
from griductive.core.models import Character


class VariableManager:
    """
    Manages deterministic propositional variable assignment.
    Main variables:
        C_i (1 <= i <= N^2): True if character i is CRIMINAL, False if INNOCENT.
        Characters are sorted alphabetically by display name (or ID if names match)
        to guarantee 100% deterministic variable mapping.
    Auxiliary variables:
        Allocated sequentially starting from N^2 + 1 for CNF encodings (e.g. Sequential Counter / Parity).
    """

    def __init__(self, characters: List[Character]):
        # Sort characters deterministically by name, then ID
        sorted_chars = sorted(characters, key=lambda c: (c.name.lower(), c.id))

        self._char_to_var: Dict[str, int] = {}
        self._var_to_char: Dict[int, str] = {}
        self._main_vars_count: int = len(sorted_chars)
        self._next_aux_var: int = self._main_vars_count + 1

        for idx, char in enumerate(sorted_chars, start=1):
            self._char_to_var[char.id] = idx
            self._char_to_var[char.name] = idx  # Support lookup by display name as well
            self._var_to_char[idx] = char.id

    @property
    def main_vars_count(self) -> int:
        return self._main_vars_count

    @property
    def total_vars_count(self) -> int:
        return self._next_aux_var - 1

    @property
    def aux_vars_count(self) -> int:
        return self._next_aux_var - 1 - self._main_vars_count

    def get_var(self, char_id: str) -> int:
        """Returns positive integer variable ID for character C_i."""
        if char_id not in self._char_to_var:
            raise KeyError(f"Character ID '{char_id}' not found in VariableManager.")
        return self._char_to_var[char_id]

    def get_char_id(self, var_id: int) -> Optional[str]:
        """Returns character ID for main variable var_id, or None if auxiliary variable."""
        return self._var_to_char.get(var_id)

    def allocate_aux_var(self) -> int:
        """Allocates and returns a new auxiliary variable ID."""
        var = self._next_aux_var
        self._next_aux_var += 1
        return var

    def is_main_var(self, var_id: int) -> bool:
        """Checks if var_id is a primary character variable."""
        return 1 <= abs(var_id) <= self._main_vars_count

    def reset_aux_vars(self):
        """Resets auxiliary variable counter back to N^2 + 1."""
        self._next_aux_var = self._main_vars_count + 1

    def get_all_main_vars(self) -> List[int]:
        """Returns all main variable IDs in deterministic order [1..N^2]."""
        return list(range(1, self._main_vars_count + 1))
