#!/usr/bin/env python3
"""
F1 Sector Analysis — Entry Point

Usage:
    python main.py                                          # full analysis (default)
    python main.py compare --d1 VER --d2 HAM                # compare best laps
    python main.py compare --d1 VER --d2 HAM --lap1 5 --lap2 7  # specific laps
    python main.py compare --list-drivers                   # show available drivers
"""

import argparse
import sys
import pandas as pd

from sector_analysis import (
    load_session,
    get_sector_data,
    get_best_sector_times,
    get_average_sector_times,
    get_sector_speed_data,
    get_team_colors,
    list_available_drivers,
    compare_two_drivers,
    get_track_dominance_data,
)
from graph_generator import (
    generate_all_charts,
    plot_driver_comparison,
    plot_track_dominance,
)


# ---------------------------------------------------------------------------
# Pretty-print helpers
# ---------------------------------------------------------------------------

def _print_ranking_table(title: str, df: pd.DataFrame,
                         sector_cols: list[str], total_col: str):
    """Print a nicely formatted console ranking table."""
    print(f"\n{'─' * 72}")
    print(f"  {title}")
    print(f"{'─' * 72}")
    header = f"{'Pos':>4}  {'Driver':<6}  {'Team':<22}"
    for sc in sector_cols:
        label = sc.replace("Time_sec", "").replace("Sector", "S")
        header += f"  {label:>8}"
    header += f"  {'Total':>8}"
    print(header)
    print(f"{'─' * 72}")

    for pos, (_, row) in enumerate(df.iterrows(), start=1):
        line = f"{pos:>4}  {row['Driver']:<6}  {row['Team']:<22}"
        for sc in sector_cols:
            line += f"  {row[sc]:>8.3f}"
        line += f"  {row[total_col]:>8.3f}"
        print(line)

    print(f"{'─' * 72}\n")


def _print_comparison(comp: dict):
    """Print a rich console comparison between two drivers."""
    d1, d2 = comp["driver1"], comp["driver2"]
    t1, t2 = comp["team1"], comp["team2"]

    print(f"\n{'═' * 72}")
    print(f"  ⚔️   {d1} ({t1})  vs  {d2} ({t2})")
    print(f"  Lap {comp['lap1_num']}  vs  Lap {comp['lap2_num']}")
    print(f"{'═' * 72}")

    # Sector comparison
    print(f"\n  {'Sector':<10}  {d1:>10}  {d2:>10}  {'Delta':>10}  {'Faster':>8}")
    print(f"  {'─' * 54}")
    for s in comp["sectors"]:
        delta_str = f"{abs(s['delta']):.3f}s"
        marker = "◀" if s["faster"] == d1 else ("▶" if s["faster"] == d2 else "=")
        print(f"  {s['sector']:<10}  {s['time1']:>9.3f}s  {s['time2']:>9.3f}s  "
              f"{marker} {delta_str:>8}  {s['faster']:>8}")

    # Speed traps
    print(f"\n  {'Trap':<16}  {d1:>8}  {d2:>8}  {'Delta':>8}  {'Faster':>8}")
    print(f"  {'─' * 54}")
    for t in comp["speed_traps"]:
        delta_str = f"+{abs(t['delta']):.0f}"
        print(f"  {t['trap']:<16}  {t['speed1']:>7.0f}   {t['speed2']:>7.0f}   "
              f"{delta_str:>7}   {t['faster']:>7}")

    # Overall
    ow = comp["overall_faster"]
    od = abs(comp["overall_delta"])
    sw1 = sum(1 for s in comp["sectors"] if s["faster"] == d1)
    sw2 = sum(1 for s in comp["sectors"] if s["faster"] == d2)

    print(f"\n{'═' * 72}")
    verdict = f"🏆  {ow} FASTER BY {od:.3f}s" if ow != "TIE" else "🏆  DEAD HEAT"
    print(f"  {verdict}")
    print(f"  {d1}: {comp['overall_time1']:.3f}s   |   {d2}: {comp['overall_time2']:.3f}s")
    print(f"  Sectors won:  {d1} {sw1}  –  {sw2} {d2}")
    print(f"{'═' * 72}\n")


# ---------------------------------------------------------------------------
# Sub-commands
# ---------------------------------------------------------------------------

def cmd_full_analysis(args, session, laps, colors):
    """Run the full field analysis (original behaviour)."""
    best_df   = get_best_sector_times(laps)
    avg_df    = get_average_sector_times(laps)
    speeds_df = get_sector_speed_data(laps)

    sector_cols = ["Sector1Time_sec", "Sector2Time_sec", "Sector3Time_sec"]

    _print_ranking_table("Best Sector Times", best_df, sector_cols, "TotalBest")
    _print_ranking_table("Average Sector Times", avg_df, sector_cols, "TotalAvg")

    # Speed trap summary
    print(f"{'─' * 72}")
    print("  Speed Trap Averages (km/h)")
    print(f"{'─' * 72}")
    print(f"{'Pos':>4}  {'Driver':<6}  {'Team':<22}"
          f"  {'I1':>6}  {'I2':>6}  {'FL':>6}  {'ST':>6}  {'Avg':>6}")
    print(f"{'─' * 72}")
    for pos, (_, row) in enumerate(speeds_df.iterrows(), start=1):
        print(f"{pos:>4}  {row['Driver']:<6}  {row['Team']:<22}"
              f"  {row['SpeedI1']:>6.1f}  {row['SpeedI2']:>6.1f}"
              f"  {row['SpeedFL']:>6.1f}  {row['SpeedST']:>6.1f}"
              f"  {row['AvgSpeed']:>6.1f}")
    print(f"{'─' * 72}\n")

    generate_all_charts(laps, best_df, avg_df, speeds_df, colors)


def cmd_compare(args, session, laps, colors):
    """Head-to-head comparison of two drivers."""
    # --list-drivers mode
    if args.list_drivers:
        drivers_df = list_available_drivers(laps)
        print(f"\n{'─' * 72}")
        print("  Available Drivers (sorted by best lap)")
        print(f"{'─' * 72}")
        print(f"  {'#':>3}  {'Driver':<6}  {'Team':<24}  {'Laps':>5}  "
              f"{'Best':>8}  {'Lap Numbers'}")
        print(f"{'─' * 72}")
        for i, (_, row) in enumerate(drivers_df.iterrows(), start=1):
            lap_nums = ", ".join(str(n) for n in row["LapNumbers"])
            print(f"  {i:>3}  {row['Driver']:<6}  {row['Team']:<24}  "
                  f"{row['TotalLaps']:>5}  {row['BestLap']:>7.3f}s  [{lap_nums}]")
        print(f"{'─' * 72}\n")
        return

    # Validate driver arguments
    if not args.d1 or not args.d2:
        print("❌  Please provide two drivers with --d1 and --d2")
        print("    Example:  python main.py compare --d1 VER --d2 HAM")
        print("    Use --list-drivers to see available options.")
        sys.exit(1)

    lap1 = args.lap1 if args.lap1 else None
    lap2 = args.lap2 if args.lap2 else None

    mode_str = "best laps" if (lap1 is None and lap2 is None) else "specific laps"
    print(f"\n⚔️   Comparing {args.d1.upper()} vs {args.d2.upper()} ({mode_str})")

    try:
        comp = compare_two_drivers(laps, args.d1, args.d2, lap1, lap2)
    except ValueError as e:
        print(f"\n❌  {e}")
        sys.exit(1)

    _print_comparison(comp)

    print("Generating comparison chart + track dominance map ...\n")
    plot_driver_comparison(comp, colors)

    # Track dominance map
    try:
        dom_data = get_track_dominance_data(
            session, args.d1, args.d2, lap1, lap2
        )
        plot_track_dominance(dom_data, colors)
    except Exception as e:
        print(f"  Warning: Could not generate track dominance map: {e}")

    print("Done!\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="F1 Sector-Wise Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                                          # full analysis
  python main.py compare --list-drivers                   # see drivers & laps
  python main.py compare --d1 VER --d2 HAM                # compare best laps
  python main.py compare --d1 VER --d2 HAM --lap1 5 --lap2 7
        """,
    )
    parser.add_argument("--year", type=int, default=2021, help="Season year")
    parser.add_argument("--gp", type=str, default="Abu Dhabi",
                        help="Grand Prix name")
    parser.add_argument("--session", type=str, default="Q",
                        help="Session type (FP1, FP2, FP3, Q, R)")

    subparsers = parser.add_subparsers(dest="command")

    # ── compare sub-command ──
    cmp_parser = subparsers.add_parser("compare",
                                       help="Compare two drivers head-to-head")
    cmp_parser.add_argument("--d1", type=str, help="Driver 1 abbreviation (e.g. VER)")
    cmp_parser.add_argument("--d2", type=str, help="Driver 2 abbreviation (e.g. HAM)")
    cmp_parser.add_argument("--lap1", type=int, default=None,
                            help="Specific lap number for driver 1 (default: best lap)")
    cmp_parser.add_argument("--lap2", type=int, default=None,
                            help="Specific lap number for driver 2 (default: best lap)")
    cmp_parser.add_argument("--list-drivers", action="store_true",
                            help="List all available drivers and their lap numbers")

    args = parser.parse_args()

    # ── Load session ──────────────────────────────────────────────────────
    print(f"\n🏁  F1 Sector Analysis  •  {args.year} {args.gp} GP — {args.session}")
    print("=" * 60)

    session = load_session(args.year, args.gp, args.session)
    laps = get_sector_data(session)
    colors = get_team_colors(session)

    print(f"\n📊  Loaded {len(laps)} accurate laps from "
          f"{laps['Driver'].nunique()} drivers\n")

    # ── Dispatch ──────────────────────────────────────────────────────────
    if args.command == "compare":
        cmd_compare(args, session, laps, colors)
    else:
        cmd_full_analysis(args, session, laps, colors)


if __name__ == "__main__":
    main()
