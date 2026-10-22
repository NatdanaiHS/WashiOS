#!/usr/bin/env python3
"""Verify the formal-verification manuscript against its retained evidence.

Replaces research/icsec2026/paper/verify_candidate.py, which asserted the archived confirmation-gated
manuscript. Every number the manuscript states must be reproducible from a retained artifact:

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

import csv
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
FORMAL = ROOT / "research/icsec2026/formal"
SUBMISSION = ROOT / "research/icsec2026/submission"
TEX_RAW = (SUBMISSION / "main.tex").read_text(encoding="utf-8")
BIB = (SUBMISSION / "references.bib").read_text(encoding="utf-8")

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

WORD_NUMBERS = {11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen", 15: "fifteen"}

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
result_dirs = sorted(p for p in (FORMAL / "results").iterdir() if p.is_dir())
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
    proc = subprocess.run([sys.executable, str(FORMAL / "tooling/check_verdicts.py"), str(results)],
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

    for cfg, label in [("payload_silent", "SILENT"), ("payload_badcrc", r"BAD\\_CRC"),
                       ("payload_delayed_100", "DELAYED 100"), ("watchdog_nostall", "no stall"),
                       ("watchdog_stall", "one stall"), ("boot_shipped", "shipped app"),
                       ("boot_design", "design variant")]:
        n = states(results, cfg)
        row = re.search(rf"{label} & ([\d\\,]+) &", TEX)
        quoted = int(row.group(1).replace("\\,", "").replace(",", "")) if row else None
        ok(f"state count {label}: {n}") if quoted == n else fail(
            f"state count {label}: manuscript {quoted} != retained {n}")

    # jitter-sensitivity configurations, quoted as a pair and a single value
    j0, j1, j5 = (states(results, f"payload_delayed_100_j{j}") for j in (0, 1, 5))
    pair = re.search(r"DELAYED 100, \$J\{\\in\}\\\{0,1\\\}\$ & ([\d, ]+) &", TEX)
    quoted_pair = {int(x) for x in re.findall(r"\d+", pair.group(1))} if pair else set()
    ok(f"jitter sweep state counts {{{j0}, {j1}}}") if quoted_pair == {j0, j1} else fail(
        f"jitter sweep J in {{0,1}}: manuscript {sorted(quoted_pair)} != retained {sorted({j0, j1})}")
    row5 = re.search(r"DELAYED 100, \$J\{=\}5\$ & ([\d\\,]+) &", TEX)
    quoted5 = int(row5.group(1).replace("\\,", "").replace(",", "")) if row5 else None
    ok(f"jitter sweep state count J=5: {j5}") if quoted5 == j5 else fail(
        f"jitter sweep J=5: manuscript {quoted5} != retained {j5}")

    biggest = max(states(results, n) for n in outs)
    if re.search(rf"largest state space is {biggest // 1000}\\,{biggest % 1000:03d}", TEX):
        ok(f"largest state space {biggest} stated")
    else:
        fail(f"largest state space {biggest} not stated")

# 4. bounds from the model constants ---------------------------------------------------------------
model = (FORMAL / "models/payload_link.xml").read_text(encoding="utf-8")
consts = {k: int(v) for k, v in re.findall(r"const int (\w+_MS)\s*=\s*(\d+);", model)}
first = consts["POLL_MS"] + consts["JITTER_MS"] + consts["DEADLINE_MS"] + consts["LOOP_MS"] + consts["JITTER_MS"]
offline = 3 * (consts["POLL_MS"] + consts["JITTER_MS"]) + consts["DEADLINE_MS"] + consts["LOOP_MS"] + consts["JITTER_MS"]
recovery = consts["POLL_MS"] + consts["JITTER_MS"] + consts["TX_MAX_MS"]
for value, name in [(first, "first-timeout"), (offline, "OFFLINE"), (recovery, "recovery")]:
    ok(f"{name} bound {value} ms appears in manuscript") if re.search(rf"\b{value}\b", TEX) else fail(
        f"{name} bound {value} ms missing from manuscript")
wd = (FORMAL / "models/watchdog_gating.xml").read_text(encoding="utf-8")
dl = [int(x) for x in re.search(r"DEADLINE\[2\]\s*=\s*\{\s*(\d+),\s*(\d+)\s*\}", wd).groups()]
slack = sum(int(re.search(rf"{k}\s*=\s*(\d+)", wd).group(1)) for k in ("WD_POLL_MS", "WD_TASK_MS", "JITTER_MS"))
for d in dl:
    ok(f"stall detection bound {d + slack} ms appears") if str(d + slack) in TEX else fail(
        f"stall detection bound {d + slack} ms missing")
# the sensitivity claim: the first-timeout bound as a function of J
if re.search(r"601\{?\+?\}?2J|601\+2J", TEX.replace(" ", "")):
    ok("jitter-parameterised bound 601+2J stated")
else:
    fail("jitter-parameterised bound 601+2J not stated")

# 5. conformance report ----------------------------------------------------------------------------
report_path = FORMAL / "conformance/results/conformance_report.json"
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
bc, disagree = prim["bound_check"], prim["clock_disagreement_ms"]
for value, label in [(bc["within_bound"], "within-bound count"), (bc["intervals"], "interval count"),
                     (disagree["max"], "clock disagreement max"), (disagree["median"], "clock disagreement median"),
                     (prim["bounds_ms"]["falsification_floor"], "falsification floor")]:
    exact = str(value) if not float(value).is_integer() else str(int(value))
    forms = {exact, str(round(float(value), 1)), str(int(round(float(value))))}
    shown = next((f for f in forms if f in TEX), None)
    ok(f"{label} {exact} stated as {shown}") if shown else fail(
        f"{label} {exact} missing from manuscript (accepted forms {sorted(forms)})")
if bc["unresolved"] == 1 and str(round(prim["unresolved_intervals"][0]["excess_ms"])) in TEX:
    ok(f"unresolved interval reported ({prim['unresolved_intervals'][0]['run_id']}, "
       f"{prim['unresolved_intervals'][0]['excess_ms']} ms excess)")
else:
    fail(f"unresolved interval count {bc['unresolved']} not reflected in the manuscript")

# the measured time base must be quoted as the report computes it
tb = report["timebase"]
long_window = tb["windows"]["observation_605s"]
for value, label in [(long_window["mean_poll_period_ms"], "measured mean poll period"),
                     (long_window["polls"], "poll count of the long window"),
                     (tb["host_shorter_by_pct"], "MCU/host rate difference (%)")]:
    # Rounded forms are accepted, but only ones that still carry the value's
    # information. Dropping every significant digit (0.235 -> "0") matched any
    # text in the manuscript and let a wrong figure through, so such degenerate
    # forms are excluded and each candidate must match as a whole number token.
    forms = {f for f in (str(value), str(round(float(value), 2)),
                         str(int(round(float(value)))))
             if float(f) != 0 or float(value) == 0}
    shown = next((f for f in sorted(forms, key=len, reverse=True)
                  if re.search(rf"(?<![\d.]){re.escape(f)}(?![\d])", TEX)), None)
    ok(f"{label} {value} stated as {shown}") if shown else fail(
        f"{label} {value} missing from manuscript (accepted {sorted(forms)})")

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
ok("one canonical manuscript source") if list(SUBMISSION.glob("main*.tex")) == [SUBMISSION / "main.tex"] else fail(
    "multiple main*.tex sources in submission/")
pending = [m for m in re.findall(r"\\pending\{([^}]*)\}", TEX) if m]
fail(f"{len(pending)} \\pending markers remain: {pending}") if pending else ok("no \\pending markers")

# 8. optional PDF checks ---------------------------------------------------------------------------
pdf = SUBMISSION / "build" / "main.pdf"
if pdf.exists():
    try:
        from pypdf import PdfReader  # type: ignore
        reader = PdfReader(str(pdf))
        pages = len(reader.pages)
        text = "".join((pg.extract_text() or "") for pg in reader.pages).lower()
        ok(f"PDF page count {pages}") if 4 <= pages <= 6 else fail(f"PDF page count {pages} outside 4-6")
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
    warn("submission/build/main.pdf not built; PDF checks skipped")

print()
print(f"{len(failures)} failure(s), {len(warnings)} warning(s)")
sys.exit(1 if failures else 0)
