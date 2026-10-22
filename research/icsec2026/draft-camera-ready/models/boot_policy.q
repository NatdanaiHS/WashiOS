// Queries for boot_policy.xml. APP_CONFIRMS_SELECT patched by run_verifyta.sh.
// See formal/EXPECTED_VERDICTS.md (B7 and B7r differ between the two configurations; B8 is a finding).

// Q0 sanity
A[] not deadlock

// B1 the policy never launches an image whose vector table or CRC failed validation
A[] not launchedInvalid

// B2 the policy never launches from a slot whose state is Empty or Bad
A[] B.AppRunning imply (stateOf(launchedSlot) == VALID || stateOf(launchedSlot) == PENDING || stateOf(launchedSlot) == CONFIRMED)

// B3 a Pending slot is launched at most MAX_UNCONFIRMED + 1 times in a row before the safe loop
A[] pendingLaunches <= MAX_UNCONFIRMED + 1

// B4 if neither image validates when the bootloader starts, the safe loop is inevitable
(B.Start && !imageOkA && !imageOkB) --> B.SafeLoop

// B5 safe loop is reachable and is recorded
E<> B.SafeLoop
A[] B.SafeLoop imply safeLoop

// B6 (finding F2) after a retained critical fault the application is never relaunched without a cold start
A[] (retainedCriticalFault && B.AppRunning) imply false

// B7 (finding F1) a Pending slot never becomes Confirmed with the shipped application
//    Expected: SATISFIED for APP_CONFIRMS_SELECT = 0, NOT satisfied for 1
A[] not (stateB == CONFIRMED)
// B7r reachability of confirmation in the design variant (expected NOT satisfied for 0, SATISFIED for 1)
E<> (stateB == CONFIRMED)

// B8 (finding F4) the unconfirmed-boot limit is never bypassed
//    Expected NOT satisfied: the limit is checked on the active slot only (BootPolicy.hpp:64-67,126-131),
//    so a fallback into a Pending slot can launch it although bootCount already exceeds the limit.
A[] not launchedOverLimit
// B8b an over-limit launch never happens on the primary path (expected SATISFIED): only the fallback bypasses the check
A[] not overLimitNonFallback
// B8c after an over-limit fallback launch, the very next warm boot is refused unless the application
//     confirmed the slot (expected SATISFIED for APP_CONFIRMS 0; NOT satisfied for 1, where confirmation resets the count)
A[] (lastLaunchOverLimit && B.Recovered) imply (stateOf(active) == PENDING && bootCount > MAX_UNCONFIRMED)

// B9 progress: every reset runs the policy to completion, launching the application or entering the safe loop
B.Start --> (B.AppRunning || B.SafeLoop)
