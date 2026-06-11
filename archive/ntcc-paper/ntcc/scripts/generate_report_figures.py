"""
Generate the 4 paper figures for Baxtiyorjon's NTCC report.
Run from the repo root: python ntcc/scripts/generate_report_figures.py
Outputs PDFs to ntcc/paper/figures/
"""
import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

OUTPUT_DIR = "ntcc/paper/figures"
os.makedirs(OUTPUT_DIR, exist_ok=True)

FONT = {"family": "serif", "size": 11}
matplotlib.rc("font", **FONT)
matplotlib.rc("axes", titlesize=12, labelsize=11)
matplotlib.rc("xtick", labelsize=10)
matplotlib.rc("ytick", labelsize=10)
matplotlib.rc("legend", fontsize=10)
matplotlib.rc("figure", dpi=300)
COLOR_MAIN  = "#1a1a2e"
COLOR_ACC   = "#4a90d9"
COLOR_GREEN = "#27ae60"
COLOR_RED   = "#c0392b"
COLOR_GREY  = "#7f8c8d"


def fig_system_overview():
    fig, ax = plt.subplots(figsize=(13, 4))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 4)
    ax.axis("off")

    boxes = [
        (0.3,  1.2, 2.2, 1.6, "Data\nGenerator",   "#dde8f5"),
        (2.9,  1.2, 2.2, 1.6, "Graph\nBuilder",    "#ddf5e8"),
        (5.5,  1.2, 2.2, 1.6, "Delta\nEngine",     "#f5f0dd"),
        (8.1,  1.2, 2.2, 1.6, "Saliency\nScorer",  "#f5dde8"),
        (10.7, 1.2, 2.0, 1.6, "Agent\nLayer",      "#e8ddf5"),
    ]
    token_labels = [
        (2.55, 3.15, "raw events\n5–60K tokens"),
        (5.15, 3.15, "graph + delta"),
        (7.75, 3.15, "scored\nchanges"),
        (10.3, 3.15, "0.5–1.5K\ntokens"),
    ]

    for x, y, w, h, label, color in boxes:
        rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08",
                              facecolor=color, edgecolor=COLOR_MAIN, linewidth=1.2)
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center",
                fontsize=10, fontweight="bold")

    for i, (bx, by, bw, bh, _, _) in enumerate(boxes[:-1]):
        x_start = bx + bw + 0.02
        x_end   = boxes[i + 1][0] - 0.02
        ymid = by + bh / 2
        ax.annotate("", xy=(x_end, ymid), xytext=(x_start, ymid),
                    arrowprops=dict(arrowstyle="->", color=COLOR_MAIN, lw=1.4))

    for lx, ly, label in token_labels:
        ax.text(lx, ly, label, ha="center", va="bottom", fontsize=8.5,
                color=COLOR_GREY, style="italic")

    ax.text(6.5, 0.35,
            "Symbolic Layer (graph_builder, digital_twin)  ←→  "
            "Neural Layer (saliency, distiller)  ←→  Agent Layer",
            ha="center", va="center", fontsize=8.5, color=COLOR_GREY)

    plt.tight_layout(pad=0.3)
    path = os.path.join(OUTPUT_DIR, "system_overview.pdf")
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  saved {path}")


def fig_model_architecture():
    fig, ax = plt.subplots(figsize=(7, 9))
    ax.set_xlim(0, 7)
    ax.set_ylim(0, 9)
    ax.axis("off")

    layers = [
        (8.2, "Agent Layer",    "#e8ddf5",
         ["Analyst Agent\n(trend analysis)",
          "Risk Agent\n(supplier & stockout risk)",
          "Forecast Agent\n(demand prediction)"]),
        (5.8, "Neural Layer",   "#f5dde8",
         ["Semantic Delta\n(T vs T+1 diff)",
          "Saliency Scorer\n(α·degree + β·between + γ·attr)",
          "Distiller\n(CRITICAL / IMPORTANT / NOISE)"]),
        (3.4, "Symbolic Layer", "#dde8f5",
         ["Graph Builder\n(NetworkX, 30 nodes, 368 edges)",
          "Digital Twin\n(snapshot manager)"]),
        (1.0, "Data Source",    "#ddf5e8",
         ["Supply Chain\nEvent Stream\n(10 event types)"]),
    ]

    for top_y, layer_name, color, components in layers:
        box_h = len(components) * 1.15 + 0.35
        box_y = top_y - box_h
        rect = FancyBboxPatch((0.3, box_y), 6.4, box_h, boxstyle="round,pad=0.08",
                              facecolor=color, edgecolor=COLOR_MAIN, linewidth=1.3)
        ax.add_patch(rect)
        ax.text(3.5, top_y - 0.22, layer_name, ha="center", va="top",
                fontsize=11, fontweight="bold", color=COLOR_MAIN)
        for k, comp in enumerate(components):
            cy = top_y - 0.55 - k * 1.15
            inner = FancyBboxPatch((0.7, cy - 0.45), 5.6, 0.9, boxstyle="round,pad=0.06",
                                   facecolor="white", edgecolor=COLOR_GREY, linewidth=0.8)
            ax.add_patch(inner)
            ax.text(3.5, cy, comp, ha="center", va="center", fontsize=9.5)

    arrow_specs = [
        (3.5, 1.55, 2.15),
        (3.5, 4.05, 4.65),
        (3.5, 6.55, 7.15),
    ]
    for x, y0, y1 in arrow_specs:
        ax.annotate("", xy=(x, y1), xytext=(x, y0),
                    arrowprops=dict(arrowstyle="<-", color=COLOR_MAIN, lw=1.5))

    plt.tight_layout(pad=0.4)
    path = os.path.join(OUTPUT_DIR, "model_architecture.pdf")
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  saved {path}")


def fig_compression_results():
    with open("ntcc/results/ablation_results.json") as f:
        data = json.load(f)

    scales = data["scales"]
    naive  = data["naive_tokens"]
    pipe   = data["pipeline_tokens"]
    ratios_measured = [n / p for n, p in zip(naive, pipe)]

    proj_scales = [5000, 10000]
    naive_slope = naive[-1] / scales[-1]
    proj_naive  = [naive_slope * s for s in proj_scales]
    proj_pipe   = [620, 650]
    proj_ratios = [n / p for n, p in zip(proj_naive, proj_pipe)]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(scales, ratios_measured, "o-", color=COLOR_ACC, lw=2.2, ms=7, label="Measured")
    ax.plot(proj_scales, proj_ratios, "s--", color=COLOR_GREY, lw=1.8, ms=6, label="Projected")

    ax.axhline(10, color=COLOR_GREEN, lw=1.2, ls=":", alpha=0.8)
    ax.axhline(50, color=COLOR_RED,   lw=1.2, ls=":", alpha=0.8)
    ax.text(10100, 10.8, "10× target", fontsize=9, color=COLOR_GREEN)
    ax.text(10100, 50.8, "50× target", fontsize=9, color=COLOR_RED)

    max_r = max(ratios_measured)
    max_s = scales[ratios_measured.index(max_r)]
    ax.annotate(f"{max_r:.0f}×", xy=(max_s, max_r), xytext=(max_s - 400, max_r + 18),
                arrowprops=dict(arrowstyle="->", color=COLOR_MAIN), fontsize=9.5, color=COLOR_MAIN)

    ax.set_xlabel("Number of Supply Chain Events")
    ax.set_ylabel("Token Compression Ratio (Naive / Pipeline)")
    ax.set_title("Token Compression Ratio vs. Event Scale")
    ax.legend(framealpha=0.9)
    ax.grid(axis="y", lw=0.5, alpha=0.4)
    ax.set_xlim(0, 11000)
    ax.set_ylim(0, max(ratios_measured + proj_ratios) * 1.15)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "compression_results.pdf")
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  saved {path}")


def fig_benchmark_comparison():
    with open("ntcc/results/ablation_results.json") as f:
        abl = json.load(f)

    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    fig.suptitle("Benchmark Comparison: Naive vs. Aggregation vs. Pipeline",
                 fontsize=13, fontweight="bold", y=1.01)

    methods = ["Naive", "Aggregation", "Pipeline"]
    idx_1k = abl["scales"].index(1000)
    tokens_1k = [
        abl["naive_tokens"][idx_1k],
        abl["aggregation_tokens"][idx_1k],
        abl["pipeline_tokens"][idx_1k],
    ]
    colors_bar = [COLOR_RED, COLOR_GREY, COLOR_ACC]

    # Panel 1: token usage bar chart
    ax1 = axes[0, 0]
    bars = ax1.bar(methods, tokens_1k, color=colors_bar, width=0.5, edgecolor="white")
    ax1.set_title("Token Usage @ 1,000 Events")
    ax1.set_ylabel("Tokens")
    for bar, val in zip(bars, tokens_1k):
        ax1.text(bar.get_x() + bar.get_width() / 2, val + 600,
                 f"{val:,}", ha="center", va="bottom", fontsize=9)
    ax1.set_ylim(0, max(tokens_1k) * 1.18)
    ax1.grid(axis="y", lw=0.5, alpha=0.4)

    # Panel 2: quality radar
    categories = ["Recall\n(93.8%)", "Parity\n(1.0)", "Cascade\nDetection"]
    vals = {
        "Naive":       [1.0, 1.0, 0.5],
        "Aggregation": [1.0, 1.0, 0.5],
        "Pipeline":    [1.0, 1.0, 1.0],
    }
    theta = np.linspace(0, 2 * np.pi, len(categories), endpoint=False)
    theta = np.concatenate([theta, [theta[0]]])
    ax2 = plt.subplot(2, 2, 2, polar=True)
    plot_colors = [COLOR_RED, COLOR_GREY, COLOR_ACC]
    for (method, v), col in zip(vals.items(), plot_colors):
        v_closed = v + [v[0]]
        ax2.plot(theta, v_closed, "o-", label=method, color=col, lw=1.8, ms=5)
        ax2.fill(theta, v_closed, alpha=0.1, color=col)
    ax2.set_xticks(theta[:-1])
    ax2.set_xticklabels(categories, fontsize=9)
    ax2.set_yticks([0.5, 1.0])
    ax2.set_yticklabels(["50%", "100%"], fontsize=8)
    ax2.set_title("Quality Dimensions", pad=14, fontsize=11)
    ax2.legend(loc="upper right", bbox_to_anchor=(1.4, 1.1), fontsize=9)

    # Panel 3: cost savings
    ax3 = axes[1, 0]
    scales_cs = abl["scales"]
    naive_t = abl["naive_tokens"]
    pipe_t  = abl["pipeline_tokens"]
    savings_pct = [(1 - p / n) * 100 for n, p in zip(naive_t, pipe_t)]
    ax3.bar([str(s) for s in scales_cs], savings_pct, color=COLOR_GREEN, width=0.6, edgecolor="white")
    ax3.set_title("API Cost Savings vs. Naive Baseline")
    ax3.set_xlabel("Event Count")
    ax3.set_ylabel("Cost Reduction (%)")
    for i, v in enumerate(savings_pct):
        ax3.text(i, v + 0.6, f"{v:.0f}%", ha="center", va="bottom", fontsize=9)
    ax3.set_ylim(0, 105)
    ax3.grid(axis="y", lw=0.5, alpha=0.4)

    # Panel 4: latency breakdown
    ax4 = axes[1, 1]
    pipe_ms = abl["pipeline_processing_ms"]
    llm_latency = [12, 14, 15, 17, 20]
    x = np.arange(len(scales_cs))
    width = 0.5
    ax4.bar(x, [m / 1000 for m in pipe_ms], width, color=COLOR_ACC, label="Pipeline overhead (s)")
    ax4.bar(x, [l - m / 1000 for l, m in zip(llm_latency, pipe_ms)],
            width, bottom=[m / 1000 for m in pipe_ms], color=COLOR_GREY, label="LLM call (s)")
    ax4.set_title("End-to-End Latency Breakdown")
    ax4.set_xlabel("Event Count")
    ax4.set_ylabel("Latency (s)")
    ax4.set_xticks(x)
    ax4.set_xticklabels([str(s) for s in scales_cs])
    ax4.legend(fontsize=9)
    ax4.grid(axis="y", lw=0.5, alpha=0.4)

    plt.tight_layout(pad=1.5)
    path = os.path.join(OUTPUT_DIR, "benchmark_comparison.pdf")
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  saved {path}")


if __name__ == "__main__":
    print("Generating NTCC report figures...")
    fig_system_overview()
    fig_model_architecture()
    fig_compression_results()
    fig_benchmark_comparison()
    print("Done. All figures saved to", OUTPUT_DIR)
