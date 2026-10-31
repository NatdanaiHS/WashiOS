// Queries for watchdog_gating.xml. SCENARIO_SELECT patched by run_verifyta.sh.
// Bounds are inclusive; bounded-response queries use '>' and tightness queries ('T') use '>='
// and are EXPECTED NOT SATISFIED. See formal/EXPECTED_VERDICTS.md.

// Q0 sanity
A[] not deadlock

// W1 (expected SATISFIED in SCENARIO 0, NOT satisfied in SCENARIO 1) a healthy system is never reset and never logs a critical failure
A[] not resetHappened
A[] not criticalFailed

// W2 no hardware refresh is issued after a critical failure is recorded
A[] not refreshedAfterFailure

// W3 a stalled critical task is detected no later than deadline + watchdog poll + task delay + jitter
//    Heartbeat: 1500 + 152 ; PayloadLink: 800 + 152 (inclusive)
A[] (stalled[0] && since[0] > DEADLINE[0] + WD_POLL_MS + WD_TASK_MS + JITTER_MS) imply criticalFailed
A[] (stalled[1] && since[1] > DEADLINE[1] + WD_POLL_MS + WD_TASK_MS + JITTER_MS) imply criticalFailed
// W3T tightness (expected NOT satisfied in SCENARIO 1)
A[] (stalled[1] && since[1] >= DEADLINE[1] + WD_POLL_MS + WD_TASK_MS + JITTER_MS) imply criticalFailed

// W5 a stall inevitably leads to reset (leads-to; vacuous in SCENARIO 0)
E.Injected --> resetHappened

// W6 end-to-end stall-to-reset bound: detection bound + IWDG maximum period (inclusive)
A[] (stalled[1] && since[1] > DEADLINE[1] + WD_POLL_MS + WD_TASK_MS + JITTER_MS + IWDG_MAX_MS) imply resetHappened
A[] (stalled[0] && since[0] > DEADLINE[0] + WD_POLL_MS + WD_TASK_MS + JITTER_MS + IWDG_MAX_MS) imply resetHappened

// W7 the reset never fires before a critical failure is recorded (no spurious reset in either scenario)
A[] resetHappened imply criticalFailed
