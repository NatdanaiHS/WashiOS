# Code-level conformance (DRAFT-CAMERA-READY, 2026-10-18)

Addresses Reviewer 2 ("narrow the model–code gap for at least one mechanism") and partly Reviewer 3
("watchdog and boot need more testing") without hardware. Each program compiles the **real, unmodified
firmware headers** with plain `g++` (PlatformIO is not installed on this machine) and checks the model's
properties against the code's behaviour. The firmware tree is only read.

```bash
research/icsec2026/draft-camera-ready/code_conformance/run_all.sh [scale]   # default 5, ~30 s
```

Output goes to `results/<UTC stamp>/` (exclusive), with `provenance.txt` (HEAD commit, compiler, SHA-256 of
every compiled firmware header, the F4 diff stat) and `SHA256SUMS.csv`.

| Program | Real code exercised | What is re-stated (cannot run on host) | Kind of evidence |
|---|---|---|---|
| `payload_link_sim.cpp` | `PayloadLinkController`, `PayloadFrameDecoder`, frame codec, `HostModeCommandParser` | the two RTOS/HAL loops (`PayloadLinkTask::Run`, demo-payload `main`), with blocking UART writes at 115200 8N1, line by line with source citations | randomized discrete-event simulation, 1 µs resolution; **sampled, not exhaustive** |
| `watchdog_gate_sim.cpp` | `TaskHealthRegistry`, `Watchdog`, `WatchdogRunner`, `FaultLog` | heartbeat / payload-link / watchdog task loops, IWDG counter | stall at every 1 ms and 0.25 ms phase over 1 s; randomized wake-up latency |
| `boot_policy_explore.cpp` | `BootPolicy::run()`, `BootMetadata`, `FaultLog`, CRC-32 | flash map, jump, beacon (mocks as in `bootloader/test`) | **exhaustive** breadth-first search of all reachable retained states under the UPPAAL boot environment; one abstraction: pre-boot `boot_count` > 5 clamped to 5 |

## Result of run `results/20261018T075550Z/` (scale 5): all pass

- **Payload link** (287 500 trials, wake-up latency J ≤ 2 ms): measured maxima stay inside the model's
  bounds in every scenario. Without status reports: first timeout ≤ 596.7 ms (bound 603), OFFLINE
  ≤ 1598.6 (1607), recovery ≤ 506.4 (516). With the A7 block (status line + up to 50 ms extra): ≤ 633.1 /
  1640.1 / 529.8 (663 / 1667 / 576). The delay boundary matches the model's predicates: 50–85 ms accepted
  in every trial, 100–250 ms timed out in every trial, 86–99 ms mixed (90 ms: 13 of 7 500 trials time out).
  With the block, 110–159 ms can be accepted, and 160 ms and above always time out. Host-visible recovery
  intervals exceed the internal ones by at most 4.6 ms (finding E3). The status line alone, without the
  extra block, moves no maximum by more than about 3 ms, so the 30 ms median slip seen on hardware is not
  explained by the line's own transmission time (hardware item B2).
- **Watchdog gate** (11 000 runs per task and IWDG extreme, plus 800 runs of 120 s without a stall): W1
  holds (no failure, no reset). W2 holds (no refresh after a recorded failure). W3: detection ≤ 870.7 ms
  (link, bound 952) and ≤ 1586.9 ms (heartbeat, bound 1652). W6: reset within W3 + 2170 ms in every run.
- **Boot policy** (324–528 states per variant): B1, B2, B4, B6, B9 hold on both the pre-fix (HEAD) and the
  fixed (working tree) code. On the **pre-fix code B8 is violated in 4 states, all on the fallback path**
  (finding F4 reproduced in the real C++). With the fix, B3 and B8 hold. At most 4 consecutive Pending
  launches occur. Slot B can become Confirmed only in the design variant (F1). `run_all.sh` fails if any of
  these expectations is lost.

## Run history

- `20261018T075416Z`: **INVALID** for the boot results (vacuous exploration); see
  `results/20261018T075416Z.INVALID.md`.
- `20261018T075512Z`: valid, superseded (ran before the F4/F1 expectation checks were added to `run_all.sh`).
- `20261018T075550Z`: current.

## What this does and does not show

It shows that the C++ that implements the three mechanisms, run under the model's environment assumptions,
stays inside the model's bounds and exhibits the model's findings. It is not a refinement proof, and the
payload and watchdog checks sample rather than enumerate. The task loops are re-stated by hand, and the
J ≤ 2 ms and A7 assumptions carry over from the model. Hardware items B1–B6 remain the only way to check
those assumptions themselves.
