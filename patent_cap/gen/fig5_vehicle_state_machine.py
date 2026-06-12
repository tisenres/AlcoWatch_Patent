"""Figure 5 — Vehicle-control safety state machine (2D line, ACN1408 CAP).

Pure 1-bit line art. Fail-safe: IGNITION_BLOCKED is the default/initial state.
States and transitions per CLAUDE.md "Arduino Safety Logic".
"""
import sys
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import patent_style as ps  # noqa: E402

OUT = HERE.parent / "figures"


def build():
    fig, ax = ps.new_sheet(9.5, 7.0)

    waiting = ps.box(ax, 8, 74, 24, 9, "WAITING_FOR_DATA", fontsize=8)
    blocked = ps.box(ax, 38, 48, 26, 11, "IGNITION_BLOCKED\n(default / fail-safe)",
                     ps.n("safety_logic"), fontsize=8)
    allowed = ps.box(ax, 70, 74, 24, 9, "IGNITION_ALLOWED", fontsize=8)
    connlost = ps.box(ax, 8, 14, 24, 9, "CONNECTION_LOST", fontsize=8)
    override = ps.box(ax, 70, 14, 24, 9, "OVERRIDE_ACTIVE", ps.n("override"), fontsize=8)

    # initial state marker -> default BLOCKED (fail-safe)
    ax.plot([51], [92], marker="o", color="black", markersize=5, antialiased=False)
    ps.arrow(ax, (51, 91), blocked["t"])
    ps.label(ax, 53, 86, "power-on (default BLOCK)", ha="left", fontsize=7)

    # WAITING_FOR_DATA -> BLOCKED
    ps.arrow(ax, waiting["b"], blocked["l"])
    ps.label(ax, 30, 65, "init", fontsize=7)

    # BLOCKED -> ALLOWED (allow conditions) : up on the left side
    ps.arrow(ax, blocked["t"], allowed["l"])
    ps.label(ax, 57, 71, "BAC<0.08 &\nworn & recent", fontsize=7)

    # ALLOWED -> BLOCKED (revoke) : down on the right side
    ps.arrow(ax, allowed["b"], blocked["r"])
    ps.label(ax, 76, 61, "BAC>=0.08 /\nremoved / stale", fontsize=7)

    # BLOCKED -> CONNECTION_LOST (timeout)
    ps.arrow(ax, blocked["l"], connlost["t"])
    ps.label(ax, 25, 40, "60 s timeout", fontsize=7)

    # CONNECTION_LOST -> BLOCKED (reconnect)
    ps.arrow(ax, connlost["r"], blocked["b"])
    ps.label(ax, 43, 31, "reconnect", fontsize=7)

    # BLOCKED -> OVERRIDE_ACTIVE (5 s hold)
    ps.arrow(ax, blocked["b"], override["l"])
    ps.label(ax, 60, 33, "5 s hold", fontsize=7)

    # OVERRIDE_ACTIVE -> BLOCKED (after 5 min, logged)
    ps.arrow(ax, override["t"], blocked["b"])
    ps.label(ax, 74, 36, "5 min,\nlogged ->\nre-block", fontsize=7)

    ps.label(ax, 50, 3,
             "Required for ALLOW: active BLE + recent BAC update + BAC<0.08 + watch worn",
             fontsize=7)
    ps.save(fig, "fig5_vehicle_state_machine", outdir=OUT)


if __name__ == "__main__":
    build()
    print("wrote fig5_vehicle_state_machine")
