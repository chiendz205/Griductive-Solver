# Griductive Solver - Logic Deduction and DPLL SAT Agent

Griductive Solver is a CSC14003 project that models grid-based logic puzzles with propositional logic, converts clues to CNF, and solves them with a pure-Python DPLL SAT solver. It includes an explainable automatic agent, a Flask REST API, and an interactive web interface.

## Project Structure

```text
griductive/          Core models, logic, engine, and agent
data/                JSON puzzle files and schema
experiments/         Reproducible benchmark script
tests/               Pytest test suite
templates/, static/  Web interface
docs/                Report, experiment results, and demo guide
tools/               Report PDF builder
app.py               Flask entry point
```

## Setup and Run

```powershell
py -3 -m pip install -r requirements.txt
py -3 app.py
```

Open http://127.0.0.1:5000.

## Tests and Coverage

```powershell
py -3 -m pytest -q
py -3 -m pytest -q --cov=griductive --cov-report=term
```

The current suite contains 63 tests and reports 91% package coverage.

## Benchmarks

```powershell
py -3 experiments/benchmark.py
```

This regenerates `docs/experiment_results.md` and `docs/experiment_results.csv` from all puzzles in `data/`.

## Build the Report

```powershell
py -3 tools/build_report_pdf.py
```

The English technical report, including the Generative AI usage appendix, is in `docs/Report.md` and `docs/Report.pdf`.

## Architecture Summary

- `VariableManager` maps characters and auxiliary variables deterministically.
- `CNFEncoder` supports `FACT`, `SAME`, `DIFFERENT`, `EXACTLY`, `AT_LEAST`, `AT_MOST`, `PARITY`, and `BETWEEN` clues.
- `DPLLSolver` implements fixed-point unit propagation, DLCS branching, assumptions, and telemetry without an external SAT library.
- `GameEngine` owns hidden truth; `PublicKBInterface` prevents the agent from reading it.
- `LogicAgent` proves statuses by contradiction, generates hints, and records an explainable deduction trace.
- JSON Schema and semantic validation reject structurally or contextually invalid puzzles.

## Documentation

- `docs/Report.md`: complete project report and AI usage appendix
- `docs/experiment_results.md`: generated benchmark results
- `docs/DEMO_VIDEO.md`: recording and submission checklist
