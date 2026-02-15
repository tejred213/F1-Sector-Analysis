"""
F1 Sector Analysis — Data Loading & Processing Module

Loads FastF1 session data and computes sector-level performance
metrics for all drivers.
"""

import fastf1
import pandas as pd
import numpy as np
from pathlib import Path


# ---------------------------------------------------------------------------
# Session loading
# ---------------------------------------------------------------------------

CACHE_DIR = Path(__file__).resolve().parent / "cache"


def load_session(year: int = 2021,
                 gp: str = "Abu Dhabi",
                 session_type: str = "Q") -> fastf1.core.Session:
    """Load a FastF1 session, using the local cache directory."""
    fastf1.Cache.enable_cache(str(CACHE_DIR))
    session = fastf1.get_session(year, gp, session_type)
    session.load()
    return session


# ---------------------------------------------------------------------------
# Data extraction helpers
# ---------------------------------------------------------------------------

def get_sector_data(session: fastf1.core.Session) -> pd.DataFrame:
    """
    Return a cleaned DataFrame of sector times for every driver.

    Filters to accurate laps only and converts timedeltas to seconds.
    """
    laps = session.laps.copy()

    # Keep only accurate laps (timing integrity OK)
    laps = laps[laps["IsAccurate"] == True].reset_index(drop=True)

    # Convert timedelta columns to float seconds
    for col in ("Sector1Time", "Sector2Time", "Sector3Time", "LapTime"):
        laps[f"{col}_sec"] = laps[col].dt.total_seconds()

    return laps


def get_best_sector_times(laps: pd.DataFrame) -> pd.DataFrame:
    """
    Best (minimum) sector time per driver for each sector.

    Returns a DataFrame indexed by Driver with columns:
      Sector1Time_sec, Sector2Time_sec, Sector3Time_sec, Team
    """
    sector_cols = ["Sector1Time_sec", "Sector2Time_sec", "Sector3Time_sec"]

    best = (
        laps
        .groupby("Driver")[sector_cols]
        .min()
        .reset_index()
    )

    # Attach team info
    team_map = laps.drop_duplicates("Driver").set_index("Driver")["Team"]
    best["Team"] = best["Driver"].map(team_map)

    # Sort by total best time
    best["TotalBest"] = best[sector_cols].sum(axis=1)
    best = best.sort_values("TotalBest").reset_index(drop=True)

    return best


def get_average_sector_times(laps: pd.DataFrame) -> pd.DataFrame:
    """
    Average sector time per driver for each sector (accurate laps only).
    """
    sector_cols = ["Sector1Time_sec", "Sector2Time_sec", "Sector3Time_sec"]

    avg = (
        laps
        .groupby("Driver")[sector_cols]
        .mean()
        .reset_index()
    )

    team_map = laps.drop_duplicates("Driver").set_index("Driver")["Team"]
    avg["Team"] = avg["Driver"].map(team_map)

    avg["TotalAvg"] = avg[sector_cols].sum(axis=1)
    avg = avg.sort_values("TotalAvg").reset_index(drop=True)

    return avg


def get_sector_speed_data(laps: pd.DataFrame) -> pd.DataFrame:
    """
    Average speed-trap readings per driver across accurate laps.

    Speed columns: SpeedI1, SpeedI2, SpeedFL (finish-line), SpeedST (speed-trap).
    """
    speed_cols = ["SpeedI1", "SpeedI2", "SpeedFL", "SpeedST"]

    speeds = (
        laps
        .groupby("Driver")[speed_cols]
        .mean()
        .reset_index()
    )

    team_map = laps.drop_duplicates("Driver").set_index("Driver")["Team"]
    speeds["Team"] = speeds["Driver"].map(team_map)

    # Sort by average of all speed traps (descending — fastest first)
    speeds["AvgSpeed"] = speeds[speed_cols].mean(axis=1)
    speeds = speeds.sort_values("AvgSpeed", ascending=False).reset_index(drop=True)

    return speeds


def get_team_colors(session: fastf1.core.Session) -> dict:
    """
    Return a mapping  {DriverAbbreviation: '#hexcolor'}  using
    official FastF1 team colours.
    """
    color_map = {}
    for _, lap in session.laps.iterrows():
        drv = lap["Driver"]
        if drv not in color_map:
            try:
                color_map[drv] = fastf1.plotting.get_team_color(
                    lap["Team"], session=session
                )
            except Exception:
                color_map[drv] = "#FFFFFF"
    return color_map


def get_driver_team_map(laps: pd.DataFrame) -> dict:
    """Return a simple {Driver: Team} mapping."""
    return (
        laps.drop_duplicates("Driver")
        .set_index("Driver")["Team"]
        .to_dict()
    )


# ---------------------------------------------------------------------------
# Head-to-head driver comparison
# ---------------------------------------------------------------------------

def list_available_drivers(laps: pd.DataFrame) -> pd.DataFrame:
    """
    Return a summary of available drivers and how many accurate laps
    each completed, useful for the user to pick drivers and lap numbers.
    """
    summary = (
        laps.groupby(["Driver", "Team"])
        .agg(
            TotalLaps=("LapNumber", "count"),
            BestLap=("LapTime_sec", "min"),
            LapNumbers=("LapNumber", lambda x: sorted(x.astype(int).tolist())),
        )
        .reset_index()
        .sort_values("BestLap")
        .reset_index(drop=True)
    )
    return summary


def get_driver_lap(laps: pd.DataFrame, driver: str,
                   lap_number: int | None = None) -> pd.Series:
    """
    Get a specific lap for a driver.

    If *lap_number* is None, the driver's personal-best lap is returned.
    """
    drv_laps = laps[laps["Driver"] == driver.upper()]
    if drv_laps.empty:
        raise ValueError(f"Driver '{driver}' not found in session data.")

    if lap_number is not None:
        lap = drv_laps[drv_laps["LapNumber"] == lap_number]
        if lap.empty:
            available = sorted(drv_laps["LapNumber"].astype(int).tolist())
            raise ValueError(
                f"Lap {lap_number} not found for {driver}. "
                f"Available accurate laps: {available}"
            )
        return lap.iloc[0]

    # Default: personal-best lap
    best_idx = drv_laps["LapTime_sec"].idxmin()
    return drv_laps.loc[best_idx]


def compare_two_drivers(laps: pd.DataFrame,
                        driver1: str, driver2: str,
                        lap1: int | None = None,
                        lap2: int | None = None) -> dict:
    """
    Compare two drivers sector-by-sector.

    Parameters
    ----------
    laps : cleaned laps DataFrame (from get_sector_data)
    driver1, driver2 : driver abbreviations (e.g. "VER", "HAM")
    lap1, lap2 : optional specific lap numbers; None = personal best

    Returns
    -------
    dict with keys:
        driver1, driver2          – abbreviation strings
        team1, team2              – team names
        lap1_num, lap2_num        – lap numbers used
        sectors                   – list of dicts per sector:
            {sector, time1, time2, delta, faster}
        speed_traps               – list of dicts per speed point:
            {trap, speed1, speed2, delta, faster}
        overall_time1, overall_time2, overall_delta, overall_faster
    """
    d1 = driver1.upper()
    d2 = driver2.upper()

    row1 = get_driver_lap(laps, d1, lap1)
    row2 = get_driver_lap(laps, d2, lap2)

    sector_cols = ["Sector1Time_sec", "Sector2Time_sec", "Sector3Time_sec"]
    speed_cols  = ["SpeedI1", "SpeedI2", "SpeedFL", "SpeedST"]
    speed_names = ["Intermediate 1", "Intermediate 2", "Finish Line", "Speed Trap"]

    sectors = []
    for i, col in enumerate(sector_cols):
        t1, t2 = row1[col], row2[col]
        delta = t1 - t2
        sectors.append({
            "sector": f"Sector {i+1}",
            "time1": t1,
            "time2": t2,
            "delta": delta,
            "faster": d1 if delta < 0 else (d2 if delta > 0 else "TIE"),
        })

    speed_traps = []
    for col, name in zip(speed_cols, speed_names):
        s1, s2 = row1[col], row2[col]
        delta = s1 - s2  # positive = driver1 faster (higher speed)
        speed_traps.append({
            "trap": name,
            "speed1": s1,
            "speed2": s2,
            "delta": delta,
            "faster": d1 if delta > 0 else (d2 if delta < 0 else "TIE"),
        })

    ot1 = row1["LapTime_sec"]
    ot2 = row2["LapTime_sec"]

    return {
        "driver1": d1,
        "driver2": d2,
        "team1": row1["Team"],
        "team2": row2["Team"],
        "lap1_num": int(row1["LapNumber"]),
        "lap2_num": int(row2["LapNumber"]),
        "sectors": sectors,
        "speed_traps": speed_traps,
        "overall_time1": ot1,
        "overall_time2": ot2,
        "overall_delta": ot1 - ot2,
        "overall_faster": d1 if ot1 < ot2 else (d2 if ot2 < ot1 else "TIE"),
    }


# ---------------------------------------------------------------------------
# Track Dominance data
# ---------------------------------------------------------------------------

def get_track_dominance_data(session, driver1: str, driver2: str,
                             lap1: int | None = None,
                             lap2: int | None = None,
                             num_mini_sectors: int = 200) -> dict:
    """
    Build data for a Track Dominance map.

    For each mini-sector (uniform distance slices around the lap),
    determine which driver carries higher speed.

    Returns
    -------
    dict with keys:
        x, y            – arrays of track coordinates (num_mini_sectors,)
        dominance       – array of +1 (driver1 faster) / -1 (driver2 faster)
        speed1, speed2  – interpolated speed arrays
        driver1, driver2, team1, team2
    """
    d1, d2 = driver1.upper(), driver2.upper()

    laps_all = session.laps

    # ── Pick the specific laps ──────────────────────────────────────────
    def _pick_lap(driver, lap_number):
        drv_laps = laps_all.pick_drivers(driver)
        if lap_number is not None:
            lap = drv_laps[drv_laps["LapNumber"] == lap_number]
            if lap.empty:
                raise ValueError(f"Lap {lap_number} not found for {driver}")
            return lap.iloc[0]
        return drv_laps.pick_fastest()

    lap_row1 = _pick_lap(d1, lap1)
    lap_row2 = _pick_lap(d2, lap2)

    tel1 = lap_row1.get_telemetry().add_distance()
    tel2 = lap_row2.get_telemetry().add_distance()

    # ── Resample both to the same uniform distance grid ─────────────────
    total_dist = min(tel1["Distance"].max(), tel2["Distance"].max())
    ref_dist = np.linspace(0, total_dist, num_mini_sectors)

    x1 = np.interp(ref_dist, tel1["Distance"], tel1["X"])
    y1 = np.interp(ref_dist, tel1["Distance"], tel1["Y"])
    s1 = np.interp(ref_dist, tel1["Distance"], tel1["Speed"])

    x2 = np.interp(ref_dist, tel2["Distance"], tel2["X"])
    y2 = np.interp(ref_dist, tel2["Distance"], tel2["Y"])
    s2 = np.interp(ref_dist, tel2["Distance"], tel2["Speed"])

    # Average X/Y for the track centre-line
    x = (x1 + x2) / 2
    y = (y1 + y2) / 2

    # +1 = driver1 faster (higher speed), -1 = driver2 faster
    dominance = np.where(s1 > s2, 1, np.where(s2 > s1, -1, 0))

    return {
        "x": x,
        "y": y,
        "speed1": s1,
        "speed2": s2,
        "dominance": dominance,
        "driver1": d1,
        "driver2": d2,
        "team1": lap_row1["Team"],
        "team2": lap_row2["Team"],
        "lap1_num": int(lap_row1["LapNumber"]),
        "lap2_num": int(lap_row2["LapNumber"]),
    }
