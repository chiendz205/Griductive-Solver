"""
GameEngine implementation.
Owns secret puzzle state, manages public knowledge base, and validates submitted verdicts.
"""

import json
from typing import List, Dict, Tuple, Optional, Any
from jsonschema import validate, ValidationError
from griductive.core.models import (
    Status, VerdictStatus, Character, ClueData, VerdictResult, PublicKBState
)
from griductive.core.var_map import VariableManager
from griductive.engine.interfaces import PublicKBInterface
from griductive.logic.cnf_encoder import CNFEncoder
from griductive.logic.clues import validate_clue_semantics
from griductive.logic.dpll import DPLLSolver


class GameEngine(PublicKBInterface):
    """
    Core GameEngine owning true puzzle state.
    Exposes only public KB via PublicKBInterface.
    """

    def __init__(self):
        self._grid_size: int = 3
        self._characters: Dict[str, Character] = {}
        self._clues: Dict[str, ClueData] = {}
        self._proven_verdicts: Dict[str, Status] = {}
        self._raw_json_data: Optional[Dict[str, Any]] = None

    def load_puzzle_json(self, json_path: str):
        """Loads puzzle configuration from JSON file path."""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Load and validate against schema
        with open('data/puzzle_schema.json', 'r', encoding='utf-8') as f:
            schema = json.load(f)
        
        try:
            validate(instance=data, schema=schema)
        except ValidationError as e:
            raise ValueError(f"Invalid puzzle format: {e.message}")
            
        self.load_puzzle_data(data)

    def load_puzzle_data(self, data: Dict[str, Any]):
        """Loads puzzle configuration from dictionary."""
        self._raw_json_data = data
        self._grid_size = data["grid_size"]
        self._characters = {}
        self._clues = {}
        self._proven_verdicts = {}

        # Parse Characters
        for char_dict in data["characters"]:
            char = Character(
                id=char_dict["id"],
                name=char_dict["name"],
                job=char_dict["job"],
                row=char_dict["row"],
                col=char_dict["col"],
                true_status=Status(char_dict["true_status"]),
                revealed_status=Status.UNKNOWN,
                clue_ids=[]
            )
            self._characters[char.id] = char

        # Parse Clues
        for clue_dict in data["clues"]:
            clue = ClueData.from_dict(clue_dict)
            self._clues[clue.id] = clue
            if clue.owner_id in self._characters:
                self._characters[clue.owner_id].clue_ids.append(clue.id)

        # Deep semantic validation of every clue's params (beyond JSON schema).
        self._validate_puzzle_semantics()

    def _validate_puzzle_semantics(self):
        """
        Validates the loaded puzzle beyond the JSON schema: character coordinates
        must be inside the grid and unique, clue owners must exist, and every
        clue's params must match its type (checked by validate_clue_semantics).
        Raises ValueError on the first problem found.
        """
        n = self._grid_size
        seen_coords = {}
        for char in self._characters.values():
            if not (1 <= char.row <= n) or not (1 <= char.col <= n):
                raise ValueError(
                    f"Character '{char.id}' has out-of-range coordinate "
                    f"(row={char.row}, col={char.col}) for a {n}x{n} grid."
                )
            coord = (char.row, char.col)
            if coord in seen_coords:
                raise ValueError(
                    f"Characters '{seen_coords[coord]}' and '{char.id}' share the "
                    f"same cell (row={char.row}, col={char.col})."
                )
            seen_coords[coord] = char.id

        char_ids = set(self._characters.keys())
        for clue in self._clues.values():
            if clue.owner_id not in char_ids:
                raise ValueError(f"Clue '{clue.id}' has unknown owner_id '{clue.owner_id}'.")
            validate_clue_semantics(clue, char_ids, n)

    def restart(self):
        """Restores puzzle to initial starting state."""
        if self._raw_json_data:
            self.load_puzzle_data(self._raw_json_data)

    # --- PublicKBInterface Implementation ---

    def get_grid_size(self) -> int:
        return self._grid_size

    def get_public_characters(self) -> Dict[str, Character]:
        """Returns character objects containing ONLY revealed status."""
        public_map: Dict[str, Character] = {}
        for cid, char in self._characters.items():
            public_map[cid] = Character(
                id=char.id,
                name=char.name,
                job=char.job,
                row=char.row,
                col=char.col,
                true_status=Status.UNKNOWN,  # Hide true status!
                revealed_status=char.revealed_status,
                clue_ids=list(char.clue_ids)
            )
        return public_map

    def get_revealed_clues(self) -> List[ClueData]:
        """Returns only currently revealed clues."""
        return [clue for clue in self._clues.values() if clue.is_initially_revealed]

    def get_proven_verdicts(self) -> Dict[str, Status]:
        return dict(self._proven_verdicts)

    def get_public_kb_state(self) -> PublicKBState:
        return PublicKBState(
            grid_size=self.get_grid_size(),
            characters=self.get_public_characters(),
            revealed_clues=self.get_revealed_clues(),
            proven_verdicts=self.get_proven_verdicts()
        )

    # --- Verdict Submission & Validation ---

    def submit_verdict(self, character_id: str, claimed_status: Status) -> VerdictResult:
        """
        Submits a verdict for a character.
        Validates if claimed_status is logically ENTAILED by current public KB.
        Returns VerdictResult with ACCEPTED, NOT_PROVABLE, or CONTRADICTED.
        """
        if character_id not in self._characters:
            raise ValueError(f"Unknown character ID: {character_id}")

        char = self._characters[character_id]
        if char.revealed_status != Status.UNKNOWN:
            return VerdictResult(
                status=VerdictStatus.ACCEPTED,
                character_id=character_id,
                claimed_status=char.revealed_status,
                message=f"Character '{char.name}' is already revealed as {char.revealed_status.value}."
            )

        # Entailment check using current public KB
        entailed_status = self._check_public_entailment(character_id)

        if entailed_status == claimed_status:
            # ACCEPTED!
            char.revealed_status = claimed_status
            self._proven_verdicts[character_id] = claimed_status

            # Reveal new clues owned by this character
            newly_revealed: List[ClueData] = []
            for clue_id in char.clue_ids:
                clue = self._clues[clue_id]
                if not clue.is_initially_revealed:
                    clue.is_initially_revealed = True
                    newly_revealed.append(clue)

            return VerdictResult(
                status=VerdictStatus.ACCEPTED,
                character_id=character_id,
                claimed_status=claimed_status,
                message=f"Verdict ACCEPTED! {char.name} is proven to be {claimed_status.value}.",
                newly_revealed_clues=newly_revealed
            )
        elif entailed_status != Status.UNKNOWN:
            # CONTRADICTED! (Opposite state is entailed)
            return VerdictResult(
                status=VerdictStatus.CONTRADICTED,
                character_id=character_id,
                claimed_status=claimed_status,
                message=f"Verdict CONTRADICTED! The opposite state ({entailed_status.value}) is logically entailed."
            )
        else:
            # NOT_PROVABLE! (Neither status is entailed by current public KB)
            return VerdictResult(
                status=VerdictStatus.NOT_PROVABLE,
                character_id=character_id,
                claimed_status=claimed_status,
                message=f"Verdict NOT_PROVABLE! Current public clues are insufficient to force {claimed_status.value} for {char.name}."
            )

    def _check_public_entailment(self, character_id: str) -> Status:
        """Helper evaluating entailment strictly against current public KB."""
        public_chars = self.get_public_characters()
        char_list = list(public_chars.values())
        var_mgr = VariableManager(char_list)
        encoder = CNFEncoder(var_mgr, public_chars, self._grid_size)

        revealed_clues = self.get_revealed_clues()
        encoding_res = encoder.encode_clues(revealed_clues)
        clauses = list(encoding_res.clauses)

        # Add proven verdicts as unit clauses
        for p_id, p_stat in self._proven_verdicts.items():
            v_id = var_mgr.get_var(p_id)
            if p_stat == Status.CRIMINAL:
                clauses.append([v_id])
            elif p_stat == Status.INNOCENT:
                clauses.append([-v_id])

        solver = DPLLSolver()
        target_var = var_mgr.get_var(character_id)
        all_vars = list(range(1, var_mgr.total_vars_count + 1))

        # Check CRIMINAL entailment: KB ^ NOT_C is UNSAT?
        is_sat_neg, _, _ = solver.solve(clauses, all_vars, assumptions=[-target_var])
        if not is_sat_neg:
            return Status.CRIMINAL

        # Check INNOCENT entailment: KB ^ C is UNSAT?
        is_sat_pos, _, _ = solver.solve(clauses, all_vars, assumptions=[target_var])
        if not is_sat_pos:
            return Status.INNOCENT

        return Status.UNKNOWN

    # --- Full Secret Uniqueness Check ---

    def _encode_full_puzzle(self) -> Tuple[VariableManager, Any]:
        """Encodes ALL clues (including hidden ones) into a single CNF formula."""
        all_chars = self._characters
        char_list = list(all_chars.values())
        var_mgr = VariableManager(char_list)
        encoder = CNFEncoder(var_mgr, all_chars, self._grid_size)
        encoding_res = encoder.encode_clues(list(self._clues.values()))
        return var_mgr, encoding_res

    def get_full_cnf_metrics(self) -> Dict[str, int]:
        """
        Returns the CNF size of the complete puzzle (all clues encoded together).
        Deterministic and reproducible - used by the experiment benchmark.
        """
        var_mgr, encoding_res = self._encode_full_puzzle()
        return {
            "main_vars": encoding_res.main_vars_count,
            "aux_vars": encoding_res.aux_vars_count,
            "total_vars": encoding_res.total_vars_count,
            "clauses": encoding_res.clauses_count,
        }

    def check_full_puzzle_uniqueness(self) -> Tuple[bool, int]:
        """
        Independent check: counts total satisfying assignments for ALL clues combined.
        Returns (is_unique, solution_count).
        """
        var_mgr, encoding_res = self._encode_full_puzzle()
        clauses = list(encoding_res.clauses)

        solver = DPLLSolver()
        all_vars = list(range(1, var_mgr.total_vars_count + 1))

        solutions_count = 0
        working_clauses = list(clauses)

        while True:
            is_sat, model, _ = solver.solve(working_clauses, all_vars)
            if not is_sat or model is None:
                break

            solutions_count += 1
            if solutions_count > 1:
                break  # More than 1 solution!

            # Block current main variable assignment
            blocking_clause = []
            for v_id in range(1, var_mgr.main_vars_count + 1):
                val = model[v_id]
                blocking_clause.append(-v_id if val else v_id)
            working_clauses.append(blocking_clause)

        return (solutions_count == 1), solutions_count
