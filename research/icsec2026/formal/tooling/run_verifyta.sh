#!/usr/bin/env bash
# Run every model/query configuration with UPPAAL verifyta and retain outputs with hashes.
# Usage: research/icsec2026/formal/tooling/run_verifyta.sh [path-to-verifyta]
# Output: research/icsec2026/formal/results/<UTC timestamp>/ (never overwrites).
set -euo pipefail

VERIFYTA="${1:-${VERIFYTA:-/opt/uppaal/bin/verifyta}}"
FORMAL="$(cd "$(dirname "$0")/.." && pwd)"
MODELS="$FORMAL/models"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$FORMAL/results/$STAMP"
mkdir -p "$FORMAL/results"; mkdir "$OUT"   # exclusive: fails if the directory exists

command -v "$VERIFYTA" >/dev/null || { echo "verifyta not found: $VERIFYTA" >&2; exit 2; }
"$VERIFYTA" -v 2>&1 | head -1 | tee "$OUT/verifyta_version.txt"

run() {  # name model.xml queries.q sed-expr
  local name="$1" model="$2" queries="$3" patch="$4"
  local inst="$OUT/$name.xml"
  sed -e "$patch" "$model" > "$inst"
  echo "== $name"
  # -u: summary, -s: state-space stats, -t0: no trace (deterministic text); -q suppresses copyright
  "$VERIFYTA" -u -s -q "$inst" "$queries" > "$OUT/$name.out" 2> "$OUT/$name.err" || echo "verifyta exit $? for $name" | tee -a "$OUT/$name.err"
  { echo "== $name"; grep -E "Formula is|Verifying formula|-- Property" "$OUT/$name.out" || true; } >> "$OUT/SUMMARY.txt"
}

# Payload link: one Host per fault mode; DELAYED swept over the frozen sweep values.
run payload_silent   "$MODELS/payload_link.xml" "$MODELS/payload_link.q" 's/FAULT_SELECT/SILENT/'
run payload_badcrc   "$MODELS/payload_link.xml" "$MODELS/payload_link.q" 's/FAULT_SELECT/BAD_CRC/'
for d in 50 90 100 110 250; do
  run "payload_delayed_$d" "$MODELS/payload_link.xml" "$MODELS/payload_link.q" \
      "s/FAULT_SELECT/DELAYED/; s/const int DELAY_MS = 250;/const int DELAY_MS = $d;/"
done

# Jitter sensitivity for the delay-acceptance boundary (assumption A1). DELAY_MS is held at the
# boundary value 100 ms and JITTER_MS is swept; see formal/EXPECTED_VERDICTS.md.
for j in 0 1 5; do
  run "payload_delayed_100_j$j" "$MODELS/payload_link.xml" "$MODELS/payload_link.q" \
      "s/FAULT_SELECT/DELAYED/; s/const int DELAY_MS = 250;/const int DELAY_MS = 100;/; s/JITTER_MS *= 2;/JITTER_MS    = $j;/"
done

# Watchdog gating: no-stall and one-stall scenarios.
run watchdog_nostall "$MODELS/watchdog_gating.xml" "$MODELS/watchdog_gating.q" 's/SCENARIO_SELECT/0/'
run watchdog_stall   "$MODELS/watchdog_gating.xml" "$MODELS/watchdog_gating.q" 's/SCENARIO_SELECT/1/'

# Boot policy: shipped application (never confirms) and design intent (confirms).
run boot_shipped     "$MODELS/boot_policy.xml" "$MODELS/boot_policy.q" 's/APP_CONFIRMS_SELECT/0/; s/FALLBACK_RESETS_SELECT/0/'
run boot_design      "$MODELS/boot_policy.xml" "$MODELS/boot_policy.q" 's/APP_CONFIRMS_SELECT/1/; s/FALLBACK_RESETS_SELECT/0/'
# F4 fix: resetBootAttempts() on fallback activation. B8 is expected to hold here.
run boot_f4fix       "$MODELS/boot_policy.xml" "$MODELS/boot_policy.q" 's/APP_CONFIRMS_SELECT/0/; s/FALLBACK_RESETS_SELECT/1/'

# Inventory
( cd "$OUT" && find . -type f ! -name SHA256SUMS.csv -print0 | sort -z | \
  xargs -0 -I{} sh -c 'printf "%s,%s,%s\n" "{}" "$(stat -c %s "{}")" "$(sha256sum "{}" | cut -d" " -f1 | tr a-f A-F)"' ) \
  | sed '1i relative_path,size_bytes,sha256' > "$OUT/SHA256SUMS.csv"
echo "results in $OUT"
