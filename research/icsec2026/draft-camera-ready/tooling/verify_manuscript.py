#!/usr/bin/env python3
"""Verify the CAMERA-READY manuscript against the draft-camera-ready evidence.

DRAFT-CAMERA-READY port (2026-10-18) of formal/tooling/verify_manuscript.py. Reads the re-modelled payload
link (round trip A2, status block A7), its retained verifyta run and oracle, the draft conformance report
and the code-level conformance run, all under research/icsec2026/draft-camera-ready/. The positioning lock
is still the approved one in formal/. Usage:

    verify_manuscript.py [--tex PATH] [--max-pages N]     (defaults: submission/main.tex, 6)

Every number the manuscript states must be reproducible from a retained artifact:

  * positioning lock hash equals the approval record;
  * the newest verifyta results directory verifies against its inventory and matches the oracle;
  * configuration count, formula count and state counts quoted in main.tex equal the retained outputs;
  * bounds quoted in main.tex equal the values derived from the model constants;
  * conformance numbers (anchors, bound check, clock disagreement, per-mode rows) equal the report;
  * every property identifier used in the body is defined in the properties table;
  * bibliography hygiene, banned phrases and identity strings, one canonical source, no draft markers;
  * if submission/build/main.pdf exists and pypdf is available: 4-6 pages and no identity strings.

Exit 0 on success, 1 on any hard failure. Prints one line per check.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
FORMAL = ROOT / "research/icsec2026/formal"              # approved positioning lock only
DRAFT = ROOT / "research/icsec2026/draft-camera-ready"   # models, results, oracle, conformance
SUBMISSION = ROOT / "research/icsec2026/submission"
_args = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
_args.add_argument("--tex", type=Path, default=SUBMISSION / "main.tex")
_args.add_argument("--max-pages", type=int, default=6)
ARGS = _args.parse_args()
TEX_PATH = ARGS.tex.resolve()
TEX_RAW = TEX_PATH.read_text(encoding="utf-8")
BIB = (TEX_PATH.parent / "references.bib").read_text(encoding="utf-8")

# The source carries both an anonymous and a camera-ready author block behind \ifanon.
# Anonymity is checked against the branch that is actually selected, so a review build cannot
# leak identity while a camera-ready build is allowed to name the authors.
ANON = re.search(r"^\\anontrue\s*$", TEX_RAW, flags=re.MULTILINE) is not None


def _select_branch(text: str, anon: bool) -> str:
    r"""Drop the inactive \ifanon branch so checks see the source as it will be typeset."""
    return re.sub(r"(?<!\\newif)\\ifanon(.*?)\\else(.*?)\\fi",
                  lambda m: m.group(1) if anon else m.group(2), text, flags=re.S)


CONTRIB = re.search(r"^\\contribtrue\s*$", TEX_RAW, flags=re.MULTILINE) is not None
TEX = _select_branch(TEX_RAW, ANON)
# Camera-ready-only statements (author contributions, funding, conflicts) sit behind \ifcontrib.
TEX = re.sub(r"(?<!\\newif)\\ifcontrib(.*?)\\fi", lambda m: m.group(1) if CONTRIB else "", TEX, flags=re.S)
# DRAFT: drawing code and comments are not manuscript text; a TikZ "minimum size=8.6mm" once satisfied an
# evidence check for 8.6 ms. Numbers are checked against the typeset text only.
TEX = re.sub(r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}", "", TEX, flags=re.S)
TEX = re.sub(r"(?<!\\)%.*", "", TEX)

WORD_NUMBERS = {11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen", 15: "fifteen",
                16: "sixteen", 21: "twenty-one"}

failures: list[str] = []
warnings: list[str] = []


def ok(msg: str) -> None:
    print(f"OK    {msg}")


def fail(msg: str) -> None:
    failures.append(msg)
    print(f"FAIL  {msg}")


def warn(msg: str) -> None:
    warnings.append(msg)
    print(f"WARN  {msg}")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def states(results: Path, name: str) -> int:
    out = (results / f"{name}.out").read_text(errors="replace")
    return max(int(x) for x in re.findall(r"States stored : (\d+) states", out))


# 1. positioning lock approval -------------------------------------------------------------------
approval = (FORMAL / "POSITIONING_LOCK_FORMAL_APPROVAL.md").read_text(encoding="utf-8")
approved = re.search(r"Approved SHA-256: `([0-9A-F]{64})`", approval)
actual = sha256(FORMAL / "POSITIONING_LOCK_FORMAL.md")
if approved and approved.group(1) == actual:
    ok(f"positioning lock hash matches approval ({actual[:8]}…)")
else:
    fail(f"positioning lock hash {actual[:8]}… differs from approval record")

# 2. retained results ------------------------------------------------------------------------------
# newest full batch; probe directories (suffix after the stamp) are supporting runs, not batches
result_dirs = sorted(p for p in (DRAFT / "results").iterdir() if p.is_dir() and re.fullmatch(r"\d{8}T\d{6}Z", p.name))
if not result_dirs:
    fail("no retained verifyta results directory")
    results = None
else:
    results = result_dirs[-1]
    ok(f"using retained results {results.name}")
    inv = results / "SHA256SUMS.csv"
    bad = 0
    with inv.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            path = results / row["relative_path"].lstrip("./")
            if (not path.exists() or sha256(path) != row["sha256"].upper()
                    or path.stat().st_size != int(row["size_bytes"])):
                bad += 1
    fail(f"{bad} rows of {inv.name} do not verify") if bad else ok(f"results inventory verifies ({inv.name})")
    proc = subprocess.run([sys.executable, str(DRAFT / "tooling/check_verdicts.py"), str(results)],
                          capture_output=True, text=True)
    last = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else proc.stderr.strip()
    ok(f"verdict oracle: {last}") if proc.returncode == 0 else fail(f"verdict oracle mismatch: {last}")

# 3. counts and state counts quoted in the manuscript ----------------------------------------------
if results:
    outs = sorted(p.stem for p in results.glob("*.out"))
    total = sum(len(re.findall(r"-- Formula is", (results / f"{n}.out").read_text(errors="replace")))
                for n in outs)
    m = re.search(r"(\d+) formulas, all verdicts equal", TEX)
    if m and int(m.group(1)) == total:
        ok(f"manuscript formula total {total} equals retained outputs")
    else:
        fail(f"manuscript formula total {m.group(1) if m else '?'} != retained {total}")
    # Every count the body quotes must be the same one. A stale "240 verdicts" survived in the
    # conclusion once while the abstract and results section already said 254, so check them all
    # rather than only the first phrasing.
    # Anchored to phrasings that quote the batch total, so the legitimate per-model
    # counts ("19, 11 and 14 formulas for the three models") are not swept up.
    TOTAL_PATTERNS = (r"configurations and (\d+) formulas",
                      r"batch of (\d+) formulas",
                      r"configurations, (\d+) formulas",
                      r"All (\d+) verdicts")
    quoted = {int(n) for pat in TOTAL_PATTERNS for n in re.findall(pat, TEX)}
    stale = {n for n in quoted if n != total}
    ok(f"all {len(quoted)} quoted formula/verdict counts equal {total}") if not stale else fail(
        f"stale formula/verdict count(s) in manuscript: {sorted(stale)} (retained total {total})")
    n_cfg = len(outs)
    word = WORD_NUMBERS.get(n_cfg, str(n_cfg))
    if f"{n_cfg} configurations" in TEX and word in TEX:
        ok(f"configuration count {n_cfg} stated as digits and as '{word}'")
    else:
        fail(f"configuration count {n_cfg} not stated consistently (expected '{n_cfg} configurations' and '{word}')")

    # Table rows "<label> & <states> &" are checked against the retained "States stored" maxima. Labels are
    # the camera-ready verdict table's; a configuration the table does not list is not checked here.
    ROWS = [("payload_silent", r"SILENT"), ("payload_badcrc", r"BAD\\_CRC"),
            ("payload_delayed_90", r"DELAYED 90"), ("payload_delayed_100", r"DELAYED 100"),
            ("payload_silent_status", r"SILENT \+ status"), ("payload_badcrc_status", r"BAD\\_CRC \+ status"),
            ("payload_delayed_110_status", r"DELAYED 110 \+ status"),
            ("watchdog_nostall", "no stall"), ("watchdog_stall", "one stall"),
            ("boot_shipped", "shipped app"), ("boot_design", "design variant"), ("boot_f4fix", "F4 fix applied")]
    REQUIRED = {"payload_silent", "payload_silent_status", "watchdog_stall", "boot_shipped", "boot_design", "boot_f4fix"}
    for cfg, label in ROWS:
        n = states(results, cfg)
        row = re.search(rf"(?:^|&|\\\\)\s*{label} & ([\d\\,]+) &", TEX, flags=re.MULTILINE)
        if not row:
            (fail if cfg in REQUIRED else warn)(f"state count row '{label}' ({cfg}) not in the verdict table")
            continue
        quoted = int(row.group(1).replace("\\,", "").replace(",", ""))
        ok(f"state count {label}: {n}") if quoted == n else fail(f"state count {label}: manuscript {quoted} != retained {n}")

    biggest = max(states(results, n) for n in outs)
    if re.search(rf"largest state space is {biggest // 1000}\\,{biggest % 1000:03d}", TEX):
        ok(f"largest state space {biggest} stated")
    else:
        fail(f"largest state space {biggest} not stated")

# 4. bounds from the model constants ---------------------------------------------------------------
model = (DRAFT / "models/payload_link.xml").read_text(encoding="utf-8")
consts = {k: int(v) for k, v in re.findall(r"const int (\w+_MS)\s*=\s*(\d+);", model)}
P, D, L, J = consts["POLL_MS"], consts["DEADLINE_MS"], consts["LOOP_MS"], consts["JITTER_MS"]
DMIN, DMAX, RMIN, RMAX, DX = (consts[k] for k in ("DECODE_MIN_MS", "DECODE_MAX_MS", "RESP_MIN_MS", "RESP_MAX_MS", "DELAY_EXTRA_MS"))
SLIP = int(re.search(r"P_ST='s/SLIP_SELECT/(\d+)/", (DRAFT / "tooling/run_verifyta.sh").read_text()).group(1))
BOUNDS = {}
for slip in (0, SLIP):
    BOUNDS[slip] = (P + J - DMIN + D + L + J + slip,
                    3 * (P + J) - DMIN + D + L + J + slip,
                    P + J - DMIN + DMAX + RMAX + L + J + slip)
first, offline, recovery = BOUNDS[0]
for slip, (f_, o_, r_) in BOUNDS.items():
    for value, name in [(f_, "first-timeout"), (o_, "OFFLINE"), (r_, "recovery")]:
        ok(f"{name} bound {value} ms (SLIP {slip}) appears") if re.search(rf"\b{value}\b", TEX) else fail(
            f"{name} bound {value} ms (SLIP {slip}) missing from manuscript")
accept_edge = D - DMAX - DX - RMAX - 1                      # largest d with ACCEPTS
timeout_edge = D + L + J - DMIN - RMIN + 1                  # smallest d with TIMES_OUT at SLIP 0
for value, name in [(accept_edge, "acceptance edge"), (accept_edge + 1, "band lower edge"),
                    (timeout_edge - 1, "band upper edge (SLIP 0)"), (timeout_edge + SLIP - 1, "band upper edge (SLIP 60)")]:
    ok(f"{name} {value} ms appears") if re.search(rf"\b{value}\b", TEX) else fail(f"{name} {value} ms missing")
wd = (DRAFT / "models/watchdog_gating.xml").read_text(encoding="utf-8")
dl = [int(x) for x in re.search(r"DEADLINE\[2\]\s*=\s*\{\s*(\d+),\s*(\d+)\s*\}", wd).groups()]
slack = sum(int(re.search(rf"{k}\s*=\s*(\d+)", wd).group(1)) for k in ("WD_POLL_MS", "WD_TASK_MS", "JITTER_MS"))
for d in dl:
    ok(f"stall detection bound {d + slack} ms appears") if str(d + slack) in TEX else fail(
        f"stall detection bound {d + slack} ms missing")
# the first-timeout bound as a function of J: P - DMIN + D + L + 2J (+ SLIP)
base = P - DMIN + D + L
if re.search(rf"{base}\{{?\+?\}}?2J|{base}\+2J", TEX.replace(" ", "")):
    ok(f"jitter-parameterised bound {base}+2J stated")
else:
    fail(f"jitter-parameterised bound {base}+2J not stated")

# 5. conformance report ----------------------------------------------------------------------------
report_path = DRAFT / "conformance/results/conformance_report.json"
report = json.loads(report_path.read_text(encoding="utf-8"))
ok("conformance report: 0 issues") if report["total_issues"] == 0 else fail(
    f"conformance report has {report['total_issues']} issues")
for key in ("primary_campaign", "n0_pre", "n0_post", "extension_primary"):
    src = report[key]
    if sha256(ROOT / src["source"]) == src["source_sha256"]:
        ok(f"conformance input unchanged: {Path(src['source']).name}")
    else:
        fail(f"conformance input changed since report: {src['source']}")

prim = report["primary_campaign"]
bc, disagree = prim["bound_check"], prim["monotonic_tick_disagreement_ms"]
raw = report["raw_nominal"]
for value, label in [(bc["within_bound"], "within-bound count (SLIP 0)"), (bc["within_status_bound"], "within-bound count (SLIP 60)"),
                     (bc["intervals"], "interval count"),
                     (disagree["max"], "monotonic-tick disagreement max"),
                     (prim["bounds_ms"]["falsification_floor"], "falsification floor"),
                     (raw["status_slip_ms"]["min"], "status slip min"), (raw["status_slip_ms"]["max"], "status slip max"),
                     (raw["status_slip_ms"]["median"], "status slip median"), (raw["status_slip_ms"]["n"], "status reports measured")]:
    # DRAFT: whole-token match only, and a non-integer value may not be shown as a bare integer -- the
    # submitted gate accepted "9" for 8.6 because some unrelated 9 appeared in the text.
    exact = str(value) if not float(value).is_integer() else str(int(value))
    forms = {exact, str(round(float(value), 1))} if not float(value).is_integer() else {exact}
    shown = next((f for f in sorted(forms, key=len, reverse=True)
                  if re.search(rf"(?<![\d.]){re.escape(f)}(?![\d]|\.\d)", TEX)), None)
    ok(f"{label} {exact} stated as {shown}") if shown else fail(
        f"{label} {exact} missing from manuscript (accepted forms {sorted(forms)})")
# one decimal, whole token: the rounded integer ("7") would match any unrelated 7 in the text
_excess = f"{prim['unresolved_intervals'][0]['excess_ms']:.1f}" if prim["unresolved_intervals"] else None
if bc["unresolved"] == 1 and re.search(rf"(?<![\d.]){re.escape(_excess)}(?![\d])", TEX):
    ok(f"unresolved interval reported ({prim['unresolved_intervals'][0]['run_id']}, "
       f"{prim['unresolved_intervals'][0]['excess_ms']} ms excess)")
else:
    fail(f"unresolved interval count {bc['unresolved']} not reflected in the manuscript")
sw = DRAFT / "conformance/results/status_windows_report.json"
if sw.exists():
    swr = json.loads(sw.read_text(encoding="utf-8"))
    ok(f"status-window check present: {swr['runs_checked']} runs, {len(swr['hash_mismatches'])} hash mismatches")
else:
    warn(f"status-window check of R085 not run (raw logs from the backup needed); its {_excess} ms excess "
         "remains unresolved")

# On-target evidence (research/icsec2026/lab-partB). The host-derived read residual and time-base figures
# were superseded by MCU-side measurement: the residual missed the reader's slowly shifting lag, and the
# median-based rate was biased by it.
for stale, label in [("0.235", "old clock-rate figure"), ("498.83", "old mean poll period"),
                     ("0.84", "host-median MCU rate"), ("495.9", "host-median poll period"),
                     ("8.6", "host read residual")]:
    fail(f"{label} {stale} still in manuscript") if re.search(rf"(?<![\d.]){re.escape(stale)}(?![\d])", TEX) else ok(f"{label} {stale} removed")
LAB = ROOT / "research/icsec2026/lab-partB"


def _lab_run(pattern: str, shared: bool = False) -> Path | None:
    # Exactly one run per pattern: picking the newest would silently switch datasets when a run is added.
    hits = sorted(p for p in (LAB / "runs").glob(pattern) if p.is_dir() and ("shared-retained" in p.name) == shared)
    if len(hits) != 1:
        fail(f"expected exactly one lab run matching {pattern} (shared-retained={shared}), found "
             f"{[p.name for p in hits]}")
        return None
    if not (hits[0] / "INVENTORY.sha256").exists():
        fail(f"lab run {hits[0].name} not closed")
    return hits[0]


def _run_json(pattern: str, name: str) -> dict:
    run = _lab_run(pattern)
    if run is None:
        return {}
    if not (run / "INVENTORY.sha256").exists():
        fail(f"lab run {run.name} not closed")
    return json.loads((run / name).read_text(encoding="utf-8"))


def _shown(value: float, label: str, digits: int) -> None:
    # round half up on the decimal value as recorded (500.565 -> 500.57), not on its binary float
    from decimal import ROUND_HALF_UP, Decimal
    text = str(Decimal(str(value)).quantize(Decimal(1).scaleb(-digits), rounding=ROUND_HALF_UP))
    ok(f"{label} {text} stated") if re.search(rf"(?<![\d.]){re.escape(text)}(?![\d])", TEX) else fail(
        f"{label} {text} missing from manuscript")


b125 = _run_json("*_B1B2B5_*", "analysis_B1_B2_B5.json")
if b125:
    j = b125["B1_poll_jitter"]
    _shown(j["poll_period_all"]["min_ms"], "poll period min", 2)
    _shown(j["poll_period_all"]["max_ms"], "poll period max", 2)
    _shown(j["poll_period_all"]["max_abs_dev_ms"], "poll period excess", 2)
    _shown(j["poll_period_containing_status_report"]["max_dev_ms"], "status-period excess", 2)
    _shown(b125["B2_status_slip"]["status_span"]["max_ms"], "status write max", 2)
    _shown(b125["B5_round_trip"]["poll_to_accept"]["min_ms"], "poll-to-accept min", 2)
    _shown(b125["B5_round_trip"]["poll_to_accept"]["max_ms"], "poll-to-accept max", 2)
b6 = _run_json("*_B6_*", "analysis_B6.json")
if b6:
    _shown(b6["B6_recovery"]["recovery_interval"]["max_ms"], "MCU-timed recovery max", 1)
    _shown(b6["B6_recovery"]["detection_first_timeout"]["max_ms"], "MCU-timed first-timeout max", 1)
for pattern, label in (("*_B3link_*", "link"), ("*_B3heartbeat_*", "heartbeat")):
    b3 = _run_json(pattern, "analysis_B3.json")
    if b3:
        w = b3["B3_watchdog"]
        _shown(w["stall_to_record"]["min_ms"], f"{label} stall-to-expiry min", 1)
        _shown(w["stall_to_record"]["max_ms"], f"{label} stall-to-expiry max", 1)
        _shown(w["stall_to_reset"]["max_ms"], f"{label} stall-to-reset max", 1)
inj = json.loads((LAB / "analysis/injector_latency_B6.json").read_text(encoding="utf-8"))
_shown(inj["stamp_latency_relative_to_fastest_ms"]["max_ms"], "reader stamp lag range", 1)
_shown(inj["interval_containing_status"]["host"]["max_ms"], "host interval with status max", 1)
_shown(inj["interval_containing_status"]["mcu"]["max_ms"], "MCU interval with status max", 1)
hvm = json.loads((LAB / "analysis/host_vs_mcu_B1.json").read_text(encoding="utf-8"))
_shown(hvm["mean_period_ms"]["analyzer"], "analyzer mean period", 3)
_shown(hvm["mean_period_ms"]["host"], "host mean period", 3)


# Table tab:hw, row by row: every measured cell (ranges, sample counts, launch counts) is rebuilt from the
# closed lab runs, including the runs taken after the F5 fix, and must equal the typeset row.
def _q(value: float, digits: int) -> str:
    from decimal import ROUND_HALF_UP, Decimal
    return str(Decimal(str(value)).quantize(Decimal(1).scaleb(-digits), rounding=ROUND_HALF_UP))


def _rng(stats: dict, digits: int, n: bool = True) -> str:
    text = f"{_q(stats['min_ms'], digits)}--{_q(stats['max_ms'], digits)}"
    return f"{text} ({stats['n']})" if n else text


def _b4_launches(run: Path | None) -> dict:
    """{(scenario, mode, k): [boot outcomes]} from a B4 event log."""
    out: dict = {}
    if run is None:
        return out
    key = None
    for line in (run / "b4_events.jsonl").read_text(encoding="utf-8").splitlines():
        ev = json.loads(line)
        if ev["event"] == "scenario_start":
            key = (ev["scenario"], ev["mode"], ev["k"])
            out[key] = []
        elif ev["event"] == "boot" and key is not None:
            out[key].append(ev.get("outcome"))
        elif ev["event"] == "restore":
            key = None
    return out


def _until_refused(outcomes: list, slot: str) -> int | None:
    """launches of `slot` before the first SAFE_LOOP, or None if it is never refused."""
    if "SAFE_LOOP" not in outcomes:
        return None
    return outcomes[:outcomes.index("SAFE_LOOP")].count(f"LAUNCHED_{slot}")


hw_table = TEX[TEX.index(r"\label{tab:hw}"):TEX.index(r"\end{tabularx}", TEX.index(r"\label{tab:hw}"))]
hw_rows = {r.split("&")[0].strip(): r.strip() for r in hw_table.split(r"\\") if "&" in r}


def _row(label: str, expected_cells: str) -> None:
    row = next((v for k, v in hw_rows.items() if k.endswith(label)), None)
    got = row.split("&", 2)[2].strip() if row else None
    ok(f"tab:hw row '{label}' matches the lab runs") if got == expected_cells else fail(
        f"tab:hw row '{label}': manuscript {got!r}, lab runs give {expected_cells!r}")


stall = {lbl: _run_json(p, "analysis_B3.json").get("B3_watchdog", {})
         for p, lbl in (("*_B3link_*", "link"), ("*_B3heartbeat_*", "heartbeat"))}
shared_stalls = []
for pattern in ("*_B3link_*", "*_B3heartbeat_*"):
    run = _lab_run(pattern, shared=True)
    if run is not None:
        shared_stalls += [json.loads(x) for x in (run / "stall_trials.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
if b125 and b6 and all(stall.values()):
    j, b2 = b125["B1_poll_jitter"], b125["B2_status_slip"]
    _row("Poll period: all; with status",
         f"{_rng(j['poll_period_all'], 2)}; {_rng(j['poll_period_containing_status_report'], 2)}")
    _row("Status write blocks link task", _rng(b2["status_span"], 2))
    _row("Poll to accepted frame$^\\dagger$", _rng(b125["B5_round_trip"]["poll_to_accept"], 2))
    _row("Fault to first timeout$^\\dagger$", _rng(b6["B6_recovery"]["detection_first_timeout"], 1))
    _row("NORMAL to recovery$^\\dagger$", _rng(b6["B6_recovery"]["recovery_interval"], 1))
    _row("Stall to expiry: link; heartbeat",
         f"{_rng(stall['link']['stall_to_record'], 1)}; {_rng(stall['heartbeat']['stall_to_record'], 1)}")
    _row("Stall to reset: link; heartbeat",
         f"{_rng(stall['link']['stall_to_reset'], 1, n=False)}; {_rng(stall['heartbeat']['stall_to_reset'], 1, n=False)}")
    # expiry-to-reset span over both stall targets (explains why it is below the IWDG minimum)
    _shown(min(stall[k]["record_to_reset"]["min_ms"] for k in stall), "expiry-to-reset min", 1)
    _shown(max(stall[k]["record_to_reset"]["max_ms"] for k in stall), "expiry-to-reset max", 1)
    # "delays no poll by more than 0.40 ms": the poll that follows a status report
    _shown(b2["next_poll_slip_after_status"]["max_ms"], "poll slip after a status report", 2)
    relaunched = sum(stall[k]["relaunched_without_power_cycle"] for k in stall)
    trials = sum(stall[k]["trials"] for k in stall)
    safe = sum(t["after_stall"] == "BOOTLOADER_SAFE_LOOP" and t["after_warm_reset"] == "BOOTLOADER_SAFE_LOOP"
               and t["last_fail_name"] == "PriorCriticalFault" for t in shared_stalls)
    _row("After IWDG reset",
         f"relaunch {relaunched}/{trials}; fixed: safe loop {safe}/{len(shared_stalls)}, also after warm reset")
    total = trials + len(shared_stalls)
    ok(f"stall injection total {total} stated") if re.search(rf"(?<!\d){total} stall injections", TEX) else fail(
        f"stall injection total {total} not stated as '{total} stall injections'")

fixed = _b4_launches(_lab_run("*_B4_boot-policy-fixed"))
prefix = _b4_launches(_lab_run("*_B4_boot-policy-prefix"))
shared_b4 = _b4_launches(_lab_run("*_B4_*", shared=True))
if fixed and prefix and shared_b4:
    # B3: before F5 the application run restarts the Pending count (one launch, then fallback to A);
    # with the fix, and in policy mode, the Pending slot gets 4 launches and is then refused.
    pre_f5 = fixed.get(("c", "system", 2), [])
    app_run = pre_f5.count("LAUNCHED_B") if pre_f5 and pre_f5[0] == "LAUNCHED_B" and "SAFE_LOOP" not in pre_f5 else None
    refused = {_until_refused(fixed.get(("c", "policy", 2), []), "B"), _until_refused(shared_b4.get(("c", "system", 2), []), "B")}
    _row("Pending slot, resets",
         f"app run: {app_run} launch, then A; fixed, no app: {refused.pop() if len(refused) == 1 else refused}, then refused")
    pre = [_until_refused(prefix.get(("d", "policy", k), []), "B") for k in (1, 2, 3)]
    fix_policy = [_until_refused(fixed.get(("d", "policy", k), []), "B") for k in (1, 2, 3)]
    fix_system = [_until_refused(shared_b4.get(("d", "system", k), []), "B") for k in (1, 2, 3)]
    if fix_policy != fix_system:
        fail(f"F4 fixed launches differ between policy mode {fix_policy} and the shared-retained system run {fix_system}")
    _row("Fallback after $k{=}1,2,3$ resets",
         f"pre-fix {', '.join(map(str, pre))}; fixed {', '.join(map(str, fix_policy))}")

# code-level conformance run (draft-camera-ready/code_conformance)
cc_dirs = sorted(p for p in (DRAFT / "code_conformance/results").iterdir() if p.is_dir())
if cc_dirs:
    cc = cc_dirs[-1]
    bad = 0
    with (cc / "SHA256SUMS.csv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            path = cc / row["relative_path"].lstrip("./")
            bad += (not path.exists()) or sha256(path) != row["sha256"].upper()
    texts = {p.name: p.read_text() for p in cc.glob("*.txt")}
    passed = ("failures=0" in texts.get("payload_link.txt", "") and "failures=0" in texts.get("watchdog_gate.txt", "")
              and all("SAFETY(B1,B2,B4,B6,B9)=HOLD LIMIT(B3,B8)=HOLD" in texts.get(f"boot_fixed_{v}.txt", "") for v in ("shipped", "design"))
              and all("LIMIT(B3,B8)=VIOLATED" in texts.get(f"boot_prefix_{v}.txt", "") for v in ("shipped", "design")))
    ok(f"code conformance run {cc.name} verifies and passes") if (bad == 0 and passed) else fail(
        f"code conformance run {cc.name}: inventory rows bad {bad}, expectations met {passed}")
else:
    fail("no code conformance run retained")

TEX_MODE = {"SILENT": "SILENT", "BAD_CRC": r"BAD\\_CRC", "DELAYED": "DELAYED 250"}
for mode, m in prim["per_mode"].items():
    for kind, bound in (("detection", first), ("recovery", recovery)):
        cmd = int(round(m["command_anchored"][kind]["max_ms"]))
        med = int(round(m["confirmation_anchored"][kind]["median_ms"]))
        mx = int(round(m["confirmation_anchored"][kind]["max_ms"]))
        within = m["within_bound"][kind]
        want = rf"{TEX_MODE[mode]}\s*& {kind}\s*& {bound} & {cmd} & {med} & {mx} & {within}/30"
        ok(f"bound row {mode} {kind} matches report") if re.search(want, TEX) else fail(
            f"bound row {mode} {kind} missing or differs: expected /{want}/")

# 6. property identifiers used in the body must be defined in the properties table -----------------
table = TEX[TEX.index(r"\label{tab:props}"):TEX.index(r"\end{tabularx}", TEX.index(r"\label{tab:props}"))]
defined: set[str] = set()
for line in table.splitlines():
    cell = line.split("&")[0].strip()
    for base in re.findall(r"\b([QWB]\d+)", cell):
        defined.add(base)
    for base, extra in re.findall(r"\b([QWB]\d+)\(([^)]*)\)", cell):
        for suffix in extra.split(","):
            if suffix.strip():
                defined.add(base + suffix.strip())
SUFFIXES = ("", "T", "a", "b", "c", "r", "1", "2")
body = TEX[TEX.index(r"\section{Introduction}"):]
used = {i for i in re.findall(r"\b([QWB]\d+[a-zA-Z]?)\b", body)}
undefined = sorted(i for i in used
                   if not any(i == base + suffix for base in defined for suffix in SUFFIXES))
if undefined:
    fail(f"property identifiers used but not defined in Table I: {undefined}")
else:
    ok(f"all {len(used)} property identifiers used in the body are defined in the properties table")

# 7. bibliography, wording and draft hygiene -------------------------------------------------------
entries = set(re.findall(r"^@\w+\{([^,]+),", BIB, flags=re.MULTILINE))
cited: set[str] = set()
for group in re.findall(r"\\cite\{([^}]*)\}", TEX):
    cited.update(k.strip() for k in group.split(","))
fail(f"citations without bib entry: {sorted(cited - entries)}") if cited - entries else ok(
    f"all {len(cited)} citation keys defined")
warn(f"bib entries not cited: {sorted(entries - cited)}") if entries - cited else ok("every bib entry is cited")
# Overclaiming phrases are forbidden in both modes; identity strings only in the anonymous one.
banned = [b for b in ("state-of-the-art", "superior", "first ever", "unique") if b.lower() in TEX.lower()]
fail(f"banned phrases present: {banned}") if banned else ok("banned phrases absent")
if ANON:
    leaked = [b for b in ("WashiOS", "WashiBoot", "Borworntat", "Dendumrongkul", "Chulalongkorn",
                          "chula.ac.th", "INSTED", "International Institute of Space Technology")
              if b.lower() in TEX.lower()]
    fail(f"identity strings in the anonymous build: {leaked}") if leaked else ok(
        "no identity strings in the anonymous build")
if ANON and CONTRIB:
    fail("\\contribtrue set in the anonymous build (author contributions would name the authors)")
if ANON:
    ok("build mode: anonymous (review)")
    # The review build may either omit the author block or carry placeholder blocks that mirror the
    # camera-ready author count. Placeholders must name no person, institution or real address.
    anon_names = re.findall(r"\\IEEEauthorblockN\{([^}]*)\}", TEX)
    anon_region = TEX[TEX.find(r"\author{"):TEX.find(r"\begin{document}")]
    anon_mails = re.findall(r"[\w.+-]+@[\w.-]+", anon_region)
    bad_mails = [m for m in anon_mails if not re.fullmatch(r"anonymous\d*@anonymous\.edu", m)]
    if re.search(r"\\author\{\s*\}", TEX):
        ok("author block empty (double-anonymous)")
    elif anon_names and all(re.fullmatch(r"Anonymous Author(?: \d+|\(s\))", n.strip()) for n in anon_names):
        fail(f"non-anonymous addresses in the anonymous author block: {bad_mails}") if bad_mails else ok(
            f"author block carries {len(anon_names)} anonymous placeholder(s) (double-anonymous)")
    else:
        fail(f"anonymous mode selected but the author block names authors: {anon_names}")
else:
    warn("build mode: CAMERA-READY, author block active -- do not use for a double-anonymous submission")
    ok("author block present") if r"\IEEEauthorblockN" in TEX else fail("camera-ready mode but no author block")
ok("one canonical manuscript source") if list(TEX_PATH.parent.glob("main*.tex")) == [TEX_PATH] else fail(
    f"multiple main*.tex sources in {TEX_PATH.parent}")
pending = [m for m in re.findall(r"\\pending\{([^}]*)\}", TEX) if m]
fail(f"{len(pending)} \\pending markers remain: {pending}") if pending else ok("no \\pending markers")

# 8. optional PDF checks ---------------------------------------------------------------------------
pdf = TEX_PATH.parent / "build" / "main.pdf"
if pdf.exists():
    try:
        from pypdf import PdfReader  # type: ignore
        reader = PdfReader(str(pdf))
        pages = len(reader.pages)
        text = "".join((pg.extract_text() or "") for pg in reader.pages).lower()
        ok(f"PDF page count {pages}") if 4 <= pages <= ARGS.max_pages else fail(f"PDF page count {pages} outside 4-{ARGS.max_pages}")
        if ANON:
            for ident in ("washios", "washiboot", "borworntat", "chulalongkorn", "chula.ac.th", "insted",
                          "international institute of space technology"):
                if ident in text:
                    fail(f"identity string in anonymous PDF text: {ident}")
        meta = reader.metadata or {}
        if any(v for k, v in meta.items() if k.lower().endswith("author") and v):
            fail("PDF metadata contains an author")
        else:
            ok("PDF metadata has no author")
    except ImportError:
        # The page limit is the check that matters most for a camera-ready build: never skip it silently.
        try:
            info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, check=True).stdout
            pages = int(re.search(r"^Pages:\s+(\d+)", info, flags=re.MULTILINE).group(1))
            ok(f"PDF page count {pages} (pdfinfo)") if 4 <= pages <= ARGS.max_pages else fail(
                f"PDF page count {pages} outside 4-{ARGS.max_pages}")
            warn("pypdf not installed; PDF text and metadata checks skipped")
        except (OSError, subprocess.CalledProcessError, AttributeError):
            fail("neither pypdf nor pdfinfo available; PDF page count not checked")
    if pdf.stat().st_mtime < TEX_PATH.stat().st_mtime:
        fail(f"{pdf} is older than {TEX_PATH.name}; rebuild before trusting the page count")
elif ANON:
    warn(f"{pdf} not built; PDF checks skipped")
else:
    fail(f"{pdf} not built; the camera-ready page limit cannot be checked")

print()
print(f"{len(failures)} failure(s), {len(warnings)} warning(s)")
sys.exit(1 if failures else 0)
