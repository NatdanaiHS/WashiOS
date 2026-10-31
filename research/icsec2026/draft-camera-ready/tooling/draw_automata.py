#!/usr/bin/env python3
"""Draw the three UPPAAL models as SVG (and PNG via ImageMagick when available).

Pure standard library. Output: research/icsec2026/formal/figures/{payload_link,watchdog_gating,boot_policy}.{svg,png}
The drawings are hand-laid-out views of models/*.xml for reading; the XML files remain the verified artifacts.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "figures"
OUT.mkdir(exist_ok=True)

FONT = "font-family='DejaVu Sans, Arial, sans-serif'"

# Mean advance width of DejaVu Sans as a fraction of the font size. Used only to size the white
# plate drawn behind a label so an edge never strikes through its text; a small overestimate is
# harmless, an underestimate is not.
ADVANCE = 0.60
ADVANCE_BOLD = 0.64


class Svg:
    """Shapes, then label plates, then label text.

    Every string is emitted into `self.texts` and every string gets an opaque plate in
    `self.plates`; `save()` concatenates shapes, plates and text in that order. An edge can
    therefore never strike through a label, and a later label's plate can never cover an
    earlier label's text.
    """

    def __init__(self, w: int, h: int, title: str):
        self.w, self.h = w, h
        self.parts = [
            f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}'>",
            "<defs><marker id='arr' markerWidth='10' markerHeight='10' refX='9' refY='5' orient='auto' markerUnits='strokeWidth'>"
            "<path d='M0,0 L10,5 L0,10 z' fill='#222'/></marker>"
            "<marker id='arrRed' markerWidth='10' markerHeight='10' refX='9' refY='5' orient='auto' markerUnits='strokeWidth'>"
            "<path d='M0,0 L10,5 L0,10 z' fill='#c00000'/></marker></defs>",
            f"<rect width='{w}' height='{h}' fill='white'/>",
        ]
        self.plates: list[str] = []
        self.texts: list[str] = []
        self._emit(w / 2, 34, title, 22, "#111", "middle", bold=True, plate=False)

    def _emit(self, x, y, s, size, color, anchor, bold=False, italic=False, plate=True, fill="white"):
        """Queue one string plus the plate that keeps lines off it."""
        if plate and s:
            adv = ADVANCE_BOLD if bold else ADVANCE
            w = adv * size * len(s) + 6
            x0 = {"middle": x - w / 2, "end": x - w, "start": x - 3}[anchor]
            self.plates.append((x0, y - size * 0.82, w, size * 1.12, fill, s))
        style = " font-style='italic'" if italic else ""
        weight = " font-weight='bold'" if bold else ""
        self.texts.append(
            f"<text x='{x}' y='{y}' text-anchor='{anchor}' {FONT} font-size='{size}' fill='{color}'{style}{weight}>{s}</text>")

    def lane(self, x, y, w, h, name, color):
        self.parts.append(f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='14' fill='{color}' stroke='#999' stroke-dasharray='6 4'/>")
        self._emit(x + 14, y + 26, name, 17, "#333", "start", bold=True, fill=color)

    def loc(self, x, y, name, inv=None, initial=False, kind=None, r=34):
        stroke = "#1a4d8f"
        fill = "#e8f0fb"
        if kind == "committed":
            fill, stroke = "#fde9c9", "#b35c00"
        if kind == "urgent":
            fill, stroke = "#e6f6e6", "#2e7d32"
        if kind == "bad":
            fill, stroke = "#fbe0e0", "#a30000"
        self.parts.append(f"<circle cx='{x}' cy='{y}' r='{r}' fill='{fill}' stroke='{stroke}' stroke-width='2.5'/>")
        if initial:
            self.parts.append(f"<circle cx='{x}' cy='{y}' r='{r-6}' fill='none' stroke='{stroke}' stroke-width='1.5'/>")
        if kind in ("committed", "urgent"):
            self._emit(x, y + 6, "C" if kind == "committed" else "U", 18, stroke, "middle", bold=True, plate=False)
        self._emit(x, y - r - 10, name, 16, "#111", "middle", bold=True)
        if inv:
            self._emit(x, y + r + 20, inv, 13, "#7a2e8f", "middle", italic=True)

    def edge(self, x1, y1, x2, y2, labels, bend=0.0, lx=None, ly=None, anchor="middle", color=None, loff=0.0, lfill="white"):
        # quadratic curve with control point offset perpendicular to the chord
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        dx, dy = x2 - x1, y2 - y1
        L = max((dx * dx + dy * dy) ** 0.5, 1)
        nx, ny = -dy / L, dx / L
        cx, cy = mx + nx * bend, my + ny * bend
        head = "arr" if color is None else "arrRed"
        self.parts.append(f"<path d='M{x1},{y1} Q{cx},{cy} {x2},{y2}' fill='none' stroke='{color or '#222'}' "
                          f"stroke-width='{2.4 if color else 1.8}' marker-end='url(#{head})'/>")
        # label beside the curve: the point at t=0.5, pushed off along the curve normal by loff so
        # that the label's plate never interrupts its own edge
        px, py = 0.25 * x1 + 0.5 * cx + 0.25 * x2, 0.25 * y1 + 0.5 * cy + 0.25 * y2
        px, py = px + nx * loff, py + ny * loff
        lx = px if lx is None else lx
        ly = py if ly is None else ly
        self._labels(lx, ly, labels, anchor, lfill)

    def loop(self, x, y, r, labels, side="top", lx=None, ly=None, anchor="middle"):
        if side == "top":
            p = f"M{x-14},{y-r+4} C{x-70},{y-r-70} {x+70},{y-r-70} {x+14},{y-r+4}"
            lx = x if lx is None else lx
            ly = y - r - 58 if ly is None else ly
        elif side == "bottom":
            p = f"M{x-14},{y+r-4} C{x-70},{y+r+70} {x+70},{y+r+70} {x+14},{y+r-4}"
            lx = x if lx is None else lx
            ly = y + r + 72 if ly is None else ly
        elif side == "left":
            p = f"M{x-r+4},{y-14} C{x-r-70},{y-70} {x-r-70},{y+70} {x-r+4},{y+14}"
            lx = x - r - 78 if lx is None else lx
            ly = y if ly is None else ly
            anchor = "end"
        else:
            p = f"M{x+r-4},{y-14} C{x+r+70},{y-70} {x+r+70},{y+70} {x+r-4},{y+14}"
            lx = x + r + 78 if lx is None else lx
            ly = y if ly is None else ly
            anchor = "start"
        self.parts.append(f"<path d='{p}' fill='none' stroke='#222' stroke-width='1.8' marker-end='url(#arr)'/>")
        self._labels(lx, ly, labels, anchor)

    def _labels(self, x, y, labels, anchor, fill="white"):
        # labels: list of (text, kind) kind in guard/sync/update/note
        colors = {"guard": "#0b6e4f", "sync": "#1a4d8f", "update": "#8a4b00", "note": "#555", "find": "#c00000"}
        n = len(labels)
        y0 = y - (n - 1) * 8
        for i, (txt, kind) in enumerate(labels):
            self._emit(x, y0 + i * 16, txt, 13, colors[kind], anchor,
                       bold=(kind == "sync"), italic=(kind in ("note", "find")), fill=fill)

    def text(self, x, y, s, size=13, color="#333", anchor="start", bold=False, plate=False):
        self._emit(x, y, s, size, color, anchor, bold=bold, plate=plate)

    def legend(self, x, y):
        items = [("#0b6e4f", "guard (clock or data condition)"), ("#1a4d8f", "synchronisation  ch!  sender  /  ch?  receiver"),
                 ("#8a4b00", "update / clock reset"), ("#7a2e8f", "location invariant (time may not exceed)")]
        for i, (c, t) in enumerate(items):
            self.parts.append(f"<rect x='{x}' y='{y + i*20 - 11}' width='14' height='14' fill='{c}'/>")
            self.text(x + 22, y + i * 20, t, 13)
        self.text(x, y + 88, "double circle = initial location;  C = committed;  U = urgent", 13, "#555")

    def overlaps(self):
        """Pairs of label plates that intersect: two labels printed on top of each other."""
        bad = []
        for i, a in enumerate(self.plates):
            for b in self.plates[i + 1:]:
                if a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]:
                    bad.append((a[5], b[5]))
        return bad

    def save(self, stem: str):
        svg = OUT / f"{stem}.svg"
        rects = [f"<rect x='{x:.1f}' y='{y:.1f}' width='{w:.1f}' height='{h:.1f}' fill='{f}'/>"
                 for x, y, w, h, f, _ in self.plates]
        svg.write_text("\n".join(self.parts + rects + self.texts + ["</svg>"]), encoding="utf-8")
        png = OUT / f"{stem}.png"
        tool = shutil.which("magick") or shutil.which("convert")
        if tool:
            subprocess.run([tool, "-density", "110", "-background", "white", str(svg), str(png)], check=False)
        return svg, png


def payload_link():
    s = Svg(1700, 1000, "payload_link.xml — network of three timed automata (Controller ∥ Payload ∥ Host)")
    s.text(850, 60, "Constants: P = 500 ms poll, D = 100 ms deadline, N = 3 timeouts → OFFLINE, L = 1 ms loop, J = 2 ms jitter, TX ∈ [3,4] ms serialization, d = configured delay", 14, "#444", "middle")

    # Controller lane
    s.lane(40, 90, 1620, 300, "Controller  (core/include/comms/PayloadLinkController.hpp, PayloadLinkTask.hpp)", "#f7f9ff")
    cx1, cy = 330, 240
    cx2 = 1100
    s.loc(cx1, cy, "Idle", "xPoll ≤ P + J", initial=True)
    s.loc(cx2, cy, "Awaiting", "xResp ≤ D + L + J")
    s.edge(cx1 + 34, cy - 12, cx2 - 34, cy - 12, [("xPoll ≥ P", "guard"), ("poll!", "sync"), ("xPoll := 0, xResp := 0", "update")], bend=-70, ly=158)
    s.edge(cx2 - 34, cy + 6, cx1 + 34, cy + 6, [("resp_ok?", "sync"), ("consecutive := 0, link := ONLINE (recovery if was OFFLINE)", "update")], bend=-20, ly=278)
    s.edge(cx2 - 30, cy + 22, cx1 + 30, cy + 22, [("xResp ≥ D  (deadline)", "guard"), ("consecutive++;  if consecutive = N then link := OFFLINE", "update")], bend=-95, ly=350)
    s.loop(cx2, cy, 34, [("resp_badcrc?", "sync"), ("crc reject; poll stays pending", "update")], side="right")
    s.loop(cx1, cy, 34, [("resp_ok? (no poll pending)", "sync"), ("sequence reject", "update")], side="left")

    # Payload lane
    s.lane(40, 410, 1000, 290, "Payload  (demo-payload/src/main.cpp handleRequest)", "#fbfff7")
    px1, py = 300, 560
    px2 = 760
    s.loc(px1, py, "Ready", initial=True)
    s.loc(px2, py, "Responding")
    s.edge(px1 + 34, py - 12, px2 - 34, py - 12, [("mode ≠ SILENT", "guard"), ("poll?", "sync"), ("y := 0, pending := mode", "update")], bend=-60, ly=478)
    s.edge(px2 - 34, py + 6, px1 + 34, py + 6, [("pending ≠ BAD_CRC ∧ y ≥ delay(pending) + TX_MIN", "guard"), ("resp_ok!", "sync")], bend=-10, ly=592)
    s.edge(px2 - 30, py + 22, px1 + 30, py + 22, [("pending = BAD_CRC ∧ y ≥ TX_MIN", "guard"), ("resp_badcrc!", "sync")], bend=-80, ly=665)
    s.loop(px1, py, 34, [("mode = SILENT", "guard"), ("poll?  (no response)", "sync")], side="left")
    s.text(px2 + 46, py - 4, "y ≤ delay(pending) + TX_MAX", 13, "#7a2e8f", "start", plate=True)
    s.text(560, 690, "delay(pending) = d if pending = DELAYED, else 0", 13, "#555", "middle", plate=True)

    # Host lane
    s.lane(1060, 410, 600, 290, "Host  (frozen trial protocol)", "#fffaf3")
    hx = [1130, 1300, 1470, 1610]
    hy = 560
    s.loc(hx[0], hy, "Nominal", None, initial=True, r=28)
    s.loc(hx[1], hy, "Faulted", "z ≤ 4000", r=28)
    s.loc(hx[2], hy, "Restored", "zr ≤ 3000", r=28)
    s.loc(hx[3], hy, "Done", None, r=24)
    s.edge(hx[0] + 28, hy, hx[1] - 28, hy, [("zn ≥ 2P ∧ link = ONLINE", "guard"), ("inject!  mode := F, z := 0", "sync")], bend=-40, ly=470)
    s.edge(hx[1] + 28, hy, hx[2] - 28, hy, [("z ≥ 4000", "guard"), ("restore!  mode := NORMAL, zr := 0", "sync")], bend=40, ly=640)
    s.edge(hx[2] + 28, hy, hx[3] - 24, hy, [("zr ≥ 3000", "guard")], bend=-30, ly=497)

    # verified bounds box
    s.text(60, 740, "Verified (UPPAAL 5.0.0, results/20260908T074838Z):", 15, "#111", bold=True)
    for i, t in enumerate([
        "Q2  first timeout ≤ P + J + D + L + J = 605 ms after confirmed fault onset (tight)",
        "Q3  OFFLINE ≤ 3(P + J) + D + L + J = 1609 ms (tight)",
        "Q4  ONLINE ≤ P + J + TX_MAX = 506 ms after confirmed restoration (tight)",
        "Q9  d ≤ 95 ms always accepted;  d ≥ 101 ms always times out;  96–100 ms undetermined under J = 2 ms",
        "Q7  BAD_CRC: CRC reject always precedes the first timeout;  Q1: never OFFLINE while nominal",
    ]):
        s.text(60, 766 + i * 20, "• " + t, 14, "#222")
    s.legend(1100, 760)
    return (*s.save("payload_link"), s.overlaps())


def watchdog():
    s = Svg(1700, 900, "watchdog_gating.xml — Task(HB) ∥ Task(PL) ∥ Supervisor ∥ Iwdg ∥ Env")
    s.text(850, 60, "PERIOD = {500, 100} ms, DEADLINE = {1500, 800} ms, WD_POLL = 100 ms, WD_TASK = 50 ms, J = 2 ms, IWDG ∈ [1882, 2170] ms (nominal 2000; DS12589 Table 44)", 14, "#444", "middle")

    # Task template
    s.lane(40, 90, 620, 280, "Task(id)  ×2  (TaskHealthRegistry::checkIn)", "#f7f9ff")
    tx1, ty, tx2 = 200, 230, 520
    s.loc(tx1, ty, "Running", None, initial=True)
    s.text(tx1 + 46, ty + 12, "t ≤ PERIOD[id] + J", 13, "#7a2e8f", "start", plate=True)
    s.loc(tx2, ty, "Stalled", kind="bad")
    s.loop(tx1, ty, 34, [("t ≥ PERIOD[id]", "guard"), ("t := 0, since[id] := 0, healthy[id] := true", "update")], side="bottom", ly=338)
    s.edge(tx1 + 34, ty, tx2 - 34, ty, [("stall[id]?", "sync"), ("stalled[id] := true", "update")], bend=-40, ly=175)

    # Env
    s.lane(700, 90, 460, 280, "Env  (stall injector, SCENARIO 1 only)", "#fffaf3")
    ex1, ey, ex2 = 800, 230, 1060
    s.loc(ex1, ey, "Healthy", initial=True, r=30)
    s.loc(ex2, ey, "Injected", r=30)
    s.edge(ex1 + 30, ey - 8, ex2 - 30, ey - 8, [("e ≥ 3000", "guard"), ("stall[HB]!", "sync")], bend=-45, ly=165)
    s.edge(ex1 + 30, ey + 10, ex2 - 30, ey + 10, [("e ≥ 3000", "guard"), ("stall[PL]!", "sync")], bend=45, ly=300)

    # Iwdg
    s.lane(1200, 90, 460, 280, "Iwdg  (hardware independent watchdog)", "#fff5f5")
    ix1, iy, ix2 = 1300, 230, 1560
    s.loc(ix1, iy, "Counting", None, initial=True, r=30)
    s.text(ix1 + 42, iy + 44, "d ≤ IWDG_MAX", 13, "#7a2e8f", "start", plate=True)
    s.loc(ix2, iy, "Reset", kind="bad", r=30)
    s.loop(ix1, iy, 30, [("kick?", "sync"), ("d := 0", "update")], side="bottom", ly=345)
    s.edge(ix1 + 30, iy - 6, ix2 - 30, iy - 6, [("d ≥ IWDG_MIN", "guard"), ("resetHappened := true", "update")], bend=-40, ly=190)

    # Supervisor
    s.lane(40, 395, 1620, 300, "Supervisor  (WatchdogTask → WatchdogRunner::runOnce → Watchdog::poll → TaskHealthRegistry::evaluate)", "#fbfff7")
    sx, sy = 620, 560
    s.loc(sx, sy, "Polling", None, initial=True, r=40)
    s.text(sx - 115, sy + 6, "w ≤ WD_POLL + WD_TASK + J", 13, "#7a2e8f", "end", plate=True)
    s.loop(sx, sy, 40, [("w ≥ WD_POLL ∧ since[HB] ≤ DL[HB] ∧ since[PL] ≤ DL[PL]", "guard"), ("∧ healthy[HB] ∧ healthy[PL]", "guard"),
                        ("kick!   (HAL_IWDG_Refresh)", "sync"), ("w := 0", "update")], side="left", lx=560, ly=470, anchor="end")
    s.loop(sx, sy, 40, [("w ≥ WD_POLL ∧ since[id] > DL[id]  (expired, strict >)", "guard"),
                        ("w := 0, healthy[id] := false, criticalFailed := true", "update"),
                        ("(three edges: HB only, PL only, both)", "note")], side="right", lx=690, ly=560, anchor="start")
    s.loop(sx, sy, 40, [("w ≥ WD_POLL ∧ clocks within deadline ∧ ¬(all healthy)", "guard"), ("w := 0   (no refresh)", "update")], side="bottom", ly=668)
    s.text(1080, 480, "Refresh gate: the IWDG is kicked only on the all-healthy edge", 14, "#222")
    s.text(1080, 500, "(Watchdog.hpp:61-65). A stalled task never checks in, so once expired its", 14, "#222")
    s.text(1080, 520, "flag stays false and no further kick ever occurs (W2).", 14, "#222")
    s.text(1080, 545, "Verified:", 15, "#111", bold=True)
    for i, t in enumerate([
        "W1  no stall ⇒ never reset, never a critical failure (SCENARIO 0)",
        "W3  stall detected ≤ DL + 100 + 50 + 2 = 952 ms (PL) / 1652 ms (HB), tight",
        "W6  stall → IWDG reset ≤ detection bound + 2170 ms",
        "W7  a reset never happens before a critical failure is recorded",
    ]):
        s.text(1080, 570 + i * 20, "• " + t, 14, "#222")

    s.legend(60, 740)
    s.text(1000, 730, "On the G431 build the safe-fail callback only logs; the IWDG performs the reset", 13, "#555")
    s.text(1000, 750, "(core/src/main.cpp:81-93). After the reset the bootloader sees WatchdogTimeout in the", 13, "#555")
    s.text(1000, 770, "retained FaultLog and enters the safe loop instead of relaunching (finding F2).", 13, "#555")
    return (*s.save("watchdog_gating"), s.overlaps())


def boot():
    s = Svg(1700, 1060, "boot_policy.xml — Boot ∥ App ∥ Flash  (untimed; BootPolicy::run on every reset)")
    s.text(850, 60, "Retained across warm resets: active, stateA, stateB ∈ {Empty, Valid, Pending, Confirmed, Bad}, bootCount, confirmedFlag, retainedCriticalFault.  MAX_UNCONFIRMED = 3.", 14, "#444", "middle")
    s.lane(40, 90, 1620, 600, "Boot  (bootloader/include/boot/BootPolicy.hpp run(), BootMetadata.hpp)", "#f7f9ff")
    bx = {"Start": (200, 330), "Recovered": (560, 330), "Selecting": (920, 330), "App": (1540, 180), "Safe": (1540, 500)}
    s.loc(*bx["Start"], "Start", initial=True, kind="urgent")
    s.loc(*bx["Recovered"], "Recovered", kind="committed")
    s.loc(*bx["Selecting"], "Selecting", kind="committed")
    s.loc(*bx["App"], "AppRunning", r=40)
    s.loc(*bx["Safe"], "SafeLoop", kind="bad", r=40)
    # forward path: labels sit on their own edge, the plate keeps the line out of the text
    s.edge(234, 330, 526, 330, [("¬metadataCorrupt", "guard"), ("normalizeConfirmed()", "update")], bend=-30, loff=-24)
    s.edge(594, 330, 886, 330, [("¬loopLimit ∧", "guard"), ("¬retainedCriticalFault", "guard")], bend=-30, loff=-26)
    # two launch edges, separated so each label lies on its own curve
    s.edge(944, 306, 1502, 198, [("slotBootable(active)", "guard"), ("launch(active, false)", "update")], bend=-44, loff=-30)
    s.edge(952, 352, 1508, 224, [("¬slotBootable(active) ∧ slotBootable(other)", "guard"),
                                 ("active := other; launch(active, true)   —   bootCount NOT reset: finding F4", "find")],
           bend=76, loff=52, color="#c00000", lfill="#fff1f1")
    # refusals into SafeLoop: three curves at clearly different depths, each carrying its own label
    s.edge(946, 362, 1506, 474, [("¬slotBootable(active) ∧ ¬slotBootable(other)", "guard"), ("fail(NO_SLOT)", "update")], bend=-30, loff=38)
    s.edge(586, 358, 1500, 500, [("loopLimit: state(active) = Pending ∧ bootCount > 3", "guard"), ("retainedCriticalFault  (two edges)", "guard"),
                                 ("fail(BOOT_LOOP)  |  fail(PRIOR_FAULT)  (finding F2)", "update")], bend=104, lx=1000, ly=506)
    s.edge(224, 362, 1508, 532, [("metadataCorrupt", "guard"), ("fail(FAULTLOG)", "update")], bend=196, lx=700, ly=548)
    # resets back to start
    s.edge(1504, 145, 228, 300, [("reset?   (warm: watchdog or software reset)", "sync"), ("retained state kept", "update")], bend=112, loff=16)
    s.edge(1514, 536, 224, 352, [("coldStart?   (power cycle)", "sync"), ("retained state scrubbed: fault log, bootCount, flags", "update")], bend=-372, loff=10)

    # App and Flash lanes
    s.lane(40, 710, 780, 180, "App  (launched application)", "#fbfff7")
    for i, t in enumerate([
        "appRunning ∧ APP_CONFIRMS = 1   →  confirmedFlag := true        (design variant only)",
        "appRunning                          →  reset!  with retainedCriticalFault := true   (critical stall)",
        "appRunning                          →  reset!                                                   (clean reset)",
        "Shipped firmware never writes BootMetadata: APP_CONFIRMS = 0  (finding F1).",
    ]):
        s.text(60, 760 + i * 24, t, 13, "#222" if i < 3 else "#a30000")
    s.lane(860, 710, 800, 180, "Flash / environment", "#fffaf3")
    for i, t in enumerate([
        "appRunning ∨ safeLoop  →  imageOkA := false  |  imageOkB := false     (corruption)",
        "appRunning                 →  imageOkB := true, stateB := Pending           (stage an update)",
        "appRunning                 →  active := SlotB, bootCount := 0                 (switch slot)",
        "appRunning ∨ safeLoop  →  coldStart!   ;   appRunning → metadataCorrupt := true",
    ]):
        s.text(880, 760 + i * 24, t, 13, "#222")

    s.text(60, 915, "Verified:", 15, "#111", bold=True)
    for i, t in enumerate([
        "B1/B2  never launch an unvalidated image or a non-bootable slot state      B3  a Pending slot is launched ≤ 4 times in a row",
        "B4  both images bad at boot ⇝ SafeLoop      B6  retained critical fault ⇒ never relaunched before a cold start (F2)",
        "B7  shipped app: Pending never becomes Confirmed (F1)      B8  limit bypass reachable only via the fallback edge (F4); next warm boot is refused",
    ]):
        s.text(60, 940 + i * 22, "• " + t, 14, "#222")
    s.legend(1240, 925)
    return (*s.save("boot_policy"), s.overlaps())


if __name__ == "__main__":
    import sys

    clashes = 0
    for fn in (payload_link, watchdog, boot):
        svg, png, bad = fn()
        print(svg.relative_to(OUT.parents[2]), "->", png.name, "(png)" if png.exists() else "(png not produced)")
        for a, b in bad:
            clashes += 1
            print(f"    label overlap: {a!r} <-> {b!r}")
    sys.exit(1 if clashes else 0)
