"""
Plot Sweep Results
==================
Reads the CSVs produced by evaluation_script.py and generates charts.

Supports two modes (auto-detected from the session folder, or forced with --mode):

  ┌─ runs_sweep ──────────────────────────────────────────────────────────────┐
  │  Source : runs_sweep_results.csv + runs_sweep_llm_detail.csv              │
  │  X-axis : run number (1, 2, 3, …)                                         │
  │  Use    : analyse the stochastic variability of LLM models                │
  │           with a fixed number of LLM iterations                           │
  │                                                                            │
  │  Fig 1 – Generation time vs run                                           │
  │  Fig 2 – RGED and Cross-Fitness vs run                                    │
  │  Fig 3 – Errors and LLM sub-iteration quality vs run                      │
  │  Fig 4 – Heatmap of per-sub-iteration state × run                         │
  └───────────────────────────────────────────────────────────────────────────┘

  ┌─ sweep (iterations) ──────────────────────────────────────────────────────┐
  │  Source : sweep_iterations_results.csv + sweep_llm_iterations_detail.csv  │
  │  X-axis : max_llm_iterations                                              │
  │  Use    : analyse how metrics change as the number of                     │
  │           Generator↔Validator iterations varies                           │
  │                                                                            │
  │  Fig 1 – Execution time vs LLM iterations                                 │
  │  Fig 2 – RGED and Cross-Fitness vs LLM iterations                         │
  │  Fig 3 – Errors per configuration vs LLM iterations                       │
  │  Fig 4 – Heatmap of per-sub-iteration state × configuration               │
  └───────────────────────────────────────────────────────────────────────────┘

Usage
-----
  python plot_sweep_results.py                         # auto-detect latest session
  python plot_sweep_results.py --mode runs_sweep       # force runs_sweep mode
  python plot_sweep_results.py --mode sweep            # force sweep mode
  python plot_sweep_results.py --session <path>        # specify session folder
  python plot_sweep_results.py --summary <file.csv>    # specify summary CSV
  python plot_sweep_results.py --save                  # save charts to disk

Quick configuration via .env:
  EVAL_PLOT_SESSION_DIR=evaluation_results/session_YYYYMMDD_HHMMSS
  EVAL_PLOT_SAVE=false
  EVAL_PLOT_MODE=runs_sweep   # or 'sweep'
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

# ---------------------------------------------------------------------------
# Global style
# ---------------------------------------------------------------------------
plt.rcParams.update({
    "figure.dpi": 130,
    "axes.grid": True,
    "grid.alpha": 0.35,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "font.size": 11,
})

PALETTE = {
    "time":        "#2196F3",
    "rged":        "#E53935",
    "cross_fit":   "#43A047",
    "fit_orig":    "#7E57C2",
    "fit_mit":     "#FF7043",
    "xml_err":     "#E53935",
    "issues":      "#FF9800",
    "invalid":     "#9C27B0",
    "failed":      "#607D8B",
    "valid":       "#43A047",
    "mean":        "#1A237E",
    "band":        "#BBDEFB",
}

# ---------------------------------------------------------------------------
# Shared utilities
# ---------------------------------------------------------------------------

def _latest_session(output_dir: str) -> Path:
    base = Path(output_dir)
    sessions = sorted(base.glob("session_*"), reverse=True)
    if not sessions:
        sys.exit(f"[ERROR] No session found in '{output_dir}'")
    return sessions[0]


def _load_csv(path: Path, label: str) -> pd.DataFrame:
    if not path.exists():
        print(f"[WARNING] File not found: {path}  ({label} skipped)")
        return pd.DataFrame()
    df = pd.read_csv(path)
    print(f"[OK] Loaded '{path.name}'  →  {len(df)} rows, columns: {list(df.columns)}")
    return df


def _to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _annotate(ax, xs, ys, fmt="{:.3f}", color="black", offset=(0, 6)):
    for x, y in zip(xs, ys):
        if pd.notna(y):
            ax.annotate(
                fmt.format(y),
                xy=(x, y), xytext=offset,
                textcoords="offset points",
                fontsize=8, color=color,
                ha="center"
            )


def _auto_detect_mode(session_dir: Path) -> str:
    """Auto-detect the mode from the CSV files present in the session folder."""
    if (session_dir / "runs_sweep_results.csv").exists():
        return "runs_sweep"
    if (session_dir / "sweep_iterations_results.csv").exists():
        return "sweep"
    return "runs_sweep"   # default


# ============================================================================
# ██████╗ ██╗   ██╗███╗   ██╗███████╗    ███████╗██╗    ██╗███████╗███████╗██████╗
# ██╔══██╗██║   ██║████╗  ██║██╔════╝    ██╔════╝██║    ██║██╔════╝██╔════╝██╔══██╗
# ██████╔╝██║   ██║██╔██╗ ██║███████╗    ███████╗██║ █╗ ██║█████╗  █████╗  ██████╔╝
# ██╔══██╗██║   ██║██║╚██╗██║╚════██║    ╚════██║██║███╗██║██╔══╝  ██╔══╝  ██╔═══╝
# ██║  ██║╚██████╔╝██║ ╚████║███████║    ███████║╚███╔███╔╝███████╗███████╗██║
# ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝    ╚══════╝ ╚══╝╚══╝ ╚══════╝╚══════╝╚═╝
#  X-axis = run_number  |  fixed LLM iterations
# ============================================================================

def runs_fig1_execution_time(df: pd.DataFrame, save_dir: Optional[Path] = None):
    """Fig 1 – Generation time vs run_number."""
    if df.empty or "generation_time_s" not in df.columns:
        print("[WARNING] Timing data not available, figure 1 skipped.")
        return

    xs = _to_numeric(df["run_number"])
    ys = _to_numeric(df["generation_time_s"])
    mask = xs.notna() & ys.notna()

    fixed_iter = int(df["max_llm_iterations"].iloc[0]) if "max_llm_iterations" in df.columns else "?"

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(xs[mask], ys[mask],
            marker="o", linewidth=2, markersize=7,
            color=PALETTE["time"], label="Generation time (s)")

    failed = df[df["generation_success"].astype(str).str.lower() != "true"]
    if not failed.empty:
        fx = _to_numeric(failed["run_number"])
        fy = _to_numeric(failed["generation_time_s"]).fillna(0)
        ax.scatter(fx, fy, marker="X", s=120, color="red", zorder=5, label="Generation failed")

    _annotate(ax, xs[mask], ys[mask], fmt="{:.1f}s", color=PALETTE["time"])

    ax.set_xlabel("Run #")
    ax.set_ylabel("Generation time (seconds)")
    ax.set_title(f"Execution time vs Run #  (fixed LLM iterations = {fixed_iter})")
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.legend()
    fig.tight_layout()
    _save_or_show(fig, save_dir, "fig1_execution_time.png")


def runs_fig2_rged_fitness(df: pd.DataFrame, save_dir: Optional[Path] = None):
    """Fig 2 – RGED and fitness vs run_number."""
    cols_needed = {"run_number", "normalized_ged", "behavioral_similarity"}
    if df.empty or not cols_needed.issubset(df.columns):
        print("[WARNING] RGED/fitness columns not available, figure 2 skipped.")
        return

    fixed_iter = int(df["max_llm_iterations"].iloc[0]) if "max_llm_iterations" in df.columns else "?"

    xs    = _to_numeric(df["run_number"])
    rged  = _to_numeric(df["normalized_ged"])
    cross = _to_numeric(df["behavioral_similarity"])

    fig, ax1 = plt.subplots(figsize=(9, 5))
    ax2 = ax1.twinx()

    mask_r = xs.notna() & rged.notna()
    l1, = ax1.plot(xs[mask_r], rged[mask_r],
                   marker="s", linewidth=2, markersize=7,
                   color=PALETTE["rged"], label="Normalised RGED")
    _annotate(ax1, xs[mask_r], rged[mask_r], fmt="{:.4f}", color=PALETTE["rged"], offset=(0, 8))

    mask_c = xs.notna() & cross.notna()
    l2, = ax2.plot(xs[mask_c], cross[mask_c],
                   marker="o", linewidth=2, markersize=7,
                   color=PALETTE["cross_fit"], label="Cross-Fitness (behavioural similarity)")
    _annotate(ax2, xs[mask_c], cross[mask_c], fmt="{:.4f}", color=PALETTE["cross_fit"], offset=(0, -14))

    ax1.set_xlabel("Run #")
    ax1.set_ylabel("Normalised RGED  ↑ more different", color=PALETTE["rged"])
    ax2.set_ylabel("Fitness  ↑ more similar", color=PALETTE["cross_fit"])
    ax1.set_title(f"RGED and Cross-Fitness vs Run #  (fixed LLM iterations = {fixed_iter})")
    ax1.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax1.tick_params(axis="y", labelcolor=PALETTE["rged"])
    ax2.tick_params(axis="y", labelcolor=PALETTE["cross_fit"])
    ax1.set_ylim(bottom=0)
    ax2.set_ylim(0, 1.05)

    ax1.legend([l1, l2], [l1.get_label(), l2.get_label()], loc="upper left", fontsize=9)
    fig.tight_layout()
    _save_or_show(fig, save_dir, "fig2_rged_fitness.png")


def runs_fig3_errors(df: pd.DataFrame, save_dir: Optional[Path] = None):
    """Fig 3 – Errors per run vs run_number."""
    cols_check = {"run_number", "llm_xml_errors_count",
                  "llm_final_issues_count", "llm_valid_iter_count", "llm_actual_iterations"}
    if df.empty or not cols_check.issubset(df.columns):
        print("[WARNING] Error columns not available, figure 3 skipped.")
        return

    fixed_iter = int(df["max_llm_iterations"].iloc[0]) if "max_llm_iterations" in df.columns else "?"

    xs        = _to_numeric(df["run_number"])
    xml_err   = _to_numeric(df["llm_xml_errors_count"]).fillna(0)
    issues    = _to_numeric(df["llm_final_issues_count"]).fillna(0)
    actual    = _to_numeric(df["llm_actual_iterations"]).fillna(0)
    valid_c   = _to_numeric(df["llm_valid_iter_count"]).fillna(0)
    invalid_c = (actual - valid_c - xml_err).clip(lower=0)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle(
        f"Errors and LLM sub-iteration validity vs Run #  (fixed LLM iterations = {fixed_iter})",
        y=1.01
    )

    mask  = xs.notna()
    width = 0.35
    x_pos = np.arange(mask.sum())

    ax = axes[0]
    b1 = ax.bar(x_pos - width / 2, xml_err[mask], width,
                color=PALETTE["xml_err"], alpha=0.85, label="XML errors")
    b2 = ax.bar(x_pos + width / 2, issues[mask], width,
                color=PALETTE["issues"], alpha=0.85, label="Validator issues (last iter)")
    ax.set_xticks(x_pos); ax.set_xticklabels(xs[mask].astype(int), fontsize=10)
    ax.set_xlabel("Run #")
    ax.set_ylabel("Error / issue count")
    ax.set_title("XML Errors and Validator Issues")
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.legend(fontsize=9)
    for bar in (*b1, *b2):
        h = bar.get_height()
        if h > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, h + 0.05,
                    str(int(h)), ha="center", va="bottom", fontsize=8)

    ax2 = axes[1]
    ax2.bar(x_pos, valid_c[mask],   color=PALETTE["valid"],   alpha=0.85, label="Valid sub-iters")
    ax2.bar(x_pos, invalid_c[mask], bottom=valid_c[mask],
            color=PALETTE["invalid"], alpha=0.75, label="Invalid sub-iters")
    ax2.bar(x_pos, xml_err[mask],   bottom=valid_c[mask] + invalid_c[mask],
            color=PALETTE["xml_err"], alpha=0.75, label="XML errors / generation failed")
    ax2.set_xticks(x_pos); ax2.set_xticklabels(xs[mask].astype(int), fontsize=10)
    ax2.set_xlabel("Run #")
    ax2.set_ylabel("Number of sub-iterations")
    ax2.set_title("LLM Sub-iteration Breakdown")
    ax2.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax2.legend(fontsize=9)

    fig.tight_layout()
    _save_or_show(fig, save_dir, "fig3_errors.png")


def runs_fig4_heatmap(detail_df: pd.DataFrame, save_dir: Optional[Path] = None):
    """Fig 4 – Heatmap (run × sub-iteration) of the validation state."""
    if detail_df.empty:
        print("[WARNING] Detail CSV is empty, figure 4 skipped.")
        return
    req = {"run_number", "llm_sub_iteration", "validator_passed", "xml_valid"}
    if not req.issubset(detail_df.columns):
        print("[WARNING] Missing columns in detail CSV, figure 4 skipped.")
        return

    dfc = detail_df.copy()
    dfc["run_number"]        = _to_numeric(dfc["run_number"])
    dfc["llm_sub_iteration"] = _to_numeric(dfc["llm_sub_iteration"])

    def _status_code(row):
        vp = str(row.get("validator_passed", "")).lower() in ("true", "1")
        xv = str(row.get("xml_valid",        "")).lower() in ("true", "1")
        return 2 if vp else (1 if xv else 0)

    dfc["_code"] = dfc.apply(_status_code, axis=1)

    runs     = sorted(dfc["run_number"].dropna().unique().astype(int))
    max_sub  = int(dfc["llm_sub_iteration"].max())
    sub_list = list(range(1, max_sub + 1))

    matrix = np.full((len(runs), len(sub_list)), np.nan)
    for _, row in dfc.dropna(subset=["run_number", "llm_sub_iteration"]).iterrows():
        r = runs.index(int(row["run_number"]))
        c = int(row["llm_sub_iteration"]) - 1
        if 0 <= c < len(sub_list):
            matrix[r, c] = row["_code"]

    fixed_iter = int(dfc["max_llm_iterations"].iloc[0]) if "max_llm_iterations" in dfc.columns else "?"

    cmap = matplotlib.colors.ListedColormap(["#EF5350", "#FFA726", "#66BB6A"])
    cmap.set_bad(color="#EEEEEE")

    fig, ax = plt.subplots(figsize=(max(7, max_sub * 1.1), max(4, len(runs) * 0.8)))
    ax.imshow(matrix, cmap=cmap, vmin=0, vmax=2, aspect="auto")

    ax.set_xticks(range(len(sub_list)))
    ax.set_xticklabels([f"Sub-iter {s}" for s in sub_list], fontsize=9)
    ax.set_yticks(range(len(runs)))
    ax.set_yticklabels([f"Run {n}" for n in runs], fontsize=9)
    ax.set_xlabel("LLM sub-iteration")
    ax.set_ylabel("Run #")
    ax.set_title(
        f"State of each LLM sub-iteration  (fixed LLM iterations = {fixed_iter})\n"
        "(🟢 Validator OK  🟡 XML ok, Validator KO  🔴 XML error)"
    )

    status_label = {2: "valid", 1: "invalid", 0: "XML err"}
    for r in range(len(runs)):
        for c in range(len(sub_list)):
            v = matrix[r, c]
            if not np.isnan(v):
                ax.text(c, r, status_label[int(v)],
                        ha="center", va="center", fontsize=7.5,
                        color="white" if v != 1 else "black")

    from matplotlib.patches import Patch
    legend_els = [
        Patch(facecolor="#66BB6A", label="Validator approved"),
        Patch(facecolor="#FFA726", label="XML valid, Validator KO"),
        Patch(facecolor="#EF5350", label="XML error / generation failed"),
        Patch(facecolor="#EEEEEE", label="Not executed"),
    ]
    ax.legend(handles=legend_els, loc="upper right",
              bbox_to_anchor=(1.0, -0.12), ncol=2, fontsize=9)

    fig.tight_layout()
    _save_or_show(fig, save_dir, "fig4_iteration_detail_heatmap.png")


# ============================================================================
# ██╗████████╗███████╗██████╗  █████╗ ████████╗██╗ ██████╗ ███╗   ██╗███████╗
# ██║╚══██╔══╝██╔════╝██╔══██╗██╔══██╗╚══██╔══╝██║██╔═══██╗████╗  ██║██╔════╝
# ██║   ██║   █████╗  ██████╔╝███████║   ██║   ██║██║   ██║██╔██╗ ██║███████╗
# ██║   ██║   ██╔══╝  ██╔══██╗██╔══██║   ██║   ██║██║   ██║██║╚██╗██║╚════██║
# ██║   ██║   ███████╗██║  ██║██║  ██║   ██║   ██║╚██████╔╝██║ ╚████║███████║
# ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝
#  X-axis = max_llm_iterations  |  fixed number of runs (= 1)
# ============================================================================

def plot_execution_time(df: pd.DataFrame, save_dir: Optional[Path] = None):
    """Fig 1 – Generation time vs max_llm_iterations."""
    if df.empty or "generation_time_s" not in df.columns:
        print("[WARNING] Timing data not available, figure 1 skipped.")
        return

    xs = _to_numeric(df["max_llm_iterations"])
    ys = _to_numeric(df["generation_time_s"])
    mask = xs.notna() & ys.notna()

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(xs[mask], ys[mask],
            marker="o", linewidth=2, markersize=7,
            color=PALETTE["time"], label="Generation time (s)")

    failed = df[df["generation_success"].astype(str).str.lower() != "true"]
    if not failed.empty:
        fx = _to_numeric(failed["max_llm_iterations"])
        fy = _to_numeric(failed["generation_time_s"]).fillna(0)
        ax.scatter(fx, fy, marker="X", s=120, color="red", zorder=5, label="Generation failed")

    _annotate(ax, xs[mask], ys[mask], fmt="{:.1f}s", color=PALETTE["time"])

    ax.set_xlabel("Max LLM iterations")
    ax.set_ylabel("Generation time (seconds)")
    ax.set_title("Execution time vs LLM Iterations")
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.legend()
    fig.tight_layout()
    _save_or_show(fig, save_dir, "fig1_execution_time.png")


def plot_rged_and_fitness(df: pd.DataFrame, save_dir: Optional[Path] = None):
    """Fig 2 – RGED and fitness vs max_llm_iterations."""
    cols_needed = {"max_llm_iterations", "normalized_ged", "behavioral_similarity"}
    if df.empty or not cols_needed.issubset(df.columns):
        print("[WARNING] RGED/fitness columns not available, figure 2 skipped.")
        return

    xs    = _to_numeric(df["max_llm_iterations"])
    rged  = _to_numeric(df["normalized_ged"])
    cross = _to_numeric(df["behavioral_similarity"])

    fig, ax1 = plt.subplots(figsize=(9, 5))
    ax2 = ax1.twinx()

    mask_r = xs.notna() & rged.notna()
    l1, = ax1.plot(xs[mask_r], rged[mask_r],
                   marker="s", linewidth=2, markersize=7,
                   color=PALETTE["rged"], label="Normalised RGED")
    _annotate(ax1, xs[mask_r], rged[mask_r], fmt="{:.4f}", color=PALETTE["rged"], offset=(0, 8))

    mask_c = xs.notna() & cross.notna()
    l2, = ax2.plot(xs[mask_c], cross[mask_c],
                   marker="o", linewidth=2, markersize=7,
                   color=PALETTE["cross_fit"], label="Cross-Fitness (behavioural similarity)")
    _annotate(ax2, xs[mask_c], cross[mask_c], fmt="{:.4f}", color=PALETTE["cross_fit"], offset=(0, -14))

    ax1.set_xlabel("Max LLM iterations")
    ax1.set_ylabel("Normalised RGED  ↑ more different", color=PALETTE["rged"])
    ax2.set_ylabel("Fitness  ↑ more similar", color=PALETTE["cross_fit"])
    ax1.set_title("RGED and Cross-Fitness vs LLM Iterations")
    ax1.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax1.tick_params(axis="y", labelcolor=PALETTE["rged"])
    ax2.tick_params(axis="y", labelcolor=PALETTE["cross_fit"])
    ax1.set_ylim(bottom=0)
    ax2.set_ylim(0, 1.05)

    ax1.legend([l1, l2], [l1.get_label(), l2.get_label()], loc="upper left", fontsize=9)
    fig.tight_layout()
    _save_or_show(fig, save_dir, "fig2_rged_fitness.png")


def plot_errors(df: pd.DataFrame, save_dir: Optional[Path] = None):
    """Fig 3 – Errors per configuration vs max_llm_iterations."""
    cols_check = {"max_llm_iterations", "llm_xml_errors_count",
                  "llm_final_issues_count", "llm_valid_iter_count", "llm_actual_iterations"}
    if df.empty or not cols_check.issubset(df.columns):
        print("[WARNING] Error columns not available, figure 3 skipped.")
        return

    xs       = _to_numeric(df["max_llm_iterations"])
    xml_err  = _to_numeric(df["llm_xml_errors_count"]).fillna(0)
    issues   = _to_numeric(df["llm_final_issues_count"]).fillna(0)
    actual   = _to_numeric(df["llm_actual_iterations"]).fillna(0)
    valid_c  = _to_numeric(df["llm_valid_iter_count"]).fillna(0)
    invalid_c = (actual - valid_c - xml_err).clip(lower=0)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle("Errors and LLM sub-iteration validity vs LLM Iterations", y=1.01)

    mask  = xs.notna()
    width = 0.35
    x_pos = np.arange(mask.sum())

    ax = axes[0]
    b1 = ax.bar(x_pos - width / 2, xml_err[mask], width,
                color=PALETTE["xml_err"], alpha=0.85, label="XML errors")
    b2 = ax.bar(x_pos + width / 2, issues[mask], width,
                color=PALETTE["issues"], alpha=0.85, label="Validator issues (last iter)")
    ax.set_xticks(x_pos); ax.set_xticklabels(xs[mask].astype(int), fontsize=10)
    ax.set_xlabel("Max LLM iterations")
    ax.set_ylabel("Error / issue count")
    ax.set_title("XML Errors and Validator Issues")
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.legend(fontsize=9)
    for bar in (*b1, *b2):
        h = bar.get_height()
        if h > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, h + 0.05,
                    str(int(h)), ha="center", va="bottom", fontsize=8)

    ax2 = axes[1]
    ax2.bar(x_pos, valid_c[mask],   color=PALETTE["valid"],   alpha=0.85, label="Valid sub-iters")
    ax2.bar(x_pos, invalid_c[mask], bottom=valid_c[mask],
            color=PALETTE["invalid"], alpha=0.75, label="Invalid sub-iters")
    ax2.bar(x_pos, xml_err[mask],   bottom=valid_c[mask] + invalid_c[mask],
            color=PALETTE["xml_err"], alpha=0.75, label="XML errors / generation failed")
    ax2.set_xticks(x_pos); ax2.set_xticklabels(xs[mask].astype(int), fontsize=10)
    ax2.set_xlabel("Max LLM iterations")
    ax2.set_ylabel("Number of sub-iterations")
    ax2.set_title("LLM Sub-iteration Breakdown")
    ax2.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax2.legend(fontsize=9)

    fig.tight_layout()
    _save_or_show(fig, save_dir, "fig3_errors.png")


def plot_iteration_detail(detail_df: pd.DataFrame, save_dir: Optional[Path] = None):
    """Fig 4 – Heatmap (max_iter × sub-iter) of the validation state."""
    if detail_df.empty:
        print("[WARNING] Detail CSV is empty, figure 4 skipped.")
        return
    req = {"max_llm_iterations", "llm_sub_iteration", "validator_passed", "xml_valid"}
    if not req.issubset(detail_df.columns):
        print("[WARNING] Missing columns in detail CSV, figure 4 skipped.")
        return

    dfc = detail_df.copy()
    dfc["max_llm_iterations"] = _to_numeric(dfc["max_llm_iterations"])
    dfc["llm_sub_iteration"]  = _to_numeric(dfc["llm_sub_iteration"])

    def _status_code(row):
        vp = str(row.get("validator_passed", "")).lower() in ("true", "1")
        xv = str(row.get("xml_valid",        "")).lower() in ("true", "1")
        return 2 if vp else (1 if xv else 0)

    dfc["_code"] = dfc.apply(_status_code, axis=1)

    max_iters = sorted(dfc["max_llm_iterations"].dropna().unique().astype(int))
    max_sub   = int(dfc["llm_sub_iteration"].max())
    sub_iters = list(range(1, max_sub + 1))

    matrix = np.full((len(max_iters), len(sub_iters)), np.nan)
    for _, row in dfc.dropna(subset=["max_llm_iterations", "llm_sub_iteration"]).iterrows():
        r = max_iters.index(int(row["max_llm_iterations"]))
        c = int(row["llm_sub_iteration"]) - 1
        if 0 <= c < len(sub_iters):
            matrix[r, c] = row["_code"]

    cmap = matplotlib.colors.ListedColormap(["#EF5350", "#FFA726", "#66BB6A"])
    cmap.set_bad(color="#EEEEEE")

    fig, ax = plt.subplots(figsize=(max(7, max_sub * 1.1), max(4, len(max_iters) * 0.8)))
    ax.imshow(matrix, cmap=cmap, vmin=0, vmax=2, aspect="auto")

    ax.set_xticks(range(len(sub_iters)))
    ax.set_xticklabels([f"Sub-iter {s}" for s in sub_iters], fontsize=9)
    ax.set_yticks(range(len(max_iters)))
    ax.set_yticklabels([f"max_iter={n}" for n in max_iters], fontsize=9)
    ax.set_xlabel("LLM sub-iteration")
    ax.set_ylabel("Configuration (max_llm_iterations)")
    ax.set_title("State of each LLM sub-iteration\n"
                 "(🟢 Validator OK  🟡 XML ok, Validator KO  🔴 XML error)")

    status_label = {2: "valid", 1: "invalid", 0: "XML err"}
    for r in range(len(max_iters)):
        for c in range(len(sub_iters)):
            v = matrix[r, c]
            if not np.isnan(v):
                ax.text(c, r, status_label[int(v)],
                        ha="center", va="center", fontsize=7.5,
                        color="white" if v != 1 else "black")

    from matplotlib.patches import Patch
    legend_els = [
        Patch(facecolor="#66BB6A", label="Validator approved"),
        Patch(facecolor="#FFA726", label="XML valid, Validator KO"),
        Patch(facecolor="#EF5350", label="XML error / generation failed"),
        Patch(facecolor="#EEEEEE", label="Not executed"),
    ]
    ax.legend(handles=legend_els, loc="upper right",
              bbox_to_anchor=(1.0, -0.12), ncol=2, fontsize=9)

    fig.tight_layout()
    _save_or_show(fig, save_dir, "fig4_iteration_detail_heatmap.png")


# ---------------------------------------------------------------------------
# Save / show helper
# ---------------------------------------------------------------------------

def _save_or_show(fig, save_dir: Optional[Path], filename: str):
    if save_dir:
        out = save_dir / filename
        fig.savefig(out, bbox_inches="tight")
        print(f"[SAVED] {out}")
    else:
        plt.show()
    plt.close(fig)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Generate charts from evaluation_script.py sweep results."
    )
    parser.add_argument("--mode",    type=str, default=None,
                        choices=["runs_sweep", "sweep"],
                        help="Mode: 'runs_sweep' (X=run) or 'sweep' (X=LLM iterations). "
                             "Default: auto-detected from the session.")
    parser.add_argument("--session", type=str, default=None,
                        help="Path to the session folder")
    parser.add_argument("--summary", type=str, default=None,
                        help="Direct path to the summary CSV")
    parser.add_argument("--detail",  type=str, default=None,
                        help="Direct path to the sub-iteration detail CSV")
    parser.add_argument("--save",    action="store_true",
                        help="Save charts to disk instead of displaying them")
    parser.add_argument("--output",  type=str, default=None,
                        help="Directory where charts will be saved")
    args = parser.parse_args()

    env_session    = os.getenv("EVAL_PLOT_SESSION_DIR", "")
    env_save       = os.getenv("EVAL_PLOT_SAVE", "false").lower() == "true"
    env_output     = os.getenv("EVAL_PLOT_OUTPUT_DIR", "")
    env_mode       = os.getenv("EVAL_PLOT_MODE", "")
    output_dir_env = os.getenv("EVAL_OUTPUT_DIR", "evaluation_results")

    save_figures = args.save or env_save

    # ── Resolve session folder ────────────────────────────────────────────────
    if args.summary:
        session_dir = Path(args.summary).parent
    elif args.session:
        session_dir = Path(args.session)
    elif env_session:
        session_dir = Path(env_session)
    else:
        session_dir = _latest_session(output_dir_env)

    # ── Auto-detect mode ──────────────────────────────────────────────────────
    mode = args.mode or env_mode or _auto_detect_mode(session_dir)

    # ── Resolve CSV paths based on mode ──────────────────────────────────────
    if mode == "runs_sweep":
        default_summary = session_dir / "runs_sweep_results.csv"
        default_detail  = session_dir / "runs_sweep_llm_detail.csv"
    else:
        default_summary = session_dir / "sweep_iterations_results.csv"
        default_detail  = session_dir / "sweep_llm_iterations_detail.csv"

    summary_csv = Path(args.summary) if args.summary else default_summary
    detail_csv  = Path(args.detail)  if args.detail  else default_detail

    print(f"\n{'='*65}")
    print(f"  Mode    : {mode}")
    print(f"  Session : {session_dir}")
    print(f"  Summary : {summary_csv}")
    print(f"  Detail  : {detail_csv}")
    print(f"  Output  : {'SAVE CHARTS' if save_figures else 'SHOW CHARTS'}")
    print(f"{'='*65}\n")

    # ── Load CSVs ─────────────────────────────────────────────────────────────
    df     = _load_csv(summary_csv, "summary CSV")
    det_df = _load_csv(detail_csv,  "sub-iter detail CSV")

    if df.empty:
        sys.exit("[ERROR] Summary CSV is empty or does not exist. "
                 "Run evaluation_script.py first.")

    # ── Output directory ──────────────────────────────────────────────────────
    if save_figures:
        if args.output:
            out_dir = Path(args.output)
        elif env_output:
            out_dir = Path(env_output)
        else:
            out_dir = session_dir / "plots"
        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"  Charts output: {out_dir}\n")
    else:
        out_dir = None

    # ── Generate charts ───────────────────────────────────────────────────────
    if mode == "runs_sweep":
        print("[1/4] Fig.1 – Generation time vs run...")
        runs_fig1_execution_time(df, out_dir)

        print("[2/4] Fig.2 – RGED and Cross-Fitness vs run...")
        runs_fig2_rged_fitness(df, out_dir)

        print("[3/4] Fig.3 – Errors vs run...")
        runs_fig3_errors(df, out_dir)

        print("[4/4] Fig.4 – Sub-iteration × run heatmap...")
        runs_fig4_heatmap(det_df, out_dir)

    else:  # mode == "sweep"
        print("[1/4] Fig.1 – Execution time vs LLM iterations...")
        plot_execution_time(df, out_dir)

        print("[2/4] Fig.2 – RGED and Cross-Fitness vs LLM iterations...")
        plot_rged_and_fitness(df, out_dir)

        print("[3/4] Fig.3 – Errors vs LLM iterations...")
        plot_errors(df, out_dir)

        print("[4/4] Fig.4 – Sub-iteration detail heatmap...")
        plot_iteration_detail(det_df, out_dir)

    print(f"\n{'='*65}")
    print("  ✓ All charts generated.")
    if save_figures:
        print(f"  Saved to: {out_dir}")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    main()
