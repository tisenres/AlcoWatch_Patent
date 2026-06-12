"""Figure 3 — AI framework / signal-processing pipeline (2D line, ACN1408 CAP).

Pure 1-bit line art. Climate-adaptive calibration (132) is drawn as a POST-inference
correction applied to the trained model's raw output, NOT as a network layer.
"""
import sys
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import patent_style as ps  # noqa: E402

OUT = HERE.parent / "figures"


def build():
    fig, ax = ps.new_sheet(7.5, 9.5)

    # Sensor acquisition row
    ppg = ps.box(ax, 8, 89, 18, 7, "PPG sensor", ps.n("ppg"), fontsize=7.5)
    eda = ps.box(ax, 41, 89, 18, 7, "EDA\n(estimated)", ps.n("eda"), fontsize=7.5)
    tmp = ps.box(ax, 74, 89, 18, 7, "Temp.\n(skin/ambient)", ps.n("temp"), fontsize=7.5)

    pre = ps.box(ax, 30, 76, 40, 8, "Preprocessing &\n10-timestep windowing", ps.n("preproc"))
    feat = ps.box(ax, 30, 64, 40, 8, "Feature tensor  [10 x 6]", ps.n("features"))
    model = ps.box(ax, 27, 50, 46, 10,
                   "BiLSTM + temporal attention\n(trained on-device model)",
                   ps.n("bilstm"))
    calib = ps.box(ax, 27, 35, 46, 9,
                   "Climate-adaptive calibration\n(POST-inference correction,\nnot a network layer)",
                   ps.n("calibration"), fontsize=7.5)
    dec = ps.box(ax, 27, 22, 46, 8,
                 "Decision logic:  BAC vs 0.08 g/dL", ps.n("safety_logic"))
    ble = ps.box(ax, 30, 12, 40, 7, "Secure BLE status packet", ps.n("ble"), fontsize=7.5)
    ign = ps.box(ax, 27, 2, 46, 7, "Vehicle ignition control", ps.n("ignition"), fontsize=7.5)

    for s in (ppg, eda, tmp):
        ps.arrow(ax, s["b"], (pre["c"][0] + (s["c"][0] - 50) * 0.3, pre["t"][1]))
    ps.arrow(ax, pre["b"], feat["t"])
    ps.arrow(ax, feat["b"], model["t"])
    ps.arrow(ax, model["b"], calib["t"])
    ps.arrow(ax, calib["b"], dec["t"])
    ps.arrow(ax, dec["b"], ble["t"])
    ps.arrow(ax, ble["b"], ign["t"])
    # right-side flow annotations (kept clear of the boxes)
    ps.label(ax, 76, 54, "raw BAC", ha="left", fontsize=6.8)
    ps.label(ax, 76, 39.5, "calibrated\nBAC", ha="left", fontsize=6.8)
    ps.label(ax, 76, 26, "allow / block\n+ confidence", ha="left", fontsize=6.8)

    ps.save(fig, "fig3_ai_framework", outdir=OUT)


if __name__ == "__main__":
    build()
    print("wrote fig3_ai_framework")
