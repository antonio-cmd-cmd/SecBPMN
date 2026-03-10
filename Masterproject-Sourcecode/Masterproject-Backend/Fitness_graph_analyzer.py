"""
Sweep Analyzer – BPMN LLM Iteration Evaluation
===============================================

Reads the CSV files produced by evaluation_script.py (sweep mode) and generates three figures:

  Figure 1 – Execution time
      Line chart: generation_time_s  vs  max_llm_iterations

  Figure 2 – Structural / behavioural quality
      Line chart: normalized_ged (RGED) and behavioral_similarity (cross-fitness)
      vs max_llm_iterations

  Figure 3 – LLM errors
      Combined chart: total XML errors (bars) and final Validator issues
      (line) vs max_llm_iterations

Usage
-----
  python Fitness_graph_analyzer.py                   # auto-detect latest session
  python Fitness_graph_analyzer.py <session_dir>     # specify session directory
  python Fitness_graph_analyzer.py <summary.csv>     # specify summary CSV directly

Configuration
-------------
  Edit the CONFIG section below or set variables in .env:
    PLOT_OUTPUT_FORMAT   "show" | "png" | "svg" | "pdf"
    PLOT_OUTPUT_DIR      directory where charts are saved
    PLOT_DPI             export resolution (default 150)
    EVAL_OUTPUT_DIR      root folder for evaluation sessions
"""

import sys
import os
import glob
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional

try:
    import pandas as pd
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    import numpy as np
    DEPS_OK = True
except ImportError as _e:
    print(f"[ERROR] Missing dependencies: {_e}")
    print("Install with:  pip install pandas matplotlib numpy")
    DEPS_OK = False

# =============================================================================
# ⚙️  CONFIG – edit here or via environment variables / .env
# =============================================================================

# "show"  → open an interactive window
# "png" / "svg" / "pdf" → save files to OUTPUT_DIR
OUTPUT_FORMAT = os.getenv("PLOT_OUTPUT_FORMAT", "show")

# Directory where charts are saved (ignored when OUTPUT_FORMAT="show")
OUTPUT_DIR = os.getenv("PLOT_OUTPUT_DIR", "evaluation_results/plots")

# Root folder for evaluation sessions
RESULTS_BASE = os.getenv("EVAL_OUTPUT_DIR", "evaluation_results")

# Export resolution (DPI)
EXPORT_DPI = int(os.getenv("PLOT_DPI", "150"))

# =============================================================================


# ---------------------------------------------------------------------------
# Utility – CSV search
# ---------------------------------------------------------------------------

def _find_latest_session_csv(results_base):
    pattern_summary = os.path.join(results_base, "session_*", "sweep_iterations_results.csv")
    pattern_detail  = os.path.join(results_base, "session_*", "sweep_llm_iterations_detail.csv")

    summary_files = sorted(glob.glob(pattern_summary))
    detail_files  = sorted(glob.glob(pattern_detail))

    return (summary_files[-1] if summary_files else None,
            detail_files[-1]  if detail_files  else None)


def _resolve_paths(argv):
    if len(argv) < 2:
        summary, detail = _find_latest_session_csv(RESULTS_BASE)
        if not summary:
            raise FileNotFoundError(
                f"No CSV found in '{RESULTS_BASE}'. "
                "Run evaluation_script.py in sweep mode first."
            )
        return summary, detail

    arg = argv[1]

    if os.path.isdir(arg):
        summary = os.path.join(arg, "sweep_iterations_results.csv")
        detail  = os.path.join(arg, "sweep_llm_iterations_detail.csv")
        if not os.path.exists(summary):
            raise FileNotFoundError(f"CSV not found in: {arg}")
        return summary, detail if os.path.exists(detail) else None

    if os.path.isfile(arg):
        detail_candidate = os.path.join(os.path.dirname(arg), "sweep_llm_iterations_detail.csv")
        return arg, detail_candidate if os.path.exists(detail_candidate) else None

    raise FileNotFoundError(f"Invalid path: {arg}")


# ---------------------------------------------------------------------------
# Data loading and cleaning
# ---------------------------------------------------------------------------

def load_summary(csv_path):
    df = pd.read_csv(csv_path)
    df = df.sort_values("max_llm_iterations").reset_index(drop=True)

    numeric_cols = [
        "generation_time_s", "normalized_ged", "ged_raw", "ged_similarity",
        "behavioral_similarity", "fitness_orig_self", "fitness_mit_self",
        "fitness_mit_on_orig_log", "fitness_orig_on_mit_log",
        "llm_actual_iterations", "llm_final_issues_count",
        "llm_xml_errors_count", "llm_valid_iter_count"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    bool_cols = ["generation_success", "llm_final_xml_valid", "llm_any_xml_error"]
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].map({"True": True, "False": False,
                                   True: True, False: False})
    return df


def load_detail(csv_path):
    df = pd.read_csv(csv_path)
    df = df.sort_values(["max_llm_iterations", "llm_sub_iteration"]).reset_index(drop=True)

    for col in ["max_llm_iterations", "llm_sub_iteration", "issues_count"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ["xml_valid", "validator_passed"]:
        if col in df.columns:
            df[col] = df[col].map({"True": True, "False": False,
                                   True: True, False: False})
    return df


# ---------------------------------------------------------------------------
# Shared style
# ---------------------------------------------------------------------------

COLORS = {
    "time":         "#1565C0",
    "ged":          "#C62828",
    "fitness":      "#2E7D32",
    "errors_xml":   "#EF6C00",
    "errors_valid": "#6A1B9A",
    "errors_line":  "#1565C0",
    "grid":         "#E0E0E0",
}

LW   = 2.2
MS   = 7
FONT = 11


def _style_ax(ax, xlabel="Maximum number of LLM iterations", ylabel=""):
    ax.set_xlabel(xlabel, fontsize=FONT)
    ax.set_ylabel(ylabel, fontsize=FONT)
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.grid(True, color=COLORS["grid"], linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


# ---------------------------------------------------------------------------
# Figure 1 – Execution time
# ---------------------------------------------------------------------------

def plot_execution_time(df, ax):
    col = "generation_time_s"
    ax.set_title("Execution time per configuration",
                 fontsize=13, fontweight="bold")

    if col not in df.columns or df[col].isna().all():
        ax.text(0.5, 0.5, "Data not available", ha="center", va="center",
                transform=ax.transAxes, fontsize=12, color="gray")
        return

    x = df["max_llm_iterations"]
    y = df[col]

    ax.plot(x, y, color=COLORS["time"], marker="o", lw=LW, ms=MS, zorder=3)
    ax.fill_between(x, y, alpha=0.10, color=COLORS["time"])

    for xi, yi in zip(x, y):
        if pd.notna(yi):
            ax.annotate(f"{yi:.1f}s", xy=(xi, yi),
                        xytext=(0, 9), textcoords="offset points",
                        ha="center", fontsize=9, color=COLORS["time"])

    _style_ax(ax, ylabel="Seconds")


# ---------------------------------------------------------------------------
# Figure 2 – RGED and Cross-Fitness
# ---------------------------------------------------------------------------

def plot_quality_metrics(df, ax):
    ax.set_title("RGED and Cross-Fitness vs number of iterations",
                 fontsize=13, fontweight="bold")

    has_ged     = ("normalized_ged" in df.columns
                   and not df["normalized_ged"].isna().all())
    has_fitness = ("behavioral_similarity" in df.columns
                   and not df["behavioral_similarity"].isna().all())

    if not has_ged and not has_fitness:
        ax.text(0.5, 0.5,
                "GED / Fitness data not available\n(pm4py required)",
                ha="center", va="center", transform=ax.transAxes,
                fontsize=12, color="gray")
        return

    x = df["max_llm_iterations"]
    handles = []

    # ── RGED (left axis) ────────────────────────────────────────────────────
    if has_ged:
        l1, = ax.plot(x, df["normalized_ged"],
                      color=COLORS["ged"], marker="o", lw=LW, ms=MS,
                      label="RGED (normalised) ↓", zorder=3)
        ax.fill_between(x, df["normalized_ged"], alpha=0.08, color=COLORS["ged"])
        handles.append(l1)
        _style_ax(ax, ylabel="Normalised RGED (0–1)")

    # ── Cross-Fitness (right axis or same axis) ─────────────────────────────
    if has_fitness:
        target = ax.twinx() if has_ged else ax
        if has_ged:
            target.spines["top"].set_visible(False)
            target.set_ylabel("Cross-Fitness (0–1)",
                               fontsize=FONT, color=COLORS["fitness"])
            target.tick_params(axis="y", labelcolor=COLORS["fitness"])

        l2, = target.plot(x, df["behavioral_similarity"],
                          color=COLORS["fitness"], marker="s", lw=LW, ms=MS,
                          linestyle="--", label="Cross-Fitness ↑", zorder=3)
        target.fill_between(x, df["behavioral_similarity"],
                             alpha=0.08, color=COLORS["fitness"])
        handles.append(l2)

        if not has_ged:
            _style_ax(ax, ylabel="Cross-Fitness (0–1)")

    ax.legend(handles, [h.get_label() for h in handles],
              loc="best", fontsize=9, framealpha=0.85)


# ---------------------------------------------------------------------------
# Figure 3 – LLM Errors
# ---------------------------------------------------------------------------

def plot_error_metrics(df, df_detail, ax):
    ax.set_title("LLM errors as a function of iteration count",
                 fontsize=13, fontweight="bold")

    x_vals  = df["max_llm_iterations"].values
    xpos    = np.arange(len(x_vals))
    width   = 0.30
    handles = []

    # ── Bars: XML errors per max_llm_iterations ─────────────────────────────
    xml_col = "llm_xml_errors_count"
    if xml_col in df.columns and not df[xml_col].isna().all():
        b1 = ax.bar(xpos - width, df[xml_col].fillna(0),
                    width=width, color=COLORS["errors_xml"], alpha=0.82,
                    label="XML errors (sub-iter.)", zorder=3)
        handles.append(b1)

    # ── Bars: Validator issues in the last iteration ───────────────────────
    iss_col = "llm_final_issues_count"
    if iss_col in df.columns and not df[iss_col].isna().all():
        b2 = ax.bar(xpos, df[iss_col].fillna(0),
                    width=width, color=COLORS["errors_valid"], alpha=0.65,
                    label="Validator issues (last iter.)", zorder=3)
        handles.append(b2)

    # ── Line: invalid XML from detail CSV ────────────────────────────────────
    if df_detail is not None and "xml_valid" in df_detail.columns:
        invalid_by_n = (
            df_detail[df_detail["xml_valid"] == False]
            .groupby("max_llm_iterations")
            .size()
            .reindex(x_vals, fill_value=0)
        )
        ax2 = ax.twinx()
        ax2.spines["top"].set_visible(False)
        ax2.set_ylabel("Total invalid XML (detail)",
                       fontsize=FONT - 1, color=COLORS["errors_line"])
        ax2.tick_params(axis="y", labelcolor=COLORS["errors_line"])
        ax2.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
        l3, = ax2.plot(xpos, invalid_by_n.values,
                       color=COLORS["errors_line"], marker="^", lw=1.8,
                       ms=7, linestyle=":", zorder=4,
                       label="Invalid XML (detail)")
        handles.append(l3)

    if not handles:
        ax.text(0.5, 0.5, "Error data not available",
                ha="center", va="center", transform=ax.transAxes,
                fontsize=12, color="gray")
        return

    ax.set_xticks(xpos)
    ax.set_xticklabels([str(v) for v in x_vals])
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.grid(True, axis="y", color=COLORS["grid"], linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xlabel("Maximum number of LLM iterations", fontsize=FONT)
    ax.set_ylabel("Error count", fontsize=FONT)
    ax.legend(handles, [h.get_label() for h in handles],
              loc="upper left", fontsize=9, framealpha=0.85)


# ---------------------------------------------------------------------------
# Save / display
# ---------------------------------------------------------------------------

def _save_or_show(fig, name, fmt, out_dir):
    if fmt == "show":
        plt.show()
    else:
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        filepath = os.path.join(out_dir, f"{name}.{fmt}")
        fig.savefig(filepath, dpi=EXPORT_DPI, bbox_inches="tight")
        print(f"  ✓ Saved: {filepath}")
        plt.close(fig)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    if not DEPS_OK:
        sys.exit(1)

    try:
        summary_path, detail_path = _resolve_paths(sys.argv)
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    sep = "=" * 70
    print(f"\n{sep}")
    print("SWEEP ANALYZER – BPMN LLM Iteration Evaluation")
    print(sep)
    print(f"Summary CSV  : {summary_path}")
    print(f"Detail CSV   : {detail_path or '(not found)'}")
    print(f"Output format: {OUTPUT_FORMAT}")
    if OUTPUT_FORMAT != "show":
        print(f"Output dir   : {OUTPUT_DIR}")
    print(sep + "\n")

    df_summary = load_summary(summary_path)
    df_detail  = (load_detail(detail_path)
                  if detail_path and os.path.exists(detail_path)
                  else None)

    print(f"Summary rows : {len(df_summary)}")
    print(f"Detail rows  : {len(df_detail) if df_detail is not None else 0}")
    print(f"Iterations   : {sorted(df_summary['max_llm_iterations'].tolist())}\n")

    # ── Figure 1 – Execution time ─────────────────────────────────────────────
    fig1, ax1 = plt.subplots(figsize=(8, 5))
    plot_execution_time(df_summary, ax1)
    fig1.tight_layout()
    _save_or_show(fig1, "fig1_execution_time", OUTPUT_FORMAT, OUTPUT_DIR)

    # ── Figure 2 – RGED and Cross-Fitness ────────────────────────────────────
    fig2, ax2 = plt.subplots(figsize=(8, 5))
    plot_quality_metrics(df_summary, ax2)
    fig2.tight_layout()
    _save_or_show(fig2, "fig2_rged_fitness", OUTPUT_FORMAT, OUTPUT_DIR)

    # ── Figure 3 – LLM errors ────────────────────────────────────────────────
    fig3, ax3 = plt.subplots(figsize=(8, 5))
    plot_error_metrics(df_summary, df_detail, ax3)
    fig3.tight_layout()
    _save_or_show(fig3, "fig3_llm_errors", OUTPUT_FORMAT, OUTPUT_DIR)

    print("\n✓ Charts generated successfully.")


if __name__ == "__main__":
    main()
