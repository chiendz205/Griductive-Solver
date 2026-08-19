"""
Automatic CNF Encoder for Griductive Clues.
Converts any clue or set of clues into Conjunctive Normal Form (CNF) clauses.
Supports core clues (FACT, SAME, DIFFERENT, EXACTLY, AT_LEAST, AT_MOST)
and extension clues (PARITY, BETWEEN).
"""

from typing import List, Dict, Tuple, Set, Any
from itertools import combinations
from griductive.core.models import Status, ClueData, ClueType, ParityType, Region, RegionType, Character
from griductive.core.var_map import VariableManager
from griductive.logic.clues import resolve_region_characters


class CNFEncodingResult:
    """Stores the output of CNF encoding with detailed metrics."""
    def __init__(self, clauses: List[List[int]], main_vars_count: int, aux_vars_count: int):
        self.clauses: List[List[int]] = clauses
        self.main_vars_count: int = main_vars_count
        self.aux_vars_count: int = aux_vars_count
        self.total_vars_count: int = main_vars_count + aux_vars_count
        self.clauses_count: int = len(clauses)

    def summary(self) -> str:
        return (f"CNF Encoded: {self.main_vars_count} main vars, "
                f"{self.aux_vars_count} aux vars, {self.clauses_count} clauses.")


class CNFEncoder:
    """
    Automatic CNF Encoder for Griductive Logic Clues.
    """

    def __init__(self, var_mgr: VariableManager, characters: Dict[str, Character], grid_size: int):
        self.var_mgr = var_mgr
        self.characters = characters
        self.grid_size = grid_size

    def encode_clue(self, clue: ClueData) -> List[List[int]]:
        """Encodes a single clue into CNF clauses."""
        t = clue.clue_type

        if t == ClueType.FACT:
            return self._encode_fact(clue)
        elif t == ClueType.SAME:
            return self._encode_same(clue)
        elif t == ClueType.DIFFERENT:
            return self._encode_different(clue)
        elif t == ClueType.EXACTLY:
            return self._encode_exactly(clue)
        elif t == ClueType.AT_LEAST:
            return self._encode_at_least(clue)
        elif t == ClueType.AT_MOST:
            return self._encode_at_most(clue)
        elif t == ClueType.PARITY:
            return self._encode_parity(clue)
        elif t == ClueType.BETWEEN:
            return self._encode_between(clue)
        else:
            raise ValueError(f"Unknown clue type: {t}")

    def encode_clues(self, clues: List[ClueData]) -> CNFEncodingResult:
        """Encodes a list of clues into a unified CNF formula with metrics."""
        all_clauses: List[List[int]] = []
        for clue in clues:
            clauses = self.encode_clue(clue)
            all_clauses.extend(clauses)

        return CNFEncodingResult(
            clauses=all_clauses,
            main_vars_count=self.var_mgr.main_vars_count,
            aux_vars_count=self.var_mgr.aux_vars_count
        )

    # --- Individual Encoders ---

    def _encode_fact(self, clue: ClueData) -> List[List[int]]:
        person = clue.params["person"]
        expected_status = Status(clue.params["person_status"] if "person_status" in clue.params else clue.params["status"])
        var_id = self.var_mgr.get_var(person)
        if expected_status == Status.CRIMINAL:
            return [[var_id]]
        else:
            return [[-var_id]]

    def _encode_same(self, clue: ClueData) -> List[List[int]]:
        v1 = self.var_mgr.get_var(clue.params["person1"])
        v2 = self.var_mgr.get_var(clue.params["person2"])
        # v1 <=> v2 : (-v1 v v2) ^ (v1 v -v2)
        return [[-v1, v2], [v1, -v2]]

    def _encode_different(self, clue: ClueData) -> List[List[int]]:
        v1 = self.var_mgr.get_var(clue.params["person1"])
        v2 = self.var_mgr.get_var(clue.params["person2"])
        # v1 XOR v2 : (v1 v v2) ^ (-v1 v -v2)
        return [[v1, v2], [-v1, -v2]]

    def _get_k(self, clue: ClueData) -> int:
        return clue.params.get("k", clue.params.get("count", 0))

    def _get_region(self, clue: ClueData) -> Region:
        reg = clue.params.get("region")
        if isinstance(reg, Region):
            return reg
        if isinstance(reg, dict):
            return Region.from_dict(reg)
        if "region_type" in clue.params:
            return Region(RegionType(clue.params["region_type"]), clue.params.get("target_id") or clue.params.get("param"))
        raise ValueError(f"Cannot parse region from clue params: {clue.params}")

    def _encode_at_most(self, clue: ClueData) -> List[List[int]]:
        k = self._get_k(clue)
        region = self._get_region(clue)
        char_ids = resolve_region_characters(region, self.characters, self.grid_size)
        vars_list = [self.var_mgr.get_var(cid) for cid in char_ids]
        return self._encode_cardinality_at_most(vars_list, k)

    def _encode_at_least(self, clue: ClueData) -> List[List[int]]:
        k = self._get_k(clue)
        region = self._get_region(clue)
        char_ids = resolve_region_characters(region, self.characters, self.grid_size)
        vars_list = [self.var_mgr.get_var(cid) for cid in char_ids]
        return self._encode_cardinality_at_least(vars_list, k)

    def _encode_exactly(self, clue: ClueData) -> List[List[int]]:
        k = self._get_k(clue)
        region = self._get_region(clue)
        char_ids = resolve_region_characters(region, self.characters, self.grid_size)
        vars_list = [self.var_mgr.get_var(cid) for cid in char_ids]
        clauses = []
        clauses.extend(self._encode_cardinality_at_most(vars_list, k))
        clauses.extend(self._encode_cardinality_at_least(vars_list, k))
        return clauses

    def _encode_parity(self, clue: ClueData) -> List[List[int]]:
        parity = ParityType(clue.params["parity_type"])
        region = self._get_region(clue)
        char_ids = resolve_region_characters(region, self.characters, self.grid_size)
        vars_list = [self.var_mgr.get_var(cid) for cid in char_ids]
        
        n = len(vars_list)
        if n == 0:
            return [] if parity == ParityType.EVEN else [[1], [-1]] # UNSAT for ODD on 0 vars
        
        if n == 1:
            var = vars_list[0]
            # 1 var: EVEN means 0 criminals (INOCENT = -var), ODD means 1 criminal (CRIMINAL = var)
            return [[-var]] if parity == ParityType.EVEN else [[var]]

        # Using auxiliary variables for XOR chain
        # p_1 = v1 XOR v2
        # p_2 = p1 XOR v3
        # ...
        # p_{n-1} = p_{n-2} XOR v_n
        prev_p = vars_list[0]
        clauses: List[List[int]] = []

        for i in range(1, n):
            current_var = vars_list[i]
            if i == n - 1:
                # Last step: directly enforce parity constraint on (prev_p XOR current_var)
                # If EVEN, prev_p XOR current_var == 0 => prev_p == current_var
                # If ODD,  prev_p XOR current_var == 1 => prev_p != current_var
                if parity == ParityType.EVEN:
                    # prev_p == current_var
                    clauses.extend([[-prev_p, current_var], [prev_p, -current_var]])
                else:
                    # prev_p != current_var
                    clauses.extend([[prev_p, current_var], [-prev_p, -current_var]])
            else:
                next_p = self.var_mgr.allocate_aux_var()
                # next_p <=> (prev_p XOR current_var)
                # CNF for p <=> (a XOR b):
                # (-p v a v b), (-p v -a v -b), (p v -a v b), (p v a v -b)
                clauses.append([-next_p, prev_p, current_var])
                clauses.append([-next_p, -prev_p, -current_var])
                clauses.append([next_p, -prev_p, current_var])
                clauses.append([next_p, prev_p, -current_var])
                prev_p = next_p

        return clauses

    def _encode_between(self, clue: ClueData) -> List[List[int]]:
        char1 = clue.params["char1"]
        char2 = clue.params["char2"]
        target_status = Status(clue.params["target_status"])
        region = Region(RegionType.BETWEEN_CELLS, [char1, char2])
        char_ids = resolve_region_characters(region, self.characters, self.grid_size)

        clauses = []
        for cid in char_ids:
            var_id = self.var_mgr.get_var(cid)
            if target_status == Status.CRIMINAL:
                clauses.append([var_id])
            else:
                clauses.append([-var_id])
        return clauses

    # --- Cardinality Helper Encodings ---

    def _encode_cardinality_at_most(self, vars_list: List[int], k: int) -> List[List[int]]:
        n = len(vars_list)
        if k < 0:
            return [[1], [-1]] # UNSAT
        if k >= n:
            return [] # Tautology

        if n <= 10:
            # Combinatorial subset encoding
            # For at most k, no subset of size k+1 can be all true
            clauses = []
            for combo in combinations(vars_list, k + 1):
                clauses.append([-v for v in combo])
            return clauses
        else:
            # Sequential Counter encoding for larger n
            return self._sequential_counter_at_most(vars_list, k)

    def _encode_cardinality_at_least(self, vars_list: List[int], k: int) -> List[List[int]]:
        n = len(vars_list)
        if k <= 0:
            return [] # Tautology
        if k > n:
            return [[1], [-1]] # UNSAT

        if n <= 10:
            # Combinatorial subset encoding
            # For at least k out of n, at most n-k can be false.
            # So no subset of size n-k+1 can be all false.
            clauses = []
            for combo in combinations(vars_list, n - k + 1):
                clauses.append([v for v in combo])
            return clauses
        else:
            # Convert AT_LEAST(k, vars) to AT_MOST(n-k, negated_vars)
            negated_vars = [-v for v in vars_list]
            return self._sequential_counter_at_most(negated_vars, n - k)

    def _sequential_counter_at_most(self, vars_list: List[int], k: int) -> List[List[int]]:
        """Sequential counter encoding for AtMost(k, vars_list)."""
        n = len(vars_list)
        if k == 0:
            return [[-v] for v in vars_list]
        
        # Matrix S[i][j] for 1 <= i <= n-1, 1 <= j <= k
        S = {}
        for i in range(1, n):
            for j in range(1, k + 1):
                S[(i, j)] = self.var_mgr.allocate_aux_var()

        clauses = []

        # i = 1
        x1 = vars_list[0]
        clauses.append([-x1, S[(1, 1)]])
        for j in range(2, k + 1):
            clauses.append([-S[(1, j)]])

        # 1 < i < n
        for i in range(2, n):
            xi = vars_list[i - 1]
            clauses.append([-xi, S[(i, 1)]])
            clauses.append([-S[(i - 1, 1)], S[(i, 1)]])
            for j in range(2, k + 1):
                clauses.append([-xi, -S[(i - 1, j - 1)], S[(i, j)]])
                clauses.append([-S[(i - 1, j)], S[(i, j)]])
            # Overflow clause
            clauses.append([-xi, -S[(i - 1, k)]])

        # i = n (last variable overflow)
        xn = vars_list[-1]
        clauses.append([-xn, -S[(n - 1, k)]])

        return clauses
