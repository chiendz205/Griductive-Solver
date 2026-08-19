"""
LogicAgent implementation for Griductive Solver.
Uses Propositional Logic, CNF Encoding, and DPLL SAT Solver.
Strictly adheres to PublicKBInterface - NEVER accesses secret puzzle state.
"""

from typing import List, Dict, Tuple, Optional, Any
from griductive.core.models import Status, VerdictStatus, Character, ClueData, PublicKBState
from griductive.core.var_map import VariableManager
from griductive.engine.interfaces import PublicKBInterface
from griductive.logic.cnf_encoder import CNFEncoder
from griductive.logic.dpll import DPLLSolver, DPLLStats


class LogicAgent:
    """
    Autonomous AI Logic Agent.
    Interacts with GameEngine exclusively through PublicKBInterface.
    """

    def __init__(self, kb_interface: PublicKBInterface):
        self.kb = kb_interface

    def classify_character(self, character_id: str) -> Tuple[Status, DPLLStats, Dict[str, Any]]:
        """
        Classifies entailment status of a character based strictly on current public KB.

        Returns:
            (status, combined_dpll_stats, debug_info)
            status can be CRIMINAL, INNOCENT, UNKNOWN, or INCONSISTENT.

        debug_info always contains:
            - sat_queries:        number of DPLL SAT solver invocations used here
            - active_clue_ids:    identifiers of every clue currently in the public KB
            - relevant_clue_ids:  identifiers of the clues that constrain this character
            - cnf_summary:        human-readable CNF encoding summary
        """
        public_chars = self.kb.get_public_characters()
        if character_id not in public_chars:
            raise KeyError(f"Character '{character_id}' not found in public KB.")

        char = public_chars[character_id]
        char_list = list(public_chars.values())
        var_mgr = VariableManager(char_list)
        encoder = CNFEncoder(var_mgr, public_chars, self.kb.get_grid_size())

        revealed_clues = self.kb.get_revealed_clues()
        encoding_res = encoder.encode_clues(revealed_clues)
        clauses = list(encoding_res.clauses)

        # Add proven verdicts as unit clauses
        proven_verdicts = self.kb.get_proven_verdicts()
        for p_id, p_stat in proven_verdicts.items():
            v_id = var_mgr.get_var(p_id)
            if p_stat == Status.CRIMINAL:
                clauses.append([v_id])
            elif p_stat == Status.INNOCENT:
                clauses.append([-v_id])

        # Active KB = every revealed clue; Relevant = those touching this character.
        active_clue_ids = [c.id for c in revealed_clues]
        relevant_clue_ids = self._relevant_clue_ids(char, revealed_clues, public_chars)

        solver = DPLLSolver()
        target_var = var_mgr.get_var(character_id)
        all_vars = list(range(1, var_mgr.total_vars_count + 1))

        combined_stats = DPLLStats()
        sat_queries = 0

        def make_debug(**extra: Any) -> Dict[str, Any]:
            base = {
                "sat_queries": sat_queries,
                "active_clue_ids": list(active_clue_ids),
                "relevant_clue_ids": list(relevant_clue_ids),
                "cnf_summary": encoding_res.summary(),
            }
            base.update(extra)
            return base

        # Step 0: Check if KB itself is UNSAT
        kb_sat, _, s0 = solver.solve(clauses, all_vars)
        sat_queries += 1
        self._accumulate_stats(combined_stats, s0)
        if not kb_sat:
            return Status.INCONSISTENT, combined_stats, make_debug(reason="Base KB is UNSAT")

        # Step 1: Test KB ^ NOT_Ci (Assumes character is INNOCENT, i.e., -target_var)
        sat_neg, model_neg, s1 = solver.solve(clauses, all_vars, assumptions=[-target_var])
        sat_queries += 1
        self._accumulate_stats(combined_stats, s1)

        if not sat_neg:
            # KB ^ NOT_Ci is UNSAT => Ci MUST BE CRIMINAL
            return Status.CRIMINAL, combined_stats, make_debug(sat_neg=False, sat_pos=True)

        # Step 2: Test KB ^ Ci (Assumes character is CRIMINAL, i.e., +target_var)
        sat_pos, model_pos, s2 = solver.solve(clauses, all_vars, assumptions=[target_var])
        sat_queries += 1
        self._accumulate_stats(combined_stats, s2)

        if not sat_pos:
            # KB ^ Ci is UNSAT => Ci MUST BE INNOCENT
            return Status.INNOCENT, combined_stats, make_debug(sat_neg=True, sat_pos=False)

        # Both SAT => UNKNOWN
        return Status.UNKNOWN, combined_stats, make_debug(sat_neg=True, sat_pos=True)

    def provide_hint(self) -> Optional[Dict[str, Any]]:
        """
        Generates a hint for the user by identifying an entailed character.
        Does NOT peek at secret answer; relies 100% on public KB reasoning.
        """
        public_chars = self.kb.get_public_characters()
        revealed_clues = self.kb.get_revealed_clues()
        clue_by_id = {c.id: c for c in revealed_clues}

        # Sort unrevealed characters deterministically by row-major order (row, col)
        unrevealed = [
            c for c in public_chars.values()
            if c.revealed_status == Status.UNKNOWN
        ]
        unrevealed.sort(key=lambda c: (c.row, c.col))

        for char in unrevealed:
            status, stats, debug = self.classify_character(char.id)
            if status in (Status.CRIMINAL, Status.INNOCENT):
                relevant_ids = debug.get("relevant_clue_ids", [])
                relevant_clues = [
                    clue_by_id[cid].description
                    for cid in relevant_ids if cid in clue_by_id
                ]

                return {
                    "character_id": char.id,
                    "character_name": char.name,
                    "coord": char.coord,
                    "suggested_status": status.value,
                    "explanation": f"Based on public clues, {char.name} ({char.coord}) is logically forced to be {status.value}.",
                    "relevant_clues": relevant_clues,
                    "relevant_clue_ids": relevant_ids,
                    "active_clue_ids": debug.get("active_clue_ids", []),
                    "sat_queries": debug.get("sat_queries", 0),
                    "dpll_stats": stats.summary()
                }

        return None

    def run_deduction_step(self, game_engine: Any) -> Optional[Dict[str, Any]]:
        """
        Executes a single deduction step:
        Scans characters in row-major order, classifies each against the public KB,
        and submits a verdict for the first one that is logically entailed.

        The returned trace record reports, for this step:
            - the deduced character, its coordinate and forced status
            - active_clue_ids / relevant_clue_ids (which clues drove the deduction)
            - sat_queries (total SAT solver calls made this step, incl. exploration)
            - characters_examined (how many candidates were tested)
            - aggregate DPLL statistics (decisions / propagations / backtracks / runtime)
        """
        public_chars = self.kb.get_public_characters()
        unrevealed = [
            c for c in public_chars.values()
            if c.revealed_status == Status.UNKNOWN
        ]
        # Sort row-major (A1, B1, C1, ...)
        unrevealed.sort(key=lambda c: (c.row, c.col))

        step_stats = DPLLStats()
        step_sat_queries = 0
        examined = 0

        for char in unrevealed:
            status, stats, debug = self.classify_character(char.id)
            examined += 1
            self._accumulate_stats(step_stats, stats)
            step_sat_queries += debug.get("sat_queries", 0)

            if status in (Status.CRIMINAL, Status.INNOCENT):
                # Submit to game engine
                verdict_res = game_engine.submit_verdict(char.id, status)
                return {
                    "character_id": char.id,
                    "character_name": char.name,
                    "coord": char.coord,
                    "forced_status": status.value,
                    "verdict_status": verdict_res.status.value,
                    "message": verdict_res.message,
                    "newly_revealed_clues": [c.to_dict() for c in verdict_res.newly_revealed_clues],
                    "active_clue_ids": debug.get("active_clue_ids", []),
                    "relevant_clue_ids": debug.get("relevant_clue_ids", []),
                    "sat_queries": step_sat_queries,
                    "characters_examined": examined,
                    "solver_stats": step_stats.summary(),
                    "decisions": step_stats.decisions_count,
                    "propagations": step_stats.propagations_count,
                    "backtracks": step_stats.backtracks_count,
                    "runtime_ms": step_stats.runtime_ms
                }

        return None

    def run_full_deduction_loop(self, game_engine: Any) -> List[Dict[str, Any]]:
        """
        Runs full deduction loop until puzzle is solved or no further character is entailed.
        Returns complete deduction trace.
        """
        trace: List[Dict[str, Any]] = []
        step = 1

        while True:
            step_result = self.run_deduction_step(game_engine)
            if step_result is None:
                break
            step_result["step"] = step
            trace.append(step_result)
            step += 1

        return trace

    def _relevant_clue_ids(
        self,
        char: Character,
        revealed_clues: List[ClueData],
        public_chars: Dict[str, Character]
    ) -> List[str]:
        """
        Returns the identifiers of clues that directly constrain `char`:
        clues that name it, clues it owns, or clues whose region contains it.
        """
        relevant: List[str] = []
        for clue in revealed_clues:
            params = clue.params or {}
            is_rel = False

            if clue.owner_id == char.id:
                is_rel = True

            for key in ("person", "person1", "person2", "char1", "char2"):
                if params.get(key) == char.id:
                    is_rel = True

            region = params.get("region")
            if isinstance(region, dict):
                rtype = region.get("type")
                rparam = region.get("param")
                if rtype == "ROW" and rparam == char.row:
                    is_rel = True
                elif rtype == "COLUMN" and (rparam == char.col or str(rparam).upper() == char.col_letter):
                    is_rel = True
                elif rtype == "EXPLICIT" and isinstance(rparam, (list, tuple)) and char.id in rparam:
                    is_rel = True
                elif rtype == "NEIGHBORS":
                    center_id = rparam if isinstance(rparam, str) else params.get("target_id")
                    center = public_chars.get(center_id) if center_id else None
                    if (center and center.id != char.id
                            and abs(center.row - char.row) <= 1
                            and abs(center.col - char.col) <= 1):
                        is_rel = True

            if is_rel:
                relevant.append(clue.id)

        return relevant

    def _accumulate_stats(self, target: DPLLStats, source: DPLLStats):
        target.decisions_count += source.decisions_count
        target.propagations_count += source.propagations_count
        target.backtracks_count += source.backtracks_count
        target.runtime_ms += source.runtime_ms
