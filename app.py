"""
Flask Web Application for Griductive Solver.
Provides REST API and UI rendering for Griductive Logic Game & AI Solver.
"""

import os
import glob
import json
from flask import Flask, render_template, jsonify, request
from griductive.core.models import Status, VerdictStatus
from griductive.engine.game_engine import GameEngine
from griductive.agent.logic_agent import LogicAgent

app = Flask(__name__)

# Global GameEngine and LogicAgent instances
game_engine = GameEngine()
logic_agent = LogicAgent(game_engine)

@app.after_request
def add_header(response):
    """Disable browser caching for static files during development."""
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Default puzzle to load at startup
DEFAULT_PUZZLE = os.path.join(DATA_DIR, "puzzle_01_3x3_easy.json")
if os.path.exists(DEFAULT_PUZZLE):
    game_engine.load_puzzle_json(DEFAULT_PUZZLE)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/puzzles', methods=['GET'])
def list_puzzles():
    """Returns list of available sample JSON puzzle files with pretty titles."""
    puzzle_files = glob.glob(os.path.join(DATA_DIR, "puzzle_*.json"))
    puzzles = []
    for filepath in sorted(puzzle_files):
        filename = os.path.basename(filepath)
        if filename == "puzzle_schema.json":
            continue

        title = filename
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                title = data.get("title", filename)
        except Exception as e:
            print(f"Error reading puzzle title from {filename}: {e}")

        puzzles.append({
            "filename": filename,
            "title": title
        })
    return jsonify({"puzzles": puzzles})


@app.route('/api/load', methods=['POST'])
def load_puzzle():
    """Loads a specific puzzle from data/ directory."""
    req_data = request.json or {}
    filename = req_data.get("filename", "puzzle_3x3_easy.json")
    filepath = os.path.join(DATA_DIR, filename)

    if not os.path.exists(filepath):
        return jsonify({"error": f"File {filename} not found."}), 404

    game_engine.load_puzzle_json(filepath)
    is_unique, count = game_engine.check_full_puzzle_uniqueness()

    pub_state = game_engine.get_public_kb_state()
    puzzle_title = game_engine._raw_json_data.get("title", filename) if game_engine._raw_json_data else filename

    return jsonify({
        "message": f"Successfully loaded {puzzle_title}.",
        "title": puzzle_title,
        "grid_size": pub_state.grid_size,
        "characters": [c.to_dict(include_secret=False) for c in pub_state.characters.values()],
        "revealed_clues": [c.to_dict() for c in pub_state.revealed_clues],
        "is_unique": is_unique,
        "uniqueness_count": count
    })


@app.route('/api/restart', methods=['POST'])
def restart_puzzle():
    game_engine.restart()
    pub_state = game_engine.get_public_kb_state()
    return jsonify({
        "message": "Puzzle restarted.",
        "grid_size": pub_state.grid_size,
        "characters": [c.to_dict(include_secret=False) for c in pub_state.characters.values()],
        "revealed_clues": [c.to_dict() for c in pub_state.revealed_clues]
    })


@app.route('/api/state', methods=['GET'])
def get_state():
    pub_state = game_engine.get_public_kb_state()
    return jsonify({
        "grid_size": pub_state.grid_size,
        "characters": [c.to_dict(include_secret=False) for c in pub_state.characters.values()],
        "revealed_clues": [c.to_dict() for c in pub_state.revealed_clues]
    })


@app.route('/api/verdict', methods=['POST'])
def submit_verdict():
    req_data = request.json or {}
    char_id = req_data.get("character_id")
    status_str = req_data.get("status")

    if not char_id or not status_str:
        return jsonify({"error": "Missing character_id or status."}), 400

    try:
        claimed_status = Status(status_str.upper())
        result = game_engine.submit_verdict(char_id, claimed_status)

        pub_state = game_engine.get_public_kb_state()
        return jsonify({
            "verdict_status": result.status.value,
            "character_id": result.character_id,
            "claimed_status": result.claimed_status.value,
            "message": result.message,
            "newly_revealed_clues": [c.to_dict() for c in result.newly_revealed_clues],
            "characters": [c.to_dict(include_secret=False) for c in pub_state.characters.values()],
            "revealed_clues": [c.to_dict() for c in pub_state.revealed_clues]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/api/hint', methods=['GET'])
def get_hint():
    hint = logic_agent.provide_hint()
    if hint is None:
        return jsonify({"message": "No logically forced character found with current public KB.", "hint": None})
    return jsonify({"message": "Hint generated.", "hint": hint})


@app.route('/api/auto-step', methods=['POST'])
def auto_step():
    step_res = logic_agent.run_deduction_step(game_engine)
    pub_state = game_engine.get_public_kb_state()
    return jsonify({
        "step_result": step_res,
        "characters": [c.to_dict(include_secret=False) for c in pub_state.characters.values()],
        "revealed_clues": [c.to_dict() for c in pub_state.revealed_clues]
    })


@app.route('/api/auto-solve', methods=['POST'])
def auto_solve():
    trace = logic_agent.run_full_deduction_loop(game_engine)
    pub_state = game_engine.get_public_kb_state()
    return jsonify({
        "trace": trace,
        "total_steps": len(trace),
        "characters": [c.to_dict(include_secret=False) for c in pub_state.characters.values()],
        "revealed_clues": [c.to_dict() for c in pub_state.revealed_clues]
    })


if __name__ == '__main__':
    print("Starting Griductive Solver Web Server at http://127.0.0.1:5000 ...")
    app.run(host='127.0.0.1', port=5000, debug=True)
