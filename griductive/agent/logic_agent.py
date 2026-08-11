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
        """
        public_chars = self.kb.get_public_characters()
        if character_id not in public_chars:
            raise KeyError(f"Character '{character_id}' not found in public KB.")

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

        solver = DPLLSolver()
        target_var = var_mgr.get_var(character_id)
        all_vars = list(range(1, var_mgr.total_vars_count + 1))

        combined_stats = DPLLStats()

        # Step 0: Check if KB itself is UNSAT
        kb_sat, _, s0 = solver.solve(clauses, all_vars)
        self._accumulate_stats(combined_stats, s0)
        if not kb_sat:
            return Status.INCONSISTENT, combined_stats, {"reason": "Base KB is UNSAT"}

        # Step 1: Test KB ^ NOT_Ci (Assumes character is INNOCENT, i.e., -target_var)
        sat_neg, model_neg, s1 = solver.solve(clauses, all_vars, assumptions=[-target_var])
        self._accumulate_stats(combined_stats, s1)

        if not sat_neg:
            # KB ^ NOT_Ci is UNSAT => Ci MUST BE CRIMINAL
            return Status.CRIMINAL, combined_stats, {
                "sat_neg": False, "sat_pos": True, "cnf_summary": encoding_res.summary()
            }

        # Step 2: Test KB ^ Ci (Assumes character is CRIMINAL, i.e., +target_var)
        sat_pos, model_pos, s2 = solver.solve(clauses, all_vars, assumptions=[target_var])
        self._accumulate_stats(combined_stats, s2)

        if not sat_pos:
            # KB ^ Ci is UNSAT => Ci MUST BE INNOCENT
            return Status.INNOCENT, combined_stats, {
                "sat_neg": True, "sat_pos": False, "cnf_summary": encoding_res.summary()
            }

        # Both SAT => UNKNOWN
        return Status.UNKNOWN, combined_stats, {
            "sat_neg": True, "sat_pos": True, "cnf_summary": encoding_res.summary()
        }

    def provide_hint(self) -> Optional[Dict[str, Any]]:
        """
        Generates a hint for the user by identifying an entailed character.
        Does NOT peek at secret answer; relies 100% on public KB reasoning.
        """
        public_chars = self.kb.get_public_characters()
        pub_state = self.kb.get_public_kb_state()
        
        # Sort unrevealed characters deterministically by row-major order (row, col)
        unrevealed = [
            c for c in public_chars.values()
            if c.revealed_status == Status.UNKNOWN
        ]
        unrevealed.sort(key=lambda c: (c.row, c.col))

        for char in unrevealed:
            status, stats, debug = self.classify_character(char.id)
            if status in (Status.CRIMINAL, Status.INNOCENT):
                # Gather relevant public clues
                relevant_clues = []
                for clue in pub_state.revealed_clues:
                    params = clue.params or {}
                    is_rel = False
                    if params.get('person') == char.id:
                        is_rel = True
                    elif params.get('person1') == char.id or params.get('person2') == char.id:
                        is_rel = True
                    elif params.get('char1') == char.id or params.get('char2') == char.id:
                        is_rel = True
                    
                    region = params.get('region')
                    if region and isinstance(region, dict):
                        rtype = region.get('type')
                        rparam = region.get('param')
                        if rtype == 'ROW' and rparam == char.row:
                            is_rel = True
                        elif rtype == 'COLUMN' and rparam == char.col:
                            is_rel = True
                    
                    if clue.owner_id == char.id:
                        is_rel = True

                    if is_rel:
                        relevant_clues.append(clue.description)

                return {
                    "character_id": char.id,
                    "character_name": char.name,
                    "coord": char.coord,
                    "suggested_status": status.value,
                    "explanation": f"Based on public clues, {char.name} ({char.coord}) is logically forced to be {status.value}.",
                    "relevant_clues": relevant_clues,
                    "dpll_stats": stats.summary()
                }

        return None

    def run_deduction_step(self, game_engine: Any) -> Optional[Dict[str, Any]]:
        """
        Executes a single deduction step:
        Finds an entailed character in row-major order, submits verdict to engine.
        """
        public_chars = self.kb.get_public_characters()
        unrevealed = [
            c for c in public_chars.values()
            if c.revealed_status == Status.UNKNOWN
        ]
        # Sort row-major (A1, B1, C1, ...)
        unrevealed.sort(key=lambda c: (c.row, c.col))

        for char in unrevealed:
            status, stats, debug = self.classify_character(char.id)
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
                    "solver_stats": stats.summary(),
                    "decisions": stats.decisions_count,
                    "propagations": stats.propagations_count,
                    "backtracks": stats.backtracks_count,
                    "runtime_ms": stats.runtime_ms
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

    def _accumulate_stats(self, target: DPLLStats, source: DPLLStats):
        target.decisions_count += source.decisions_count
        target.propagations_count += source.propagations_count
        target.backtracks_count += source.backtracks_count
        target.runtime_ms += source.runtime_ms
