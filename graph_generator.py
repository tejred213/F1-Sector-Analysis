"""
F1 Sector Analysis — Visualization Module

Generates rich matplotlib / seaborn charts for sector-wise driver
performance analysis with an F1-inspired dark theme.
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap
import seaborn as sns
import numpy as np
import pandas as pd
from pathlib import Path
from matplotlib.patches import FancyBboxPatch
from math import pi


# ---------------------------------------------------------------------------
# Output & Theme
# ---------------------------------------------------------------------------

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# F1 dark theme palette
BG_COLOR      = "#1E1E2F"
CARD_COLOR    = "#2A2A3D"
TEXT_COLOR    = "#E0E0E0"
ACCENT_RED    = "#E10600"
GRID_COLOR    = "#3A3A50"
SECTOR_COLORS = ["#00D2BE", "#FF8700", "#E10600"]   # teal, orange, red


def _apply_f1_theme():
    """Set global matplotlib rcParams for the F1 dark theme."""
    plt.rcParams.update({
        "figure.facecolor": BG_COLOR,
        "axes.facecolor":   CARD_COLOR,
        "axes.edgecolor":   GRID_COLOR,
        "axes.labelcolor":  TEXT_COLOR,
        "text.color":       TEXT_COLOR,
        "xtick.color":      TEXT_COLOR,
        "ytick.color":      TEXT_COLOR,
        "grid.color":       GRID_COLOR,
        "grid.alpha":       0.3,
        "legend.facecolor": CARD_COLOR,
        "legend.edgecolor": GRID_COLOR,
        "font.family":      "sans-serif",
        "font.size":        11,
    })


def _save(fig, name: str):
    """Save figure and close."""
    path = OUTPUT_DIR / f"{name}.png"
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  ✓  Saved {path}")


# ---------------------------------------------------------------------------
# 1. Best Sector Times — Grouped Horizontal Bar Chart
# ---------------------------------------------------------------------------

def plot_best_sector_times(best_df: pd.DataFrame, colors: dict):
    """
    Grouped horizontal bars:  drivers (y) × best sector time (x).
    One cluster of three bars per driver, coloured by sector.
    """
    _apply_f1_theme()

    drivers = best_df["Driver"].values
    n = len(drivers)
    bar_h = 0.25
    y_pos = np.arange(n)

    fig, ax = plt.subplots(figsize=(14, max(8, n * 0.55)))

    for i, (sec, color) in enumerate(zip(
        ["Sector1Time_sec", "Sector2Time_sec", "Sector3Time_sec"],
        SECTOR_COLORS,
    )):
        vals = best_df[sec].values
        ax.barh(y_pos + i * bar_h, vals, height=bar_h, label=f"Sector {i+1}",
                color=color, alpha=0.9, edgecolor="none", zorder=3)
        # Value labels
        for j, v in enumerate(vals):
            ax.text(v + 0.15, y_pos[j] + i * bar_h, f"{v:.3f}s",
                    va="center", fontsize=7.5, color=TEXT_COLOR, zorder=4)

    ax.set_yticks(y_pos + bar_h)
    ax.set_yticklabels(drivers, fontsize=10, fontweight="bold")
    ax.invert_yaxis()
    ax.set_xlabel("Time (seconds)", fontsize=12)
    ax.set_title("Best Sector Times — All Drivers", fontsize=16,
                 fontweight="bold", pad=15, color=ACCENT_RED)
    ax.legend(loc="lower right", fontsize=10)
    ax.grid(axis="x", linestyle="--", alpha=0.25, zorder=0)

    _save(fig, "01_best_sector_times")


# ---------------------------------------------------------------------------
# 2. Average Sector Times — Heatmap
# ---------------------------------------------------------------------------

def plot_sector_heatmap(avg_df: pd.DataFrame):
    """
    Heatmap: rows = drivers, cols = S1/S2/S3.
    Colour intensity shows how close each time is to the field-best.
    """
    _apply_f1_theme()

    sector_cols = ["Sector1Time_sec", "Sector2Time_sec", "Sector3Time_sec"]
    matrix = avg_df.set_index("Driver")[sector_cols].copy()
    matrix.columns = ["Sector 1", "Sector 2", "Sector 3"]

    # Compute delta from best per sector for colour mapping
    delta = matrix.copy()
    for col in delta.columns:
        best = delta[col].min()
        delta[col] = delta[col] - best

    fig, ax = plt.subplots(figsize=(8, max(8, len(matrix) * 0.45)))
    sns.heatmap(
        delta,
        annot=matrix.round(3).values,
        fmt="",
        cmap="RdYlGn_r",
        linewidths=0.6,
        linecolor=BG_COLOR,
        cbar_kws={"label": "Δ from best (s)", "shrink": 0.6},
        ax=ax,
    )
    ax.set_title("Average Sector Times — Heatmap (Δ to best)",
                 fontsize=14, fontweight="bold", pad=12, color=ACCENT_RED)
    ax.set_ylabel("")
    ax.tick_params(axis="y", rotation=0)

    _save(fig, "02_sector_heatmap")


# ---------------------------------------------------------------------------
# 3. Sector Time Distribution — Violin Plot
# ---------------------------------------------------------------------------

def plot_sector_violins(laps: pd.DataFrame, colors: dict):
    """
    Three subplots (one per sector), each showing a violin per driver.
    """
    _apply_f1_theme()

    # Sort drivers by total best so order is consistent
    driver_order = (
        laps.groupby("Driver")["LapTime_sec"].min()
        .sort_values()
        .index.tolist()
    )

    fig, axes = plt.subplots(3, 1, figsize=(16, 18), sharex=False)

    for idx, (sec, color) in enumerate(zip(
        ["Sector1Time_sec", "Sector2Time_sec", "Sector3Time_sec"],
        SECTOR_COLORS,
    )):
        ax = axes[idx]
        data = laps.dropna(subset=[sec])
        sns.violinplot(
            data=data, x="Driver", y=sec, order=driver_order,
            color=color, inner="box", linewidth=0.8,
            ax=ax, alpha=0.85, cut=0,
        )
        ax.set_title(f"Sector {idx+1} Time Distribution",
                     fontsize=13, fontweight="bold", color=color)
        ax.set_ylabel("Time (s)", fontsize=11)
        ax.set_xlabel("")
        ax.tick_params(axis="x", rotation=45)
        ax.grid(axis="y", linestyle="--", alpha=0.2)

    fig.suptitle("Sector Time Distributions — All Drivers",
                 fontsize=16, fontweight="bold", y=1.01, color=ACCENT_RED)
    fig.tight_layout()
    _save(fig, "03_sector_violin")


# ---------------------------------------------------------------------------
# 4. Speed Trap Comparison — Grouped Bar Chart
# ---------------------------------------------------------------------------

def plot_speed_traps(speeds_df: pd.DataFrame, colors: dict):
    """
    Grouped vertical bars: drivers (x) × speed (y) at each trap point.
    """
    _apply_f1_theme()

    speed_labels = {
        "SpeedI1": "Intermediate 1",
        "SpeedI2": "Intermediate 2",
        "SpeedFL": "Finish Line",
        "SpeedST": "Speed Trap",
    }
    speed_colors = ["#00D2BE", "#FF8700", "#E10600", "#9B59B6"]
    drivers = speeds_df["Driver"].values
    n = len(drivers)
    x = np.arange(n)
    w = 0.2

    fig, ax = plt.subplots(figsize=(18, 8))

    for i, (col, label) in enumerate(speed_labels.items()):
        vals = speeds_df[col].values
        ax.bar(x + i * w, vals, width=w, label=label,
               color=speed_colors[i], alpha=0.9, edgecolor="none", zorder=3)

    ax.set_xticks(x + 1.5 * w)
    ax.set_xticklabels(drivers, fontsize=10, fontweight="bold", rotation=45,
                       ha="right")
    ax.set_ylabel("Speed (km/h)", fontsize=12)
    ax.set_title("Speed Trap Comparison — All Drivers", fontsize=16,
                 fontweight="bold", pad=15, color=ACCENT_RED)
    ax.legend(loc="upper right", fontsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.2, zorder=0)

    # Start y-axis a bit below the minimum to show differences
    all_speeds = speeds_df[list(speed_labels.keys())].values.flatten()
    ax.set_ylim(np.nanmin(all_speeds) - 15, np.nanmax(all_speeds) + 10)

    _save(fig, "04_speed_traps")


# ---------------------------------------------------------------------------
# 5. Cumulative Lap Breakdown — Stacked Horizontal Bar
# ---------------------------------------------------------------------------

def plot_lap_breakdown(best_df: pd.DataFrame, colors: dict):
    """
    Stacked horizontal bar: each driver's theoretical best lap
    decomposed into S1 + S2 + S3.
    """
    _apply_f1_theme()

    drivers = best_df["Driver"].values
    n = len(drivers)

    s1 = best_df["Sector1Time_sec"].values
    s2 = best_df["Sector2Time_sec"].values
    s3 = best_df["Sector3Time_sec"].values

    fig, ax = plt.subplots(figsize=(14, max(8, n * 0.5)))

    ax.barh(drivers, s1, color=SECTOR_COLORS[0], label="Sector 1",
            edgecolor="none", zorder=3)
    ax.barh(drivers, s2, left=s1, color=SECTOR_COLORS[1], label="Sector 2",
            edgecolor="none", zorder=3)
    ax.barh(drivers, s3, left=s1 + s2, color=SECTOR_COLORS[2], label="Sector 3",
            edgecolor="none", zorder=3)

    # Total time label at the end
    totals = s1 + s2 + s3
    for i, t in enumerate(totals):
        ax.text(t + 0.2, i, f"{t:.3f}s", va="center", fontsize=8,
                color=TEXT_COLOR, fontweight="bold", zorder=4)

    ax.invert_yaxis()
    ax.set_xlabel("Time (seconds)", fontsize=12)
    ax.set_title("Theoretical Best Lap Breakdown (S1 + S2 + S3)",
                 fontsize=16, fontweight="bold", pad=15, color=ACCENT_RED)
    ax.legend(loc="lower right", fontsize=10)
    ax.grid(axis="x", linestyle="--", alpha=0.2, zorder=0)

    _save(fig, "05_lap_breakdown")


# ---------------------------------------------------------------------------
# 6. Sector Dominance — Radar / Spider Chart
# ---------------------------------------------------------------------------

def plot_sector_radar(best_df: pd.DataFrame, colors: dict, top_n: int = 10):
    """
    Radar chart showing normalized sector performance for the top-N drivers.

    Each axis = one sector.  Values are inverted percentile ranks so that
    *faster* = *further from centre*.
    """
    _apply_f1_theme()

    df = best_df.head(top_n).copy()
    sector_cols = ["Sector1Time_sec", "Sector2Time_sec", "Sector3Time_sec"]
    categories = ["Sector 1", "Sector 2", "Sector 3"]
    N = len(categories)

    # Normalise: convert times to a 0-1 score where 1 = best
    norm = df[sector_cols].copy()
    for col in sector_cols:
        col_min = norm[col].min()
        col_max = norm[col].max()
        rng = col_max - col_min
        if rng == 0:
            norm[col] = 1.0
        else:
            norm[col] = 1.0 - (norm[col] - col_min) / rng  # invert: lower time → higher score

    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]  # close the polygon

    fig, ax = plt.subplots(figsize=(9, 9), subplot_kw=dict(polar=True))
    ax.set_facecolor(CARD_COLOR)

    for i, row in norm.iterrows():
        drv = df.loc[i, "Driver"]
        vals = row[sector_cols].tolist()
        vals += vals[:1]
        color = colors.get(drv, "#FFFFFF")
        ax.plot(angles, vals, linewidth=2, label=drv, color=color)
        ax.fill(angles, vals, alpha=0.08, color=color)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=12, fontweight="bold")
    ax.set_yticklabels([])
    ax.set_title(f"Sector Dominance — Top {top_n} Drivers",
                 fontsize=16, fontweight="bold", pad=25, color=ACCENT_RED)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=9)

    _save(fig, "06_sector_radar")


# ---------------------------------------------------------------------------
# Public API — generate all charts at once
# ---------------------------------------------------------------------------

def generate_all_charts(laps, best_df, avg_df, speeds_df, colors):
    """Convenience wrapper to produce every chart."""
    print("\n🏎️  Generating F1 Sector Analysis Charts …\n")

    plot_best_sector_times(best_df, colors)
    plot_sector_heatmap(avg_df)
    plot_sector_violins(laps, colors)
    plot_speed_traps(speeds_df, colors)
    plot_lap_breakdown(best_df, colors)
    plot_sector_radar(best_df, colors)

    print(f"\n✅  All charts saved to {OUTPUT_DIR}/\n")


# ---------------------------------------------------------------------------
# 7. Head-to-Head Driver Comparison
# ---------------------------------------------------------------------------

def plot_driver_comparison(comparison: dict, colors: dict):
    """
    Rich head-to-head comparison chart for two drivers.

    Layout:
      • Top:    sector-by-sector delta bars + winner badges
      • Bottom: speed trap comparison bars
      • Footer: overall lap time verdict
    """
    _apply_f1_theme()

    d1, d2 = comparison["driver1"], comparison["driver2"]
    t1, t2 = comparison["team1"], comparison["team2"]
    c1 = colors.get(d1, "#00D2BE")
    c2 = colors.get(d2, "#E10600")

    # Ensure the two colours are visually distinct
    if c1 == c2 or (c1.upper() in ("#FFFFFF", "#FFF") and c2.upper() in ("#FFFFFF", "#FFF")):
        c1, c2 = "#00D2BE", "#E10600"

    sectors = comparison["sectors"]
    traps   = comparison["speed_traps"]

    fig = plt.figure(figsize=(16, 14))
    gs = fig.add_gridspec(3, 1, height_ratios=[1.2, 1.0, 0.3],
                          hspace=0.35)

    # ── Title ────────────────────────────────────────────────────────────
    fig.suptitle(
        f"{d1}  ({t1})   vs   {d2}  ({t2})",
        fontsize=20, fontweight="bold", color=TEXT_COLOR, y=0.97,
    )
    subtitle = (f"Lap {comparison['lap1_num']}  vs  "
                f"Lap {comparison['lap2_num']}")
    fig.text(0.5, 0.935, subtitle, ha="center", fontsize=13,
             color="#AAAAAA", style="italic")

    # ── Panel 1: Sector Time Comparison ──────────────────────────────────
    ax1 = fig.add_subplot(gs[0])

    sector_labels = [s["sector"] for s in sectors]
    times1 = [s["time1"] for s in sectors]
    times2 = [s["time2"] for s in sectors]
    deltas = [s["delta"] for s in sectors]
    winners = [s["faster"] for s in sectors]

    y = np.arange(len(sectors))
    bar_h = 0.35

    ax1.barh(y - bar_h / 2, times1, height=bar_h, color=c1,
             label=d1, alpha=0.9, edgecolor="none", zorder=3)
    ax1.barh(y + bar_h / 2, times2, height=bar_h, color=c2,
             label=d2, alpha=0.9, edgecolor="none", zorder=3)

    # Time labels on bars
    for i in range(len(sectors)):
        ax1.text(times1[i] + 0.1, y[i] - bar_h / 2, f"{times1[i]:.3f}s",
                 va="center", fontsize=9, color=TEXT_COLOR, zorder=4)
        ax1.text(times2[i] + 0.1, y[i] + bar_h / 2, f"{times2[i]:.3f}s",
                 va="center", fontsize=9, color=TEXT_COLOR, zorder=4)

        # Winner badge
        delta_str = f"Δ {abs(deltas[i]):.3f}s"
        badge_color = c1 if winners[i] == d1 else (c2 if winners[i] == d2 else GRID_COLOR)
        winner_text = f"◀ {winners[i]}  {delta_str}" if winners[i] != "TIE" else f"TIE  {delta_str}"
        ax1.annotate(
            winner_text,
            xy=(max(times1[i], times2[i]) + 0.8, y[i]),
            fontsize=10, fontweight="bold", color=badge_color,
            va="center", zorder=5,
        )

    ax1.set_yticks(y)
    ax1.set_yticklabels(sector_labels, fontsize=12, fontweight="bold")
    ax1.invert_yaxis()
    ax1.set_xlabel("Time (seconds)", fontsize=11)
    ax1.set_title("Sector Times", fontsize=14, fontweight="bold",
                  pad=10, color=ACCENT_RED)
    ax1.legend(loc="lower right", fontsize=11)
    ax1.grid(axis="x", linestyle="--", alpha=0.2, zorder=0)

    # ── Panel 2: Speed Trap Comparison ───────────────────────────────────
    ax2 = fig.add_subplot(gs[1])

    trap_labels = [t["trap"] for t in traps]
    speeds1 = [t["speed1"] for t in traps]
    speeds2 = [t["speed2"] for t in traps]
    trap_winners = [t["faster"] for t in traps]
    trap_deltas  = [t["delta"] for t in traps]

    x = np.arange(len(traps))
    w = 0.35

    bars1 = ax2.bar(x - w / 2, speeds1, width=w, color=c1, label=d1,
                    alpha=0.9, edgecolor="none", zorder=3)
    bars2 = ax2.bar(x + w / 2, speeds2, width=w, color=c2, label=d2,
                    alpha=0.9, edgecolor="none", zorder=3)

    # Speed labels on top of bars
    for i in range(len(traps)):
        ax2.text(x[i] - w / 2, speeds1[i] + 1, f"{speeds1[i]:.0f}",
                 ha="center", va="bottom", fontsize=9, color=c1,
                 fontweight="bold", zorder=4)
        ax2.text(x[i] + w / 2, speeds2[i] + 1, f"{speeds2[i]:.0f}",
                 ha="center", va="bottom", fontsize=9, color=c2,
                 fontweight="bold", zorder=4)

        # Winner indicator below x-axis label
        tw = trap_winners[i]
        td = abs(trap_deltas[i])
        badge_c = c1 if tw == d1 else (c2 if tw == d2 else GRID_COLOR)
        ax2.text(x[i], ax2.get_ylim()[0] if ax2.get_ylim()[0] else 0,
                 f"▲ {tw} +{td:.0f}",
                 ha="center", va="top", fontsize=8, color=badge_c,
                 fontweight="bold", zorder=4)

    ax2.set_xticks(x)
    ax2.set_xticklabels(trap_labels, fontsize=11, fontweight="bold")
    ax2.set_ylabel("Speed (km/h)", fontsize=11)
    ax2.set_title("Speed Traps", fontsize=14, fontweight="bold",
                  pad=10, color=ACCENT_RED)
    ax2.legend(loc="upper right", fontsize=11)
    ax2.grid(axis="y", linestyle="--", alpha=0.2, zorder=0)

    # Adjust y-limits for speed panel
    all_sp = speeds1 + speeds2
    ax2.set_ylim(min(all_sp) - 20, max(all_sp) + 15)

    # ── Panel 3: Overall Verdict ─────────────────────────────────────────
    ax3 = fig.add_subplot(gs[2])
    ax3.axis("off")

    ot1 = comparison["overall_time1"]
    ot2 = comparison["overall_time2"]
    od  = comparison["overall_delta"]
    ow  = comparison["overall_faster"]

    verdict_color = c1 if ow == d1 else (c2 if ow == d2 else TEXT_COLOR)
    sectors_won_d1 = sum(1 for s in sectors if s["faster"] == d1)
    sectors_won_d2 = sum(1 for s in sectors if s["faster"] == d2)

    verdict_lines = [
        f">>>  {ow} FASTER BY {abs(od):.3f}s  <<<" if ow != "TIE" else ">>>  DEAD HEAT  <<<",
        f"{d1}: {ot1:.3f}s  (Lap {comparison['lap1_num']})     "
        f"{d2}: {ot2:.3f}s  (Lap {comparison['lap2_num']})",
        f"Sectors won:   {d1} {sectors_won_d1}  –  {sectors_won_d2} {d2}",
    ]

    ax3.text(0.5, 0.75, verdict_lines[0], transform=ax3.transAxes,
             ha="center", fontsize=18, fontweight="bold", color=verdict_color)
    ax3.text(0.5, 0.35, verdict_lines[1], transform=ax3.transAxes,
             ha="center", fontsize=12, color=TEXT_COLOR)
    ax3.text(0.5, 0.0, verdict_lines[2], transform=ax3.transAxes,
             ha="center", fontsize=12, color="#AAAAAA")

    _save(fig, f"07_comparison_{d1}_vs_{d2}")


# ---------------------------------------------------------------------------
# 8. Track Dominance Map
# ---------------------------------------------------------------------------

def plot_track_dominance(dom_data: dict, colors: dict):
    """
    Draw the circuit coloured by which driver is faster at each point —
    the "Track Dominance" graphic seen on F1 TV broadcasts.
    """
    _apply_f1_theme()

    d1, d2 = dom_data["driver1"], dom_data["driver2"]
    t1, t2 = dom_data["team1"], dom_data["team2"]
    c1 = colors.get(d1, "#00D2BE")
    c2 = colors.get(d2, "#E10600")

    # Ensure distinct colours
    if c1 == c2 or (c1.upper() in ("#FFFFFF", "#FFF") and c2.upper() in ("#FFFFFF", "#FFF")):
        c1, c2 = "#00D2BE", "#E10600"

    x = dom_data["x"]
    y = dom_data["y"]
    dominance = dom_data["dominance"]

    # ── Build coloured line collection ──────────────────────────────────
    points = np.column_stack([x, y]).reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    # Map dominance to 0 (driver2) / 1 (driver1) for the colourmap
    seg_dom = dominance[:-1]  # colour each segment by its start point
    seg_colors = np.array([c1 if d == 1 else c2 for d in seg_dom])

    fig, ax = plt.subplots(figsize=(14, 12))
    fig.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    # Background track line (slightly wider, dark)
    bg_lc = LineCollection(segments, linewidths=7,
                           colors=CARD_COLOR, zorder=1)
    ax.add_collection(bg_lc)

    # Coloured track dominance line
    for seg, color in zip(segments, seg_colors):
        ax.plot(seg[:, 0], seg[:, 1], color=color, linewidth=4.5,
                solid_capstyle="round", zorder=2)

    # ── Start/Finish marker ─────────────────────────────────────────────
    ax.plot(x[0], y[0], "o", color=TEXT_COLOR, markersize=10, zorder=5)
    ax.annotate("START / FINISH", (x[0], y[0]),
                textcoords="offset points", xytext=(15, 15),
                fontsize=9, fontweight="bold", color=TEXT_COLOR,
                arrowprops=dict(arrowstyle="->", color=GRID_COLOR, lw=1.2),
                zorder=5)

    # ── Sector boundary markers (approx 1/3 and 2/3 distance) ──────────
    n = len(x)
    for frac, label in [(1/3, "S1 | S2"), (2/3, "S2 | S3")]:
        idx = int(frac * n)
        ax.plot(x[idx], y[idx], "s", color=ACCENT_RED, markersize=6, zorder=5)
        ax.annotate(label, (x[idx], y[idx]),
                    textcoords="offset points", xytext=(10, -15),
                    fontsize=8, color="#AAAAAA", zorder=5)

    # ── Equal axes, hide ticks ──────────────────────────────────────────
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Padding
    pad_x = (x.max() - x.min()) * 0.08
    pad_y = (y.max() - y.min()) * 0.08
    ax.set_xlim(x.min() - pad_x, x.max() + pad_x)
    ax.set_ylim(y.min() - pad_y, y.max() + pad_y)

    # ── Title ───────────────────────────────────────────────────────────
    fig.suptitle("TRACK DOMINANCE", fontsize=22, fontweight="bold",
                 color=TEXT_COLOR, y=0.95)
    fig.text(0.5, 0.91,
             f"{d1} ({t1})  vs  {d2} ({t2})   |   "
             f"Lap {dom_data['lap1_num']} vs Lap {dom_data['lap2_num']}",
             ha="center", fontsize=12, color="#AAAAAA")

    # ── Legend ──────────────────────────────────────────────────────────
    from matplotlib.patches import Patch
    d1_pct = int((dominance == 1).sum() / len(dominance) * 100)
    d2_pct = int((dominance == -1).sum() / len(dominance) * 100)
    legend_elements = [
        Patch(facecolor=c1, edgecolor="none",
              label=f"{d1}  ({d1_pct}%)"),
        Patch(facecolor=c2, edgecolor="none",
              label=f"{d2}  ({d2_pct}%)"),
    ]
    leg = ax.legend(handles=legend_elements, loc="lower center",
                    bbox_to_anchor=(0.5, -0.02), ncol=2, fontsize=14,
                    frameon=True, facecolor=CARD_COLOR, edgecolor=GRID_COLOR,
                    labelcolor=TEXT_COLOR, handlelength=2, handleheight=1.2)
    leg.get_frame().set_alpha(0.85)

    _save(fig, f"08_track_dominance_{d1}_vs_{d2}")

