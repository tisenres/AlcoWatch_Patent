"""Figure 1 — System architecture (2D line, ACN1408 CAP).

Compliant redraw of the photo-based provisional Figure 1. Pure black line art; no
photographs; no stale '22 KB' / 'AES-256 (as implemented)' labels (the BLE link is
labelled 'secure ... AES-256 per spec'). No biometric-authentication block (not in
the embodiment — see provisional_reconciliation.md).
"""
import sys
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import patent_style as ps  # noqa: E402

OUT = HERE.parent / "figures"


def build():
    fig, ax = ps.new_sheet(9.5, 6.2)

    ps.label(ax, 50, 99,
             "AI-based alcohol detection & vehicle ignition prevention system (%d)"
             % ps.n("system"), fontsize=8.5)

    # --- Wearable smartwatch (110) ---
    ps.box(ax, 2, 46, 34, 46, "", ps.n("smartwatch"))
    ps.label(ax, 19, 88, "Wearable smartwatch", fontsize=8.5)
    ppg = ps.box(ax, 4, 74, 14, 8, "PPG sensor", ps.n("ppg"))
    eda = ps.box(ax, 4, 63, 14, 8, "EDA\n(estimated)", ps.n("eda"))
    tmp = ps.box(ax, 4, 52, 14, 8, "Skin/ambient\ntemp.", ps.n("temp"))
    ai = ps.box(ax, 21, 58, 13, 20, "AI module\n(on-device\nBAC\nestimation)",
                ps.n("ai_module"))
    ps.label(ax, 27.5, 50, "on-device inference (%d)" % ps.n("ondevice"), fontsize=7)
    for s in (ppg, eda, tmp):
        ps.arrow(ax, s["r"], (ai["l"][0], s["c"][1]))

    # --- Secure BLE link (140) ---
    ps.arrow(ax, ai["r"], (54, ai["c"][1]))
    ps.label(ax, 45, 76, "Secure BLE link\n(AES-256 per spec)", fontsize=7.5)
    ps.label(ax, 45, 70, str(ps.n("ble")), fontsize=8, )

    # --- Vehicle control module (150) ---
    ps.box(ax, 54, 46, 22, 46, "", ps.n("vehicle_ctrl"))
    ps.label(ax, 65, 88, "Vehicle control module", fontsize=8.5)
    rx = ps.box(ax, 56, 74, 18, 8, "BLE receiver", ps.n("ble_rx"))
    logic = ps.box(ax, 56, 60, 18, 10, "Safety logic\n(fail-safe,\ndefault BLOCK)",
                   ps.n("safety_logic"))
    relay = ps.box(ax, 56, 46, 18, 8, "Relay /\nMOSFET switch", ps.n("relay"))
    ps.arrow(ax, rx["b"], logic["t"])
    ps.arrow(ax, logic["b"], relay["t"])

    # --- Right column (aligned to inner rows): indicators (170), override (180), ignition (160) ---
    indic = ps.box(ax, 80, 74, 17, 8, "LED /\nbuzzer", ps.n("indicators"))
    override = ps.box(ax, 80, 60, 17, 8, "Override\nbutton", ps.n("override"))
    ignition = ps.box(ax, 80, 46, 17, 8, "Ignition /\nOBD-II / ECU", ps.n("ignition"))
    ps.arrow(ax, override["l"], logic["r"])      # override is an input to the logic
    ps.arrow(ax, logic["t"], indic["b"])         # status indication out
    ps.arrow(ax, relay["r"], ignition["l"])      # ignition enable/disable

    ps.save(fig, "fig1_system_architecture", outdir=OUT)


if __name__ == "__main__":
    build()
    print("wrote fig1_system_architecture")
