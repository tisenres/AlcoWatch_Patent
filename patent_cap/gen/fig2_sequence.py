"""Figure 2 — Sequence diagram of system operation (2D line, ACN1408 CAP).

Full redraw (the provisional Figure 2 is a colour raster). Pure 1-bit line art.
Lifelines: smartwatch sensors (110), AI/BAC module (120), secure BLE link (140),
vehicle module (150).
"""
import sys
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import patent_style as ps  # noqa: E402

OUT = HERE.parent / "figures"

ACTORS = [
    (13, "Smartwatch\nsensors", "smartwatch"),
    (38, "AI / BAC\nmodule", "ai_module"),
    (62, "Secure BLE\nlink", "ble"),
    (87, "Vehicle\nmodule", "vehicle_ctrl"),
]


def lifeline(ax, x, y_top, y_bot):
    ax.plot([x, x], [y_bot, y_top], color="black", linewidth=0.7,
            antialiased=False, linestyle=(0, (4, 3)))


def msg(ax, x0, x1, y, text, dashed=False):
    style = "-|>" if not dashed else "-|>"
    from matplotlib.patches import FancyArrowPatch
    ax.add_patch(FancyArrowPatch((x0, y), (x1, y), arrowstyle=style,
                 mutation_scale=10, linewidth=1.0, color="black",
                 antialiased=False,
                 linestyle="--" if dashed else "-", shrinkA=0, shrinkB=0))
    ax.text((x0 + x1) / 2, y + 1.4, text, ha="center", va="bottom", fontsize=7.5,
            color="black")


def selfmsg(ax, x, y, text):
    ax.text(x + 2, y, text, ha="left", va="center", fontsize=7.5, color="black")
    ax.plot([x, x + 1.2], [y, y], color="black", linewidth=1.0, antialiased=False)


def build():
    fig, ax = ps.new_sheet(9.5, 6.4)
    xs = {}
    for x, lbl, key in ACTORS:
        ps.box(ax, x - 9, 90, 18, 8, lbl, ps.n(key), fontsize=8)
        xs[key] = x
        lifeline(ax, x, 90, 6)

    s, a, b, v = xs["smartwatch"], xs["ai_module"], xs["ble"], xs["vehicle_ctrl"]
    msg(ax, s, a, 82, "1. Continuous sensor data")
    selfmsg(ax, a, 75, "2. Estimate BAC; compare to 0.08 g/dL")
    msg(ax, a, b, 68, "3. BAC status packet (30 s)")
    msg(ax, b, v, 61, "4. Deliver status")
    selfmsg(ax, v, 54, "5. Block ignition (default fail-safe)")
    msg(ax, v, b, 47, "6. Override attempt", dashed=True)
    msg(ax, b, a, 40, "7. Request verification")
    msg(ax, a, s, 33, "8. Request BAC recheck")
    msg(ax, s, a, 26, "9. Fresh sensor data")
    msg(ax, a, v, 17, "10. Maintain ignition block")

    ps.label(ax, 50, 8,
             "Key: real-time monitoring | threshold-based block | verification | "
             "override protection", fontsize=7)
    ps.save(fig, "fig2_sequence", outdir=OUT)


if __name__ == "__main__":
    build()
    print("wrote fig2_sequence")
