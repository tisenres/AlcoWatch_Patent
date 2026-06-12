"""Figure 4 — BiLSTM + Attention model architecture (2D line, ACN1408 CAP).

Pure 1-bit line art, faithful to ml_model/training/bac_estimation_model.py. The
network ends at the Dense head; climate calibration (132) is NOT shown here (it is a
post-inference correction — see Figure 3).
"""
import sys
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import patent_style as ps  # noqa: E402

OUT = HERE.parent / "figures"


def build():
    fig, ax = ps.new_sheet(8.0, 9.5)

    # --- Main column ---
    inp = ps.box(ax, 30, 90, 34, 7, "Input  [B, 10, 6]", ps.n("features"))
    bil = ps.box(ax, 30, 79, 34, 8, "Bidirectional LSTM (64)\n-> [B, 10, 128]", ps.n("bilstm"))
    drop1 = ps.box(ax, 33, 71, 28, 6, "Dropout (0.3)")
    ctx = ps.box(ax, 30, 49, 34, 8, "Attention context\n[B, 128]")
    d32 = ps.box(ax, 33, 39, 28, 7, "Dense (32), ReLU", ps.n("dense_head"))
    drop2 = ps.box(ax, 33, 31, 28, 6, "Dropout (0.3)")
    d16 = ps.box(ax, 33, 23, 28, 7, "Dense (16), ReLU")
    out = ps.box(ax, 30, 13, 34, 7, "Dense (1), linear\n-> BAC (g/dL)", ps.n("ignition") if False else None)
    ps.label(ax, 47, 10, "BAC output", fontsize=7.5)

    ps.arrow(ax, inp["b"], bil["t"])
    ps.arrow(ax, bil["b"], drop1["t"])
    ps.arrow(ax, ctx["b"], d32["t"])
    ps.arrow(ax, d32["b"], drop2["t"])
    ps.arrow(ax, drop2["b"], d16["t"])
    ps.arrow(ax, d16["b"], out["t"])

    # --- Attention branch (distinct, to the right) ---
    # dashed grouping box for the attention sub-path (128)
    ax.add_patch(__import__("matplotlib").patches.Rectangle(
        (70, 57), 28, 22, fill=False, edgecolor="black", linewidth=0.8,
        antialiased=False, linestyle="--"))
    ps.label(ax, 84, 81.5, "Temporal attention", fontsize=7.5)
    ps.label(ax, 66, 80, str(ps.n("attention")), fontsize=8)
    ad = ps.box(ax, 72, 71, 24, 6, "Dense (1), tanh", fontsize=7.5)
    sm = ps.box(ax, 72, 64, 24, 6, "Softmax  [B, 10]", fontsize=7.5)
    su = ps.box(ax, 72, 58, 24, 5, "Weighted sum\n(over timesteps)", fontsize=7)

    # branch in from dropout, out to context
    ps.arrow(ax, drop1["r"], ad["l"])
    ps.arrow(ax, ad["b"], sm["t"])
    ps.arrow(ax, sm["b"], su["t"])
    ps.arrow(ax, (su["l"][0], su["c"][1]), (ctx["r"][0], ctx["c"][1]))
    # also the value path: dropout -> weighted sum (the (x) multiply)
    ps.label(ax, 67, 62, "x", fontsize=10)

    ps.save(fig, "fig4_model_architecture", outdir=OUT)


if __name__ == "__main__":
    build()
    print("wrote fig4_model_architecture")
