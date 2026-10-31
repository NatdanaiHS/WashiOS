#!/usr/bin/env bash
# Build and run the code-level conformance checks against the REAL firmware headers.
# Usage: research/icsec2026/draft-camera-ready/code_conformance/run_all.sh [scale]
# Output: research/icsec2026/draft-camera-ready/code_conformance/results/<UTC stamp>/ (exclusive, never reused)
# Needs only g++ (C++17) and git; no PlatformIO, no hardware. The firmware tree is read, never written.
set -euo pipefail

SCALE="${1:-5}"
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../../.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$HERE/results/$STAMP"
mkdir -p "$HERE/results"; mkdir "$OUT"
BUILD="$OUT/build"; mkdir -p "$BUILD/prefix/boot"
CXX="${CXX:-g++}"
CXXFLAGS=(-std=gnu++17 -O2 -Wall -Wextra -Werror)

{
  echo "repo_head $(git -C "$REPO" rev-parse HEAD)"
  echo "compiler $("$CXX" --version | head -1)"
  echo "scale $SCALE"
  echo "-- sha256 of the firmware sources compiled in (working tree):"
  for f in core/include/comms/PayloadLinkController.hpp core/include/comms/PayloadProtocol.hpp \
           demo-payload/src/HostModeCommandParser.hpp bootloader/include/boot/BootPolicy.hpp \
           bootloader/include/boot/BootMetadata.hpp bootloader/include/boot/Crc32.hpp \
           core/include/core/FaultLog.hpp core/include/core/TaskHealth.hpp core/include/core/Watchdog.hpp \
           core/include/core/WatchdogRunner.hpp; do
    echo "$(sha256sum "$REPO/$f" | cut -d' ' -f1)  $f"
  done
  echo "-- working-tree diff of the boot policy against HEAD (the F4 fix):"
  git -C "$REPO" diff --stat HEAD -- bootloader/include/boot/ || true
} > "$OUT/provenance.txt"

# Pre-fix boot policy = HEAD version of the two boot headers (F4 present).
git -C "$REPO" show HEAD:bootloader/include/boot/BootPolicy.hpp > "$BUILD/prefix/boot/BootPolicy.hpp"
git -C "$REPO" show HEAD:bootloader/include/boot/BootMetadata.hpp > "$BUILD/prefix/boot/BootMetadata.hpp"
cp "$REPO/bootloader/include/boot/Crc32.hpp" "$BUILD/prefix/boot/"

cd "$REPO"
"$CXX" "${CXXFLAGS[@]}" -I core/include/comms -I demo-payload/src \
  "$HERE/payload_link_sim.cpp" -o "$BUILD/payload_link_sim"
"$CXX" "${CXXFLAGS[@]}" -DNATIVE -I core/include/core -I core/include/hal \
  "$HERE/watchdog_gate_sim.cpp" -o "$BUILD/watchdog_gate_sim"
"$CXX" "${CXXFLAGS[@]}" -DNATIVE -DWASHIBOOT_ENABLE_TEST_HOOKS -I bootloader/include -I core/include/core \
  "$HERE/boot_policy_explore.cpp" -o "$BUILD/boot_fixed"
"$CXX" "${CXXFLAGS[@]}" -DNATIVE -DWASHIBOOT_ENABLE_TEST_HOOKS -I "$BUILD/prefix" -I bootloader/include \
  -I core/include/core "$HERE/boot_policy_explore.cpp" -o "$BUILD/boot_prefix"

status=0
"$BUILD/payload_link_sim" "$SCALE" > "$OUT/payload_link.txt" || status=1
"$BUILD/watchdog_gate_sim" "$SCALE" > "$OUT/watchdog_gate.txt" || status=1
for v in shipped design; do
  "$BUILD/boot_fixed" "$v" > "$OUT/boot_fixed_$v.txt" || status=1
  # The pre-fix policy is EXPECTED to violate B8 (finding F4); only its safety verdict gates the exit code.
  "$BUILD/boot_prefix" "$v" > "$OUT/boot_prefix_$v.txt" || status=1
done
# F4 must be visible in the pre-fix policy and absent in the fixed one; otherwise the explorer has gone blind.
for v in shipped design; do
  grep -q "LIMIT(B3,B8)=VIOLATED" "$OUT/boot_prefix_$v.txt" || { echo "F4 NOT reproduced on pre-fix ($v)"; status=1; }
  grep -q "B8 Pending launched over the limit: [1-9].*primary path 0)" "$OUT/boot_prefix_$v.txt" || { echo "F4 not fallback-only ($v)"; status=1; }
  grep -q "LIMIT(B3,B8)=HOLD" "$OUT/boot_fixed_$v.txt" || { echo "F4 present after fix ($v)"; status=1; }
done
grep -q "F1 slot B Confirmed reachable: no" "$OUT/boot_fixed_shipped.txt" || { echo "F1 not reproduced"; status=1; }
grep -q "F1 slot B Confirmed reachable: yes" "$OUT/boot_fixed_design.txt" || { echo "design variant cannot confirm"; status=1; }
rm -rf "$BUILD"

( cd "$OUT" && find . -type f ! -name SHA256SUMS.csv -print0 | sort -z | \
  xargs -0 -I{} sh -c 'printf "%s,%s,%s\n" "{}" "$(stat -c %s "{}")" "$(sha256sum "{}" | cut -d" " -f1 | tr a-f A-F)"' ) \
  | sed '1i relative_path,size_bytes,sha256' > "$OUT/SHA256SUMS.csv"
tail -n 3 "$OUT"/*.txt
echo "results in $OUT (exit $status)"
exit $status
