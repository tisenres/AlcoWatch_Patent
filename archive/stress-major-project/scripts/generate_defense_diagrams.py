#!/usr/bin/env python3
"""Generate two extra defense-presentation diagrams that visualize what is
currently text-only on slide 11:

1. ble_protocol.png  — 12-byte GATT characteristic byte layout
2. cabin_fsm.png     — 5-state cabin finite-state machine

Run:
    python3 scripts/generate_defense_diagrams.py
Outputs (PNG @ 300 dpi):
    paper_figures/stress/ble_protocol.png
    paper_figures/stress/cabin_fsm.png
"""
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "paper_figures" / "stress"
OUT_DIR.mkdir(parents=True, exist_ok=True)

COL_TS = "#3B6FB5"   # timestamp — blue
COL_LV = "#D9534F"   # stress level — red
COL_CF = "#5CB85C"   # confidence — green
COL_RV = "#9E9E9E"   # reserved — gray
TEXT_DARK = "#1F2937"
TEXT_MUTED = "#475569"


# ============================================================================
# DIAGRAM 1 — BLE 12-byte Protocol Packet
# ============================================================================
def make_ble_protocol():
    fig, ax = plt.subplots(figsize=(14, 7.5), dpi=300)
    ax.set_xlim(-0.7, 12.7)
    ax.set_ylim(-5.0, 4.5)
    ax.set_aspect("equal")
    ax.axis("off")

    # Title
    ax.text(6, 4.0,
            "BLE GATT Characteristic — 12-byte Stress Packet",
            ha="center", va="center",
            fontsize=22, fontweight="bold", color=TEXT_DARK)
    ax.text(6, 3.35,
            "Notification every 30 s   |   "
            "Service ABCD1234-…   |   Characteristic ABCD1235-…",
            ha="center", va="center",
            fontsize=12, color=TEXT_MUTED, style="italic")

    # ---- Field bands (color-coded headers) ABOVE the byte cells ----
    fields = [
        (0, 8, "Timestamp",     "int64 little-endian\nms since epoch", COL_TS),
        (8, 1, "Stress\nLevel", "uint8\n0=Calm  1=Mild\n2=Moderate  3=Critical", COL_LV),
        (9, 1, "Confidence",    "uint8\n0–100 %", COL_CF),
        (10, 2, "Reserved",     "future use", COL_RV),
    ]

    cell_h = 1.2
    cell_y = 1.0
    band_y = cell_y + cell_h + 0.20
    band_h = 0.75

    for start, span, name, _, color in fields:
        rect = FancyBboxPatch((start + 0.05, band_y), span - 0.10, band_h,
                              boxstyle="round,pad=0.02,rounding_size=0.08",
                              linewidth=0, facecolor=color, alpha=0.95)
        ax.add_patch(rect)
        # Smaller font for narrow bands so the label fits
        fs = 12 if span >= 2 else 9
        ax.text(start + span / 2, band_y + band_h / 2, name,
                ha="center", va="center",
                fontsize=fs, fontweight="bold", color="white",
                linespacing=1.0)

    # ---- 12 byte cells ----
    for b in range(12):
        rect = FancyBboxPatch((b + 0.05, cell_y), 0.9, cell_h,
                              boxstyle="round,pad=0.02,rounding_size=0.05",
                              linewidth=1.2, edgecolor=TEXT_DARK,
                              facecolor="white")
        ax.add_patch(rect)
        ax.text(b + 0.5, cell_y + cell_h / 2, f"B{b}",
                ha="center", va="center",
                fontsize=11, fontweight="bold", color=TEXT_DARK)

    # ---- Description boxes BELOW the cells, each with a leader line ----
    # Place description boxes in a row below; each has fixed width and is
    # tied to its field with a vertical+slanted leader line.
    desc_boxes = [
        # (center_x, top_y, width, height, color, lines)
        (3.0,  -0.4, 5.6, 1.1, COL_TS,
         ["Timestamp (Bytes 0–7)", "int64 little-endian — ms since epoch"]),
        (8.5,  -0.4, 1.9, 1.1, COL_LV,
         ["Stress Level (B8)", "0 Calm  1 Mild  2 Mod  3 Crit"]),
        # Bottom row: Confidence (left, near B9) then Reserved (right, near B10-11)
        # — order matches anchor order so leader lines don't cross.
        (8.0,  -2.0, 1.9, 1.1, COL_CF,
         ["Confidence (B9)", "uint8 — 0–100 %"]),
        (11.0, -2.0, 2.4, 1.1, COL_RV,
         ["Reserved (B10–11)", "future use"]),
    ]

    # Anchor x for each leader (center of its byte range)
    anchors = [4, 8.5, 9.5, 11]  # Timestamp center, B8, B9, B10-11 center

    for (cx, top, w, h, color, lines), ax_anchor in zip(desc_boxes, anchors):
        x0, y0 = cx - w / 2, top - h
        rect = FancyBboxPatch((x0, y0), w, h,
                              boxstyle="round,pad=0.04,rounding_size=0.10",
                              linewidth=1.2, edgecolor=color,
                              facecolor="white")
        ax.add_patch(rect)
        ax.text(cx, top - 0.30, lines[0],
                ha="center", va="center",
                fontsize=11, fontweight="bold", color=color)
        ax.text(cx, top - 0.78, lines[1],
                ha="center", va="center",
                fontsize=10, color=TEXT_DARK)
        # Leader line: from byte cell bottom down to box top
        ax.plot([ax_anchor, cx], [cell_y - 0.05, top + 0.02],
                color=color, lw=1.4, zorder=0)

    # ---- Byte ruler ----
    rule_y = -3.55
    ax.annotate("", xy=(12, rule_y), xytext=(0, rule_y),
                arrowprops=dict(arrowstyle="<->", color=TEXT_MUTED, lw=1.2))
    ax.text(6, rule_y - 0.40, "12 bytes total",
            ha="center", va="top",
            fontsize=11, color=TEXT_MUTED, style="italic")

    plt.tight_layout()
    out = OUT_DIR / "ble_protocol.png"
    fig.savefig(out, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"  saved {out.relative_to(REPO_ROOT)}")
    plt.close(fig)


# ============================================================================
# DIAGRAM 2 — 5-state Cabin FSM
# ============================================================================
def make_cabin_fsm():
    fig, ax = plt.subplots(figsize=(14, 8), dpi=300)
    ax.set_xlim(-1.0, 14.0)
    ax.set_ylim(-0.5, 9.0)
    ax.set_aspect("equal")
    ax.axis("off")

    ax.text(6.5, 8.4,
            "Cabin Control Finite-State Machine",
            ha="center", va="center",
            fontsize=22, fontweight="bold", color=TEXT_DARK)
    ax.text(6.5, 7.75,
            "Input: BLE stress level (0–3) every 30 s   |   "
            "Failsafe: 60-s timeout → WAITING",
            ha="center", va="center",
            fontsize=12, color=TEXT_MUTED, style="italic")

    # Place WAITING separately (left, lower row), 4 active states top row
    R = 1.0
    states = {
        "WAITING":  (1.5,  3.0, "WAITING",  "yellow blink\nfan: 0%\naudio: off",
                     "#F4C430", "#3D2E00"),
        "CALM":     (3.5,  6.0, "CALM",     "warm white\nfan: 30%\naudio: off",
                     "#FFE7B5", "#5D3A00"),
        "MILD":     (6.0,  6.0, "MILD",     "neutral white\nfan: 50%\naudio: off",
                     "#E6E6E6", "#1F2937"),
        "MODERATE": (8.5,  6.0, "MODERATE", "blue\nfan: 75%\nsoft music",
                     "#5BA8E8", "white"),
        "CRITICAL": (11.0, 6.0, "CRITICAL", "red blink\nfan: 100%\nvoice alert",
                     "#E04848", "white"),
    }

    # Draw active progression arrows first (so circles overlay them cleanly)
    progression = ["CALM", "MILD", "MODERATE", "CRITICAL"]
    for a, b in zip(progression, progression[1:]):
        ax_, ay_ = states[a][:2]
        bx_, by_ = states[b][:2]
        arr = FancyArrowPatch((ax_ + R, ay_), (bx_ - R, by_),
                              arrowstyle="-|>", mutation_scale=20,
                              color="#1F2937", lw=2.0, zorder=1)
        ax.add_patch(arr)

    # Reverse de-escalation arrows (curved, below the progression line)
    for a, b in zip(progression[1:], progression[:-1]):
        ax_, ay_ = states[a][:2]
        bx_, by_ = states[b][:2]
        arr = FancyArrowPatch((ax_ - R + 0.10, ay_ - 0.25),
                              (bx_ + R - 0.10, by_ - 0.25),
                              arrowstyle="-|>", mutation_scale=15,
                              color="#9CA3AF", lw=1.4,
                              connectionstyle="arc3,rad=0.30", zorder=1)
        ax.add_patch(arr)

    # WAITING ↔ CALM transitions — wider spacing avoids text overlap
    wx, wy = states["WAITING"][:2]
    cx_, cy_ = states["CALM"][:2]

    # CALM → WAITING (timeout / packet loss)
    arr_loss = FancyArrowPatch((cx_ - 0.40, cy_ - R),
                               (wx + 0.15, wy + R - 0.05),
                               arrowstyle="-|>", mutation_scale=18,
                               color="#B45309", lw=1.6,
                               connectionstyle="arc3,rad=-0.30", zorder=1)
    ax.add_patch(arr_loss)
    ax.text(2.05, 4.85, "60-s timeout\nor packet loss",
            ha="right", va="center",
            fontsize=10, color="#B45309", style="italic", linespacing=1.2)

    # WAITING → CALM (first packet)
    arr_in = FancyArrowPatch((wx + 0.55, wy + R - 0.10),
                             (cx_ - 0.10, cy_ - R + 0.05),
                             arrowstyle="-|>", mutation_scale=18,
                             color="#1F7A1F", lw=1.6,
                             connectionstyle="arc3,rad=0.32", zorder=1)
    ax.add_patch(arr_in)
    ax.text(2.85, 4.30, "first packet",
            ha="left", va="center",
            fontsize=10, color="#1F7A1F", style="italic")

    # Boot → WAITING (entering from below)
    ax.annotate("Boot",
                xy=(wx, wy - R + 0.05),
                xytext=(wx, wy - R - 1.0),
                arrowprops=dict(arrowstyle="-|>", color="#B45309", lw=1.6),
                fontsize=11, color="#B45309", fontweight="bold",
                ha="center", va="center")

    # Draw state circles (after arrows so they're on top)
    for name, (cx, cy, label, sub, fill, txt) in states.items():
        circle = patches.Circle((cx, cy), R,
                                facecolor=fill, edgecolor=TEXT_DARK,
                                linewidth=2.0, zorder=2)
        ax.add_patch(circle)
        ax.text(cx, cy + 0.32, label,
                ha="center", va="center",
                fontsize=12.5, fontweight="bold", color=txt, zorder=3)
        ax.text(cx, cy - 0.30, sub,
                ha="center", va="center",
                fontsize=8.5, color=txt, zorder=3, linespacing=1.3)

    # Bottom legend strip
    ax.text(6.5, 1.55,
            "Stress Level: 0 = Calm  →  3 = Critical   "
            "(monotonic LED & fan intensity)",
            ha="center", va="center",
            fontsize=11, color=TEXT_MUTED, style="italic")

    # Forward / reverse legend chips
    leg_y = 0.65
    chips = [
        (4.0, "#1F2937", "stress increases"),
        (9.0, "#9CA3AF", "stress de-escalates"),
    ]
    for x_, c, lbl in chips:
        arr = FancyArrowPatch((x_ - 0.55, leg_y), (x_ - 0.10, leg_y),
                              arrowstyle="-|>", mutation_scale=15,
                              color=c, lw=2.0)
        ax.add_patch(arr)
        ax.text(x_, leg_y, lbl, va="center", ha="left",
                fontsize=11, color=TEXT_DARK)

    plt.tight_layout()
    out = OUT_DIR / "cabin_fsm.png"
    fig.savefig(out, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"  saved {out.relative_to(REPO_ROOT)}")
    plt.close(fig)


def main():
    print("Generating defense diagrams...")
    make_ble_protocol()
    make_cabin_fsm()
    print("Done.")


if __name__ == "__main__":
    main()
