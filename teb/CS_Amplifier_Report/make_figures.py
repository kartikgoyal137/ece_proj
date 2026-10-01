#!/usr/bin/env python3
"""
Figure generation for the CS Amplifier laboratory report.

Two jobs:
  (1) Crop the raw Cadence Virtuoso screen captures down to the plot/schematic
      canvas and give them meaningful filenames.
  (2) Reconstruct the phase-frequency and transient responses that were not
      captured during the lab session, using ONLY the measured anchors taken
      from the supplied captures (mid-band gain, -3 dB frequency, quiescent
      operating point).  The reconstruction uses the dominant-pole small-signal
      model -- it is an analytical model, NOT simulator output, and every
      generated figure is stamped as such.

Run:  python3 make_figures.py
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator, NullFormatter
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
FIGDIR = os.path.join(HERE, "figures")
RAW = os.path.join(FIGDIR, "cadence")
os.makedirs(FIGDIR, exist_ok=True)

# --------------------------------------------------------------------------
# (1) Crop + rename the Cadence captures
# --------------------------------------------------------------------------
# All captures are 1599x899 full-desktop grabs.  Remove the GNOME top bar,
# the Virtuoso title bar and the icon toolbars from the top, and the status
# bar from the bottom, keeping the waveform/schematic canvas and the left
# navigator panel (which carries the cell name and device list).
# Waveform windows: drop the left trace-list panel but keep the axis labels.
CROP_PLOT = (118, 150, 1599, 866)
# Schematics: crop tightly around the drawn circuit, which sits in the middle
# of the canvas.  Boxes are per-image because each circuit is placed
# differently.
RENAME = [
    # (source basename,                              output name,           crop box)
    ("WhatsApp Image 2026-10-01 at 5.56.48 PM (2).jpeg", "sch_res.png",
     (590, 150, 1330, 850)),
    ("WhatsApp Image 2026-10-01 at 5.56.47 PM (2).jpeg", "sch_active.png",
     (460, 140, 1200, 840)),
    ("WhatsApp Image 2026-10-01 at 5.56.47 PM (1).jpeg", "sch_active_clean.png",
     (460, 140, 1200, 840)),
    ("WhatsApp Image 2026-10-01 at 5.56.46 PM.jpeg",     "sch_diode.png",
     (600, 190, 1340, 860)),
    ("WhatsApp Image 2026-10-01 at 5.56.47 PM.jpeg",     "ac_res.png",       CROP_PLOT),
    ("WhatsApp Image 2026-10-01 at 5.56.46 PM (2).jpeg", "ac_active.png",    CROP_PLOT),
    ("WhatsApp Image 2026-10-01 at 5.56.48 PM (1).jpeg", "ac_active_alt.png",CROP_PLOT),
    ("WhatsApp Image 2026-10-01 at 5.56.46 PM (1).jpeg", "ac_diode.png",     CROP_PLOT),
    ("WhatsApp Image 2026-10-01 at 5.56.48 PM.jpeg",     "dc_active.png",    CROP_PLOT),
]


def crop_captures():
    for src, dst, box in RENAME:
        p = os.path.join(RAW, src)
        if not os.path.exists(p):
            raise SystemExit("missing capture: %s" % p)
        Image.open(p).convert("RGB").crop(box).save(
            os.path.join(FIGDIR, dst), "PNG", optimize=True)
        print("  cropped -> figures/%s" % dst)


# The report embeds the ORIGINAL, UNCROPPED captures.  They are copied here
# under LaTeX-safe filenames (the originals carry spaces and parentheses,
# which \includegraphics cannot handle) with no other modification whatsoever
# -- same pixels, same dimensions.
ORIGDIR = os.path.join(FIGDIR, "original")


def copy_originals():
    os.makedirs(ORIGDIR, exist_ok=True)
    for src, dst, _ in RENAME:
        p = os.path.join(RAW, src)
        out = os.path.join(ORIGDIR, "orig_" + dst.replace(".png", ".jpg"))
        im = Image.open(p)
        im.save(out, "JPEG", quality=95, subsampling=0)
        print("  original -> figures/original/%s  (%dx%d, uncropped)"
              % (os.path.basename(out), im.size[0], im.size[1]))


# --------------------------------------------------------------------------
# (2) Measured anchors, read off the Cadence captures
# --------------------------------------------------------------------------
VDD = 1.8
CL = 50e-15

CONFIGS = [
    dict(key="res",    title="Resistive Load ($R_D = 3\\,\\mathrm{k}\\Omega$)",
         Av=7.1469, f3=1.03276e9,
         vin_dc=0.630, vout_dc=0.890971, vin_pp=0.020,
         colour="#ff3b30"),
    dict(key="active", title="PMOS Active Load",
         Av=17.0, f3=218.483e6,
         vin_dc=0.630, vout_dc=0.904820, vin_pp=0.020,
         colour="#ff3b30"),
    dict(key="diode",  title="PMOS Diode-Connected Load",
         Av=3.66, f3=1.89606e9,
         vin_dc=0.590, vout_dc=0.139890, vin_pp=0.010,
         colour="#ff3b30"),
]

FSIG = 10e6          # transient stimulus frequency, well inside every passband
NPER = 4             # periods displayed

STAMP = ("Analytical reconstruction - dominant-pole small-signal model\n"
         "anchored to measured $A_{v0}$ and $f_{-3\\,\\mathrm{dB}}$. Not a simulator capture.")


def cadence_axes(ax):
    """Dark waveform-viewer styling, visually consistent with the captures."""
    ax.set_facecolor("#000000")
    for s in ax.spines.values():
        s.set_color("#8a0f0f")
        s.set_linewidth(1.2)
    ax.tick_params(colors="#dddddd", which="both", labelsize=8,
                   direction="out", length=4)
    ax.grid(True, which="major", color="#555555", linestyle=":", linewidth=0.6)
    ax.grid(True, which="minor", color="#333333", linestyle=":", linewidth=0.4)
    for lab in (ax.xaxis.label, ax.yaxis.label):
        lab.set_color("#dddddd")
        lab.set_fontsize(9)


def stamp(fig, ax):
    ax.text(0.015, 0.035, STAMP, transform=ax.transAxes,
            fontsize=6.4, color="#9fe8ff", va="bottom", ha="left",
            bbox=dict(facecolor="#001018", edgecolor="#2d7f9d",
                      linewidth=0.7, boxstyle="round,pad=0.35", alpha=0.95))


def new_fig(header):
    fig = plt.figure(figsize=(7.2, 4.0), facecolor="#101010")
    ax = fig.add_axes([0.105, 0.145, 0.865, 0.745])
    cadence_axes(ax)
    fig.text(0.012, 0.955, header, color="#eeeeee", fontsize=9.5, va="center")
    return fig, ax


# ---------------------------- phase responses -----------------------------
def phase_plot(cfg):
    f = np.logspace(0, 10, 4000)
    x = f / cfg["f3"]
    # Inverting single-pole response: H(jf) = -Av0 / (1 + j f/f3)
    ph = -180.0 - np.degrees(np.arctan(x))

    fig, ax = new_fig("AC Response  -  Phase  -  CS Amplifier, %s"
                      % cfg["title"].split("(")[0].strip().replace("$", ""))
    ax.semilogx(f, ph, color=cfg["colour"], linewidth=1.5, zorder=3)

    ax.axvline(cfg["f3"], color="#ffffff", linestyle="--", linewidth=1.0,
               dashes=(6, 4), zorder=2)
    ax.axhline(-225.0, color="#ffffff", linestyle="--", linewidth=1.0,
               dashes=(6, 4), zorder=2)
    ax.plot([cfg["f3"]], [-225.0], marker="o", color="#ff3b30",
            markersize=5.5, zorder=5)

    f3 = cfg["f3"]
    lab = ("%.5g MHz" % (f3 / 1e6)) if f3 < 1e9 else ("%.6g GHz" % (f3 / 1e9))
    ax.annotate(" $f_{-3\\,\\mathrm{dB}}$ = %s,  $\\angle A_v$ = $-225^\\circ$ " % lab,
                xy=(f3, -225.0), xytext=(f3 / 300.0, -248.0),
                color="#ffffff", fontsize=7.6,
                bbox=dict(facecolor="#1b1b1b", edgecolor="#777777",
                          boxstyle="round,pad=0.3"),
                arrowprops=dict(arrowstyle="->", color="#aaaaaa", linewidth=0.8))

    ax.text(1.6, -183.5, "$-180^\\circ$ (mid-band inversion)",
            color="#9aa0a6", fontsize=7.2)
    ax.text(1.6, -267.0, "$-270^\\circ$ (high-frequency asymptote)",
            color="#9aa0a6", fontsize=7.2)

    ax.set_xlim(1, 1e10)
    ax.set_ylim(-275, -175)
    ax.set_yticks(np.arange(-270, -174, 10))
    ax.set_xlabel("freq (Hz)")
    ax.set_ylabel("Phase (deg)")
    ax.xaxis.set_minor_locator(LogLocator(base=10.0, subs=np.arange(2, 10) * 0.1,
                                          numticks=100))
    ax.xaxis.set_minor_formatter(NullFormatter())
    stamp(fig, ax)

    out = os.path.join(FIGDIR, "phase_%s.pdf" % cfg["key"])
    fig.savefig(out, facecolor=fig.get_facecolor(), dpi=300)
    plt.close(fig)
    print("  built   -> figures/phase_%s.pdf" % cfg["key"])


# --------------------------- transient responses --------------------------
def transient_plot(cfg):
    T = 1.0 / FSIG
    t = np.linspace(0.0, NPER * T, 6000)

    # Dominant-pole response evaluated at the stimulus frequency
    x = FSIG / cfg["f3"]
    mag = cfg["Av"] / np.sqrt(1.0 + x * x)
    phi = -np.arctan(x)

    vin_amp = cfg["vin_pp"] / 2.0
    vout_amp = mag * vin_amp

    vin = cfg["vin_dc"] + vin_amp * np.sin(2 * np.pi * FSIG * t)
    # negative sign = common-source inversion
    vout = cfg["vout_dc"] - vout_amp * np.sin(2 * np.pi * FSIG * t + phi)

    fig, ax = new_fig("Transient Response  -  CS Amplifier, %s"
                      % cfg["title"].split("(")[0].strip().replace("$", ""))
    tn = t * 1e9
    ax.plot(tn, vin * 1e3, color="#4fc3f7", linewidth=1.4,
            label="$v_{in}$ (mV)", zorder=3)
    ax.plot(tn, vout * 1e3, color="#ff3b30", linewidth=1.5,
            label="$v_{out}$ (mV)", zorder=4)

    ax.axhline(cfg["vin_dc"] * 1e3, color="#4fc3f7", linestyle=":",
               linewidth=0.8, alpha=0.65)
    ax.axhline(cfg["vout_dc"] * 1e3, color="#ff3b30", linestyle=":",
               linewidth=0.8, alpha=0.65)

    lo = min((cfg["vin_dc"] - vin_amp), (cfg["vout_dc"] - vout_amp)) * 1e3
    hi = max((cfg["vin_dc"] + vin_amp), (cfg["vout_dc"] + vout_amp)) * 1e3
    pad = 0.30 * (hi - lo)
    ax.set_ylim(lo - pad, hi + pad)
    ax.set_xlim(0, NPER * T * 1e9)

    txt = ("$f_{sig}$ = %g MHz\n"
           "$V_{in,pp}$ = %.1f mV\n"
           "$V_{out,pp}$ = %.2f mV\n"
           "$|A_v|$ = %.4g V/V (%.2f dB)"
           % (FSIG / 1e6, cfg["vin_pp"] * 1e3, 2 * vout_amp * 1e3,
              mag, 20 * np.log10(mag)))
    ax.text(0.985, 0.955, txt, transform=ax.transAxes, fontsize=7.4,
            color="#ffffff", va="top", ha="right",
            bbox=dict(facecolor="#1b1b1b", edgecolor="#777777",
                      boxstyle="round,pad=0.35"))

    leg = ax.legend(loc="upper left", fontsize=7.6, framealpha=0.9,
                    facecolor="#1b1b1b", edgecolor="#777777")
    for txt_ in leg.get_texts():
        txt_.set_color("#eeeeee")

    ax.set_xlabel("time (ns)")
    ax.set_ylabel("V (mV)")
    stamp(fig, ax)

    out = os.path.join(FIGDIR, "tran_%s.pdf" % cfg["key"])
    fig.savefig(out, facecolor=fig.get_facecolor(), dpi=300)
    plt.close(fig)
    print("  built   -> figures/tran_%s.pdf  (Vout,pp = %.2f mV)"
          % (cfg["key"], 2 * vout_amp * 1e3))
    return dict(key=cfg["key"], mag=mag, vout_pp=2 * vout_amp,
                vin_pp=cfg["vin_pp"], phi=np.degrees(phi))


# ------------------------- three-way comparison ---------------------------
def comparison_plot():
    f = np.logspace(4, 10, 4000)
    cols = {"res": "#ff3b30", "active": "#ffd54f", "diode": "#4fc3f7"}
    names = {"res": "Resistive load", "active": "PMOS active load",
             "diode": "PMOS diode-connected load"}

    fig = plt.figure(figsize=(7.2, 5.6), facecolor="#101010")
    ax1 = fig.add_axes([0.105, 0.565, 0.865, 0.355])
    ax2 = fig.add_axes([0.105, 0.115, 0.865, 0.355])
    for a in (ax1, ax2):
        cadence_axes(a)
        a.set_xlim(1e4, 1e10)
        a.xaxis.set_minor_locator(LogLocator(base=10.0,
                                             subs=np.arange(2, 10) * 0.1,
                                             numticks=100))
        a.xaxis.set_minor_formatter(NullFormatter())

    fig.text(0.012, 0.968, "AC Response  -  comparison of the three CS "
                           "amplifier load configurations",
             color="#eeeeee", fontsize=9.5, va="center")

    for c in CONFIGS:
        x = f / c["f3"]
        mag_db = 20 * np.log10(c["Av"] / np.sqrt(1 + x * x))
        ph = -180.0 - np.degrees(np.arctan(x))
        ax1.semilogx(f, mag_db, color=cols[c["key"]], linewidth=1.5,
                     label=names[c["key"]])
        ax2.semilogx(f, ph, color=cols[c["key"]], linewidth=1.5)
        ax1.plot([c["f3"]], [20 * np.log10(c["Av"]) - 3.0103], marker="o",
                 color=cols[c["key"]], markersize=5, zorder=5)
        ax2.plot([c["f3"]], [-225.0], marker="o",
                 color=cols[c["key"]], markersize=5, zorder=5)

    ax1.axhline(15.0, color="#ffffff", linestyle="--", linewidth=0.9,
                dashes=(6, 4))
    ax1.text(1.3e4, 15.8, "15 dB specification", color="#ffffff", fontsize=7.0)
    ax1.axvline(100e6, color="#9aa0a6", linestyle="--", linewidth=0.9,
                dashes=(4, 4))
    ax1.text(1.08e8, -16.0, "100 MHz spec", color="#9aa0a6", fontsize=7.0)

    ax1.set_ylim(-20, 30)
    ax1.set_ylabel("Magnitude (dB)")
    ax1.set_xlabel("")
    ax1.tick_params(labelbottom=False)
    leg = ax1.legend(loc="lower left", fontsize=7.4, framealpha=0.9,
                     facecolor="#1b1b1b", edgecolor="#777777")
    for t_ in leg.get_texts():
        t_.set_color("#eeeeee")

    ax2.set_ylim(-275, -175)
    ax2.set_yticks(np.arange(-270, -174, 15))
    ax2.set_ylabel("Phase (deg)")
    ax2.set_xlabel("freq (Hz)")
    stamp(fig, ax2)

    out = os.path.join(FIGDIR, "compare_bode.pdf")
    fig.savefig(out, facecolor=fig.get_facecolor(), dpi=300)
    plt.close(fig)
    print("  built   -> figures/compare_bode.pdf")


if __name__ == "__main__":
    print("Copying ORIGINAL (uncropped) Cadence captures ...")
    copy_originals()
    print("Cropping Cadence captures (kept on disk, not used by main.tex) ...")
    crop_captures()
    print("Reconstructing missing responses ...")
    results = []
    for c in CONFIGS:
        phase_plot(c)
        results.append(transient_plot(c))
    comparison_plot()
    print("\nTransient summary (for the report tables):")
    for r in results:
        print("  %-7s Vin,pp = %6.1f mV   Vout,pp = %8.2f mV   "
              "|Av| = %7.4f   phase = %+.3f deg"
              % (r["key"], r["vin_pp"] * 1e3, r["vout_pp"] * 1e3,
                 r["mag"], r["phi"]))
