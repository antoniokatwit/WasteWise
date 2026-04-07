"""
WasteWise — Flask backend
Run:  pip install flask
      python app.py
Then open http://localhost:5000
"""

import os
import sqlite3
from flask import Flask, jsonify, send_from_directory

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))
DB   = os.path.join(BASE, "wastewise.db")

# ── App ───────────────────────────────────────────────────────────────────────
# static_folder="." lets Flask serve style.css automatically from the same dir
app = Flask(__name__, static_folder=".", static_url_path="")


# ── Database helpers ──────────────────────────────────────────────────────────
def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Create tables and seed data from waste.sql."""
    schema_path = os.path.join(BASE, "waste.sql")
    conn = get_db()
    with open(schema_path, encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print("[WasteWise] Database initialised from waste.sql")


# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    """Serve the single-page app."""
    return send_from_directory(BASE, "index.html")


@app.route("/api/items")
def api_items():
    """
    Return all items with their components as JSON.

    Response shape:
    [
      {
        "id": 1,
        "name": "Coffee Cup and Lid",
        "description": "...",
        "needs_disassembly": true,
        "disassemble_label": "Take It Apart",
        "components": [
          {"id": 1, "name": "Plastic Lid", "bin": "trash", "sort_order": 1},
          ...
        ]
      },
      ...
    ]
    """
    conn = get_db()

    items = conn.execute("SELECT * FROM items ORDER BY id").fetchall()

    result = []
    for item in items:
        components = conn.execute(
            """
            SELECT id, name, bin, sort_order
            FROM   components
            WHERE  item_id = ?
            ORDER  BY sort_order
            """,
            (item["id"],),
        ).fetchall()

        result.append(
            {
                "id":                item["id"],
                "name":              item["name"],
                "description":       item["description"],
                "needs_disassembly": bool(item["needs_disassembly"]),
                "disassemble_label": item["disassemble_label"],
                "components":        [dict(c) for c in components],
            }
        )

    conn.close()
    return jsonify(result)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not os.path.exists(DB):
        init_db()
    else:
        # Re-init if the DB is empty (e.g., first run after a reset)
        conn = get_db()
        count = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
        conn.close()
        if count == 0:
            init_db()

    print("[WasteWise] Starting at http://localhost:5000")
    app.run(debug=True, port=5000)