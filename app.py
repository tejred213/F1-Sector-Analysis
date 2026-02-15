#!/usr/bin/env python3
"""
F1 Sector Analysis — Flask API Backend

Wraps the existing sector_analysis.py as a REST API.
Optimized for fast response times with background loading and caching.
In production, also serves the React frontend build.
"""

import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import numpy as np
import fastf1
import threading
import time as _time

from sector_analysis import (
    load_session,
    get_sector_data,
    get_team_colors,
    list_available_drivers,
    compare_two_drivers,
    get_track_dominance_data,
)

# In production, serve React build from frontend/dist
_frontend_dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")
app = Flask(
    __name__,
    static_folder=_frontend_dist,
    static_url_path="",
)
CORS(app)

# Hardcoded team colors (FastF1 plotting often returns #FFF for older seasons)
TEAM_COLORS_FALLBACK = {
    "Red Bull Racing": "#1E41FF",
    "Red Bull": "#3671C6",
    "Mercedes": "#00D2BE",
    "McLaren": "#FF8700",
    "Ferrari": "#DC0000",
    "Alpine": "#0090FF",
    "Alpine F1 Team": "#0090FF",
    "AlphaTauri": "#2B4562",
    "RB": "#6692FF",
    "Aston Martin": "#006F62",
    "Williams": "#005AFF",
    "Alfa Romeo": "#900000",
    "Alfa Romeo Racing": "#900000",
    "Kick Sauber": "#52E252",
    "Sauber": "#52E252",
    "Haas F1 Team": "#B6BABD",
    "Racing Point": "#F596C8",
    "Renault": "#FFF500",
    "Toro Rosso": "#469BFF",
}

# ---------------------------------------------------------------------------
# Caches
# ---------------------------------------------------------------------------
_session_cache = {}           # (year, gp, session_type) → session data dict
_schedule_cache = {}          # year → schedule list
_loading_lock = threading.Lock()
_loading_sessions = {}        # (year, gp) → {"status": "loading"/"ready"/"error", "error": ""}


def _build_session_data(session):
    """Process a loaded FastF1 session into our cached format."""
    laps = get_sector_data(session)
    raw_colors = get_team_colors(session)

    driver_team = {}
    for _, row in laps.iterrows():
        if row["Driver"] not in driver_team:
            driver_team[row["Driver"]] = row["Team"]

    colors = {}
    for drv, team in driver_team.items():
        c = raw_colors.get(drv, "#FFFFFF")
        if c in ("#FFFFFF", "#FFF", "#ffffff"):
            c = TEAM_COLORS_FALLBACK.get(team, "#FFFFFF")
        colors[drv] = c

    return {
        "session": session,
        "laps": laps,
        "colors": colors,
        "driver_team": driver_team,
    }


def _load_session_background(year, gp, session_type="Q"):
    """Load a session in a background thread so the API stays responsive."""
    key = (year, gp, session_type)
    status_key = (year, gp)

    with _loading_lock:
        if key in _session_cache:
            return  # already loaded
        if status_key in _loading_sessions and \
           _loading_sessions[status_key]["status"] == "loading":
            return  # another thread is already loading this
        _loading_sessions[status_key] = {"status": "loading", "error": ""}

    try:
        t0 = _time.time()
        session = load_session(year, gp, session_type)
        data = _build_session_data(session)
        _session_cache[key] = data
        elapsed = _time.time() - t0
        print(f"  ✅ Loaded {year} {gp} in {elapsed:.1f}s")
        with _loading_lock:
            _loading_sessions[status_key] = {"status": "ready", "error": ""}
    except Exception as e:
        print(f"  ❌ Failed to load {year} {gp}: {e}")
        with _loading_lock:
            _loading_sessions[status_key] = {"status": "error", "error": str(e)}


def _get_session_data(year=2021, gp="Abu Dhabi", session_type="Q"):
    """Get cached session data, loading synchronously if needed."""
    key = (year, gp, session_type)
    if key not in _session_cache:
        _load_session_background(year, gp, session_type)
    return _session_cache.get(key)


def _get_color_pair(data, d1, d2):
    c1 = data["colors"].get(d1, "#1E41FF")
    c2 = data["colors"].get(d2, "#00D2BE")
    if c1 == c2:
        c1, c2 = "#1E41FF", "#E10600"
    return c1, c2


def _parse_session_params():
    year = request.args.get("year", 2021, type=int)
    gp = request.args.get("gp", "Abu Dhabi", type=str)
    return year, gp


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.route("/api/schedule", methods=["GET"])
def api_schedule():
    """Get the race calendar for a given year (cached)."""
    year = request.args.get("year", 2024, type=int)

    if year not in _schedule_cache:
        try:
            schedule = fastf1.get_event_schedule(year)
        except Exception as e:
            return jsonify({"error": str(e)}), 400

        races = []
        for _, row in schedule.iterrows():
            rn = int(row["RoundNumber"])
            if rn == 0:
                continue
            races.append({
                "round": rn,
                "name": row["EventName"],
                "country": row["Country"],
                "location": row.get("Location", ""),
            })
        _schedule_cache[year] = races

    return jsonify({"year": year, "races": _schedule_cache[year]})


@app.route("/api/load-session", methods=["POST"])
def api_load_session():
    """Start loading a session in the background. Returns immediately."""
    year = request.json.get("year", 2021)
    gp = request.json.get("gp", "Abu Dhabi")

    key = (year, gp, "Q")
    if key in _session_cache:
        return jsonify({"status": "ready"})

    # Start background loading
    t = threading.Thread(target=_load_session_background, args=(year, gp, "Q"), daemon=True)
    t.start()

    return jsonify({"status": "loading"})


@app.route("/api/session-status", methods=["GET"])
def api_session_status():
    """Check if a session has finished loading."""
    year = request.args.get("year", 2021, type=int)
    gp = request.args.get("gp", "Abu Dhabi", type=str)

    key = (year, gp, "Q")
    if key in _session_cache:
        return jsonify({"status": "ready"})

    status_key = (year, gp)
    info = _loading_sessions.get(status_key, {"status": "idle", "error": ""})
    return jsonify(info)


@app.route("/api/drivers", methods=["GET"])
def api_drivers():
    """List available drivers with lap counts and numbers."""
    year, gp = _parse_session_params()
    data = _get_session_data(year, gp)
    if data is None:
        return jsonify({"error": "Session still loading, please wait"}), 202

    drivers_df = list_available_drivers(data["laps"])

    drivers = []
    for _, row in drivers_df.iterrows():
        color = data["colors"].get(row["Driver"], "#FFFFFF")
        drivers.append({
            "driver": row["Driver"],
            "team": row["Team"],
            "totalLaps": int(row["TotalLaps"]),
            "bestLap": round(float(row["BestLap"]), 3),
            "lapNumbers": row["LapNumbers"],
            "color": color,
        })

    return jsonify({"drivers": drivers})


@app.route("/api/compare", methods=["GET"])
def api_compare():
    """Compare two drivers sector-by-sector."""
    year, gp = _parse_session_params()
    d1 = request.args.get("d1", "").upper()
    d2 = request.args.get("d2", "").upper()
    lap1 = request.args.get("lap1", type=int)
    lap2 = request.args.get("lap2", type=int)

    if not d1 or not d2:
        return jsonify({"error": "Provide both d1 and d2 query parameters"}), 400

    data = _get_session_data(year, gp)
    if data is None:
        return jsonify({"error": "Session not loaded"}), 400

    try:
        comp = compare_two_drivers(data["laps"], d1, d2, lap1, lap2)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    c1, c2 = _get_color_pair(data, d1, d2)
    comp["color1"] = c1
    comp["color2"] = c2

    return jsonify(comp)


@app.route("/api/track-dominance", methods=["GET"])
def api_track_dominance():
    """Get track dominance data for two drivers."""
    year, gp = _parse_session_params()
    d1 = request.args.get("d1", "").upper()
    d2 = request.args.get("d2", "").upper()
    lap1 = request.args.get("lap1", type=int)
    lap2 = request.args.get("lap2", type=int)

    if not d1 or not d2:
        return jsonify({"error": "Provide both d1 and d2 query parameters"}), 400

    data = _get_session_data(year, gp)
    if data is None:
        return jsonify({"error": "Session not loaded"}), 400

    try:
        dom = get_track_dominance_data(
            data["session"], d1, d2, lap1, lap2, num_mini_sectors=200
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    c1, c2 = _get_color_pair(data, d1, d2)

    # Get official circuit corner data
    corners = []
    try:
        ci = data["session"].get_circuit_info()
        for _, row in ci.corners.iterrows():
            corners.append({
                "x": float(row["X"]),
                "y": float(row["Y"]),
                "number": int(row["Number"]),
                "letter": str(row.get("Letter", "")),
                "angle": float(row["Angle"]),
            })
    except Exception:
        pass  # some older sessions may lack circuit info

    return jsonify({
        "x": dom["x"].tolist(),
        "y": dom["y"].tolist(),
        "dominance": dom["dominance"].tolist(),
        "speed1": dom["speed1"].tolist(),
        "speed2": dom["speed2"].tolist(),
        "driver1": dom["driver1"],
        "driver2": dom["driver2"],
        "team1": dom["team1"],
        "team2": dom["team2"],
        "lap1_num": dom["lap1_num"],
        "lap2_num": dom["lap2_num"],
        "color1": c1,
        "color2": c2,
        "d1_pct": int((dom["dominance"] == 1).sum() / len(dom["dominance"]) * 100),
        "d2_pct": int((dom["dominance"] == -1).sum() / len(dom["dominance"]) * 100),
        "corners": corners,
    })


# ── Catch-all: serve React index.html for client-side routes ────────
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    # Serve static file if it exists, otherwise serve index.html
    full = os.path.join(app.static_folder, path)
    if path and os.path.isfile(full):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    print("\n🏁  F1 Sector Analysis API")
    print("   Sessions load in background — API stays responsive")
    print(f"   API running at http://localhost:{port}\n")
    app.run(debug=debug, port=port)
