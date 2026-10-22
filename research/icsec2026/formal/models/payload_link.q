// Queries for payload_link.xml. One TCTL formula per non-comment line.
// Run per configuration by tooling/run_verifyta.sh (FAULT_SELECT, DELAY_MS patched).
// Bounds and boundary predicates are declared in the model. Bounds are inclusive, so the
// bounded-response queries use '>' and the tightness queries ('T' suffix) use '>=' and are
// EXPECTED NOT SATISFIED. See formal/EXPECTED_VERDICTS.md for the per-configuration expectation.
// TIMES_OUT_MODE := SILENT || BAD_CRC || (DELAYED && TIMES_OUT).

// Q0 sanity
A[] not deadlock

// Q1 no false OFFLINE under a lossless nominal channel once the link is up
A[] (H.Nominal && H.zn >= 2 * POLL_MS) imply link != OFFLINE

// Q2 first-timeout bound after confirmed fault onset (605 ms inclusive)
A[] (H.Faulted && (mode == SILENT || mode == BAD_CRC || (mode == DELAYED && TIMES_OUT)) && H.z > FIRST_TIMEOUT_BOUND_MS) imply toutInFault >= 1
// Q2T tightness (expected NOT satisfied for TIMES_OUT_MODE): the timeout may occur exactly at the bound
A[] (H.Faulted && (mode == SILENT || mode == BAD_CRC || (mode == DELAYED && TIMES_OUT)) && H.z >= FIRST_TIMEOUT_BOUND_MS) imply toutInFault >= 1

// Q3 OFFLINE bound after confirmed fault onset (1609 ms inclusive)
A[] (H.Faulted && (mode == SILENT || mode == BAD_CRC || (mode == DELAYED && TIMES_OUT)) && H.z > OFFLINE_BOUND_MS) imply link == OFFLINE
// Q3T tightness (expected NOT satisfied for TIMES_OUT_MODE)
A[] (H.Faulted && (mode == SILENT || mode == BAD_CRC || (mode == DELAYED && TIMES_OUT)) && H.z >= OFFLINE_BOUND_MS) imply link == OFFLINE

// Q4 recovery bound after confirmed restoration (506 ms inclusive)
A[] (H.Restored && H.zr > RECOVERY_BOUND_MS) imply link == ONLINE
// Q4T tightness (expected NOT satisfied when the link was OFFLINE before restoration)
A[] (H.Restored && H.zr >= RECOVERY_BOUND_MS) imply link == ONLINE

// Q5 restoration eventually recovers (leads-to)
H.Restored --> link == ONLINE

// Q6 OFFLINE is entered only at the consecutive-timeout threshold
A[] (link == OFFLINE) imply consecutive >= OFFLINE_N

// Q7 (BAD_CRC) a CRC reject precedes the first timeout of the exposure
A[] (mode == BAD_CRC && toutInFault >= 1) imply crcInFault

// Q8 (BAD_CRC) CRC rejection alone never changes link state
A[] (mode == BAD_CRC && toutInFault == 0) imply link == ONLINE

// Q9a (DELAYED, ACCEPTS) below the boundary no timeout is ever counted
A[] (mode == DELAYED && ACCEPTS) imply toutInFault == 0

// Q9b (DELAYED, TIMES_OUT) at or above the boundary every late frame is sequence-rejected
A[] (mode == DELAYED && TIMES_OUT && H.Faulted && H.z > LATE_FRAME_BOUND_MS) imply seqInFault

// Q9c (DELAYED, undetermined band) both outcomes are reachable: a timeout, and a long exposure with none.
//     Expected SATISFIED only for DELAY_MS in the undetermined band (e.g. 100); NOT satisfied otherwise.
E<> (mode == DELAYED && !ACCEPTS && !TIMES_OUT && toutInFault >= 1)
E<> (mode == DELAYED && !ACCEPTS && !TIMES_OUT && H.Faulted && H.z > 2 * FIRST_TIMEOUT_BOUND_MS && toutInFault == 0)

// Q10 (SILENT) nothing is ever received during a SILENT exposure
A[] (mode == SILENT && H.Faulted) imply (!crcInFault && !seqInFault)

// Q11 progress (deadlock freedom made explicit): every outstanding poll is resolved by a response
//     or a timeout, and the controller always polls again
C.Awaiting --> C.Idle
C.Idle --> C.Awaiting
