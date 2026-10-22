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
                     (raw["host_read_residual_ms"]["max"], "host read residual max"),
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
if bc["unresolved"] == 1 and str(round(prim["unresolved_intervals"][0]["excess_ms"])) in TEX:
    ok(f"unresolved interval reported ({prim['unresolved_intervals'][0]['run_id']}, "
       f"{prim['unresolved_intervals'][0]['excess_ms']} ms excess)")
else:
    fail(f"unresolved interval count {bc['unresolved']} not reflected in the manuscript")
sw = DRAFT / "conformance/results/status_windows_report.json"
if sw.exists():
    swr = json.loads(sw.read_text(encoding="utf-8"))
    ok(f"status-window check present: {swr['runs_checked']} runs, {len(swr['hash_mismatches'])} hash mismatches")
else:
    warn("status-window check of R085 not run (raw logs from the backup needed); 17 ms remains unresolved")

# the measured time base: steady-state median period and the MCU/host rate it implies
ss = raw["steady_state"]
for value, label in [(round(ss["median_poll_period_host_ms"], 1), "steady-state median poll period"),
                     (round(ss["mcu_fast_by_at_least_pct"], 2), "MCU fast by at least (%)")]:
    shown = re.search(rf"(?<![\d.]){re.escape(str(value))}(?![\d])", TEX)
    ok(f"{label} {value} stated") if shown else fail(f"{label} {value} missing from manuscript")
for stale, label in [("0.235", "old clock-rate figure"), ("498.83", "old mean poll period")]:
    fail(f"{label} {stale} still in manuscript") if stale in TEX else ok(f"{label} {stale} removed")

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
        warn("pypdf not installed; PDF checks skipped")
else:
    warn(f"{pdf} not built; PDF checks skipped")

print()
print(f"{len(failures)} failure(s), {len(warnings)} warning(s)")
sys.exit(1 if failures else 0)
