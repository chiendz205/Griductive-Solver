# Griductive Solver Demo Video Script

**Target duration:** 8-10 minutes  
**Video URL:** _TBD - add the Google Drive link after uploading_

Read the text under **Narration** and perform the actions under **On screen**.

## 1. Introduction - 0:00 to 0:40

**On screen:** Show the report title or repository and point to the project name and team members.

**Narration:**

> Hello everyone. We are Ngo Trung Nghia and Nguyen Cong Chien. This is our Project 2 for the Introduction to Artificial Intelligence course. Our project is called Griductive Solver.
>
> Griductive is a logic deduction game in which every character is secretly either a criminal or an innocent. The player must use the currently revealed clues to prove each verdict. Guessing is not allowed.
>
> Our system includes a playable web interface, automatic CNF encoding, a DPLL SAT solver written in Python, and a logic agent that can solve the puzzle step by step.

## 2. Start the Application - 0:40 to 1:10

**On screen:** Run `py -3 app.py`, then open `http://127.0.0.1:5000`.

**Narration:**

> First, I start the Flask application by running `py -3 app.py`. The application is now available on localhost.
>
> The interface contains the puzzle selector, the game board, revealed clues, manual verdict controls, a Hint button, a Step button, an Auto Solve button, and the AI deduction trace.

## 3. Load and Explore a Puzzle - 1:10 to 2:10

**On screen:** Select `puzzle_01_3x3_easy.json` and click **Load**. Hover over a revealed clue and click it to pin the highlighted region. Point to coordinates, names, jobs, statuses, and clue-holder indicators.

**Narration:**

> I will begin with the first three-by-three puzzle. When I click Load, the application reads the JSON file, validates its structure and clue parameters, and checks whether the complete puzzle has a unique solution.
>
> The rows are numbered and the columns are labelled with letters, so each character has a coordinate such as A1 or C2. Every card displays the character's name, profession, and currently revealed status.
>
> Only public clues are displayed. When I move the cursor over a clue, the interface highlights the cells referenced by that clue. I can also click the clue to keep the region highlighted.

## 4. Manual Verdicts - 2:10 to 3:10

**On screen:** Select an unresolved character and demonstrate a rejected verdict if possible. Then request a Hint and apply a provable verdict.

**Narration:**

> The player can select a face-down character and submit either Criminal or Innocent.
>
> The game engine does not accept a verdict simply because it matches the hidden solution. It accepts a verdict only when the result is logically entailed by the current public knowledge base.
>
> This verdict is not yet forced, so the result is `NOT_PROVABLE`. The character remains unresolved and its hidden clue is not revealed.
>
> Now I submit a logically provable verdict. The engine returns `ACCEPTED`, updates the character's public status, and reveals the clue owned by that character. The new clue becomes part of the knowledge base for the next deduction step.

If the application returns `CONTRADICTED`, say this instead:

> The opposite status is logically forced, so the engine returns `CONTRADICTED`. The game state remains unchanged and no hidden clue is revealed.

## 5. Hint and One-Step Deduction - 3:10 to 4:30

**On screen:** Click **Hint** and show the suggested character, status, relevant clues, and solver statistics. Then click **Step** and point to the new trace entry.

**Narration:**

> The Hint function asks the logic agent to find one unresolved character whose status is currently forced.
>
> The hint includes the character, the entailed status, relevant clue identifiers, a short explanation, and statistics from the SAT solver. It does not read the hidden solution. It uses only revealed clues and previously proved verdicts.
>
> Next, I click Step. The agent performs exactly one deduction, submits the forced verdict to the game engine, and reveals the corresponding clue.
>
> The deduction trace records the step number, selected character, verdict, active clue identifiers, SAT queries, decisions, propagations, backtracks, runtime, and newly revealed clues. This makes the agent's behavior observable and reproducible.

## 6. Automatic Solve - 4:30 to 5:30

**On screen:** Click **Restart**, then **Auto Solve**. Allow the animation to complete, scroll through trace entries, and show the solved board.

**Narration:**

> I will restart the puzzle and run Auto Solve. The agent scans unresolved characters in deterministic row-major order.
>
> For each character, it tests both possible statuses using SAT queries. It chooses a verdict only when one assumption produces an unsatisfiable formula. After each accepted verdict, the newly revealed clue is added to the public knowledge base and the process continues.
>
> The agent never guesses. It stops when the board is solved, when no further verdict is provable, or when the public knowledge base is inconsistent.
>
> In this puzzle, every character has been resolved successfully.

## 7. Algorithms and Architecture - 5:30 to 7:00

**On screen:** Briefly show `cnf_encoder.py`, `dpll.py`, `logic_agent.py`, `interfaces.py`, and `game_engine.py` in the editor.

**Narration:**

> The system represents each character with one Boolean variable. True means Criminal and False means Innocent. The CNF encoder automatically converts six required clue types: Fact, Same, Different, Exactly, At Least, and At Most. We also implemented two extensions: Parity and Between.
>
> Our SAT solver is a pure-Python implementation of DPLL. It includes unit propagation, conflict detection, deterministic DLCS variable selection, recursive branching, backtracking, assumptions, and execution statistics.
>
> Entailment is different from finding one satisfying model. To prove that a character is Criminal, the agent temporarily assumes that the character is Innocent. If this makes the knowledge base unsatisfiable, Criminal is logically forced. The reverse test is used to prove Innocent.
>
> The architecture separates secret and public information. `GameEngine` owns the hidden solution and unrevealed clues. `LogicAgent` receives only `PublicKBInterface`, which exposes revealed clues and proved verdicts. Therefore, the agent cannot inspect `true_status` to cheat.

## 8. Tests and Experiments - 7:00 to 8:20

**On screen:** Run `py -3 -m pytest -q`, then open `docs/experiment_results.md` or the experiment table in the report.

**Narration:**

> We use automated tests to verify the API, game engine, clue validation, CNF encoding, DPLL solver, logic agent, security boundary, and all sample puzzles.
>
> The current test suite contains sixty-three tests, and all of them pass.
>
> We also created an automatic benchmark for seven puzzles, including three-by-three, four-by-four, and five-by-five boards. For each puzzle, we record primary and auxiliary variables, CNF clauses, SAT queries, decisions, propagations, backtracks, deduction steps, runtime, and uniqueness.
>
> All seven sample puzzles have exactly one solution and are solved completely by the logic agent. The results show that unit propagation performs most of the deductions at this puzzle scale.

## 9. Report and Conclusion - 8:20 to 9:00

**On screen:** Open `docs/Report.pdf` and briefly show the main sections, experiment table, references, and Generative AI Usage appendix.

**Narration:**

> The report describes the problem formulation, CNF derivations, DPLL algorithm, entailment classification, deduction loop, experiments, limitations, references, and our use of Generative AI during development.
>
> In conclusion, our project provides a complete playable Griductive game and a no-guess logical solver. The system automatically represents clues in CNF, proves verdicts with DPLL, reveals clues progressively, and explains each deduction through its trace.
>
> Thank you for watching our demonstration.

## Recording Checklist

- Keep the video between 5 and 10 minutes.
- Record at a readable resolution and zoom level.
- Use this English narration or add readable English subtitles.
- Hide passwords, tokens, personal messages, and unrelated browser tabs.
- Demonstrate manual play, Hint, Step, Auto Solve, tests, and experiments.
- Adapt the narration to the actual verdict response shown on screen.

## After Uploading

1. Upload the video to Google Drive; do not submit a YouTube link.
2. Set access to **Anyone with the link - Viewer**.
3. Test the link in a private or incognito browser window.
4. Replace `_TBD_` above with the final URL.
5. Add the same URL to `docs/Report.md`.
6. Rebuild the PDF with `py -3 tools/build_report_pdf.py`.
