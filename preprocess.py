#!/usr/bin/env python3
"""
F1 Sector Analysis — Pre-Processing Script

Downloads and pre-computes all F1 qualifying data into static JSON files.
Run this locally once; the web app then serves instant responses.

Usage:
    python preprocess.py                          # All seasons (2018-2025)
    python preprocess.py --year 2024              # Single season
    python preprocess.py --year 2024 --gp Bahrain # Single session
"""

import argparse
import json
import sys
import traceback
from pathlib import Path

import fastf1
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CACHE_DIR = Path(__file__).resolve().parent / "cache"
DATA_DIR = Path(__file__).resolve().parent / "data"
CACHE_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

fastf1.Cache.enable_cache(str(CACHE_DIR))

# FastF1 has good qualifying telemetry from 2018 onward
ALL_YEARS = list(range(2018, 2026))

# Team colour fallbacks (FastF1 sometimes returns white)
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

NUM_MINI_SECTORS = 200  # resample telemetry to this many points


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def safe_float(v):
    """Convert value to float, return None for NaN/NaT."""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    try:
        return round(float(v), 3)
    except (TypeError, ValueError):
        return None


def safe_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def sanitize_gp_name(name: str) -> str:
    """Normalize GP name for filesystem: spaces → underscores, safe chars only."""
    return name.replace(" ", "_").replace("'", "").replace(".", "")


# ---------------------------------------------------------------------------
# Processing functions
# ---------------------------------------------------------------------------

def process_schedule(years: list[int]):
    """Generate data/schedule.json with all races for all years."""
    print("\n📅 Processing schedules...")
    
    # Load existing schedule if it exists, to support incremental updates
    out = DATA_DIR / "schedule.json"
    if out.exists():
        try:
            schedule = json.loads(out.read_text())
        except Exception:
            schedule = {}
    else:
        schedule = {}

    for year in years:
        try:
            sched = fastf1.get_event_schedule(year)
            races = []
            for _, row in sched.iterrows():
                rn = int(row["RoundNumber"])
                if rn == 0:
                    continue
                races.append({
                    "round": rn,
                    "name": row["EventName"],
                    "country": row["Country"],
                    "location": row.get("Location", ""),
                })
            schedule[str(year)] = races
            print(f"  ✅ {year}: {len(races)} races")
        except Exception as e:
            print(f"  ❌ {year}: {e}")

    out = DATA_DIR / "schedule.json"
    out.write_text(json.dumps(schedule, indent=2))
    print(f"  → Saved {out}")
    return schedule


def process_session(year: int, gp_name: str, gp_dir_name: str):
    """Process a single qualifying session into JSON files."""

    gp_dir = DATA_DIR / str(year) / gp_dir_name
    gp_dir.mkdir(parents=True, exist_ok=True)

    # Skip if already processed
    if (gp_dir / "session.json").exists() and (gp_dir / "laps.json").exists():
        print(f"    ⏭  Already processed, skipping")
        return True

    # ── Load session ───────────────────────────────────────────────────
    try:
        session = fastf1.get_session(year, gp_name, "Q")
        session.load(telemetry=True)
    except Exception as e:
        print(f"    ❌ Failed to load: {e}")
        return False

    laps = session.laps.copy()

    # ── Filter to accurate laps ───────────────────────────────────────
    accurate = laps[laps["IsAccurate"] == True].reset_index(drop=True)

    if accurate.empty:
        print(f"    ⚠️  No accurate laps, skipping")
        return False

    # ── Convert sector times to seconds ───────────────────────────────
    for col in ("Sector1Time", "Sector2Time", "Sector3Time", "LapTime"):
        accurate[f"{col}_sec"] = accurate[col].dt.total_seconds()

    # ── Driver info + colors ──────────────────────────────────────────
    drivers = []
    color_map = {}

    for drv in accurate["Driver"].unique():
        drv_laps = accurate[accurate["Driver"] == drv]
        team = drv_laps.iloc[0]["Team"]

        # Get team color
        try:
            color = fastf1.plotting.get_team_color(team, session=session)
        except Exception:
            color = "#FFFFFF"
        if color in ("#FFFFFF", "#FFF", "#ffffff"):
            color = TEAM_COLORS_FALLBACK.get(team, "#FFFFFF")
        color_map[drv] = color

        # Available laps for this driver
        lap_numbers = sorted(drv_laps["LapNumber"].astype(int).tolist())
        best_lap_time = drv_laps["LapTime_sec"].min()
        best_lap_num = int(drv_laps.loc[drv_laps["LapTime_sec"].idxmin(), "LapNumber"])

        drivers.append({
            "driver": drv,
            "team": team,
            "color": color,
            "totalLaps": len(drv_laps),
            "bestLap": safe_float(best_lap_time),
            "bestLapNum": best_lap_num,
            "lapNumbers": lap_numbers,
        })

    # Sort by best lap time
    drivers.sort(key=lambda d: d["bestLap"] or 999)

    # ── Save session.json ─────────────────────────────────────────────
    session_data = {
        "year": year,
        "gp": gp_name,
        "drivers": drivers,
    }
    (gp_dir / "session.json").write_text(json.dumps(session_data, indent=2))

    # ── Save laps.json (all accurate laps) ────────────────────────────
    laps_list = []
    for _, row in accurate.iterrows():
        laps_list.append({
            "driver": row["Driver"],
            "team": row["Team"],
            "lapNumber": safe_int(row["LapNumber"]),
            "lapTime": safe_float(row["LapTime_sec"]),
            "sector1": safe_float(row["Sector1Time_sec"]),
            "sector2": safe_float(row["Sector2Time_sec"]),
            "sector3": safe_float(row["Sector3Time_sec"]),
            "speedI1": safe_float(row.get("SpeedI1")),
            "speedI2": safe_float(row.get("SpeedI2")),
            "speedFL": safe_float(row.get("SpeedFL")),
            "speedST": safe_float(row.get("SpeedST")),
        })
    (gp_dir / "laps.json").write_text(json.dumps(laps_list, indent=2))

    # ── Save corners.json ─────────────────────────────────────────────
    corners = []
    try:
        ci = session.get_circuit_info()
        for _, row in ci.corners.iterrows():
            corners.append({
                "x": float(row["X"]),
                "y": float(row["Y"]),
                "number": int(row["Number"]),
                "letter": str(row.get("Letter", "")),
                "angle": float(row["Angle"]),
            })
    except Exception:
        pass  # older sessions may lack circuit info
    (gp_dir / "corners.json").write_text(json.dumps(corners, indent=2))

    # ── Save telemetry for each driver's best lap ─────────────────────
    # IMPORTANT: Use session.laps (not the copy) to preserve telemetry access
    tel_dir = gp_dir / "telemetry"
    tel_dir.mkdir(exist_ok=True)

    for drv_info in drivers:
        drv = drv_info["driver"]
        best_num = drv_info["bestLapNum"]
        filename = f"{drv}_{best_num}.json"

        if (tel_dir / filename).exists():
            continue

        try:
            drv_laps_raw = session.laps.pick_drivers(drv)
            lap_row = drv_laps_raw[drv_laps_raw["LapNumber"] == best_num].iloc[0]
            tel = lap_row.get_telemetry().add_distance()

            if tel.empty or tel["Distance"].max() < 100:
                continue

            # Resample to uniform distance grid
            total_dist = tel["Distance"].max()
            ref_dist = np.linspace(0, total_dist, NUM_MINI_SECTORS)

            tel_data = {
                "driver": drv,
                "lapNumber": best_num,
                "distance": [round(float(d), 1) for d in ref_dist],
                "x": [round(float(v), 1) for v in np.interp(ref_dist, tel["Distance"], tel["X"])],
                "y": [round(float(v), 1) for v in np.interp(ref_dist, tel["Distance"], tel["Y"])],
                "speed": [round(float(v), 1) for v in np.interp(ref_dist, tel["Distance"], tel["Speed"])],
            }
            (tel_dir / filename).write_text(json.dumps(tel_data))
        except Exception as e:
            print(f"      ⚠️  Telemetry failed for {drv} lap {best_num}: {e}")

    n_tel = len(list(tel_dir.glob("*.json")))
    print(f"    ✅ {len(drivers)} drivers, {len(laps_list)} laps, {n_tel} telemetry files, {len(corners)} corners")
    return True


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Pre-process F1 qualifying data")
    parser.add_argument("--year", type=int, help="Process a single year")
    parser.add_argument("--gp", type=str, help="Process a single GP (requires --year)")
    args = parser.parse_args()

    if args.gp and not args.year:
        parser.error("--gp requires --year")

    years = [args.year] if args.year else ALL_YEARS

    # ── Step 1: Schedules ─────────────────────────────────────────────
    schedule = process_schedule(years)

    # ── Step 2: Sessions ──────────────────────────────────────────────
    total, success, failed = 0, 0, 0

    for year in years:
        year_str = str(year)
        if year_str not in schedule:
            continue

        races = schedule[year_str]
        print(f"\n🏎️  Processing {year} ({len(races)} races)...")

        for race in races:
            gp_name = race["name"]
            gp_dir_name = sanitize_gp_name(gp_name)

            # If --gp flag, only process that specific GP
            if args.gp and args.gp.lower() not in gp_name.lower():
                continue

            total += 1
            print(f"\n  📍 R{race['round']}: {gp_name}")

            try:
                ok = process_session(year, gp_name, gp_dir_name)
                if ok:
                    success += 1
                else:
                    failed += 1
            except Exception as e:
                failed += 1
                print(f"    ❌ Unexpected error: {e}")
                traceback.print_exc()

    print(f"\n{'='*60}")
    print(f"✅ Done! {success}/{total} sessions processed ({failed} failed)")
    print(f"   Data saved to: {DATA_DIR}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
