# Cover note to the ICSEC 2026 chairs (draft, paper #1571357468)

Dear Chairs,

Thank you for accepting our paper. Below is how the camera-ready version responds to the reviewers'
comments, with one change to the reported bounds that the reviewers should know about.

**Bounds revised, and the "17 ms" exceedance (Reviewers 2 and 3).** The reviewed version derived the
payload's response time from a single 32-byte frame. The camera-ready version derives the full round trip
from source (poll transmission, the responder's 1 ms loop, response transmission and the controller's next
receive pass; Section III-B). This moves the verified bounds from 605 / 1609 / 506 ms to 603 / 1607 /
516 ms for first timeout, OFFLINE and recovery. The verification batch was re-run and extended (from 254
formulas in fifteen configurations to 368 in twenty-one), and every verdict matches the oracle.
The interval that exceeded the reviewed 506 ms bound by 17 ms (522.8 ms) is now 6.8 ms over the revised
516 ms bound. On-target measurement shows the host's serial reader stamps lines up to 63.8 ms late,
while the MCU-timed recoveries stay within 503.5 ms (Table V). We therefore attribute the remaining excess
to the observation path and still report it as unresolved (Section IV-E).

**Jitter assumption measured (Reviewer 2).** A logic analyzer on the target shows the poll period within
0.57 ms of nominal over 1319 periods, well inside the assumed J = 2 ms. The host-observed slip at status
reports comes from the host's serial reader, not the controller (Sections III-F and IV-D, Table V).

**Narrowing the model–code gap (Reviewer 2).** The unmodified C++ of all three mechanisms was executed on
the host under the model's assumptions and stays within every bound (Section IV-C).

**Hardware tests for the watchdog and boot mechanisms (Reviewer 3).** We added 67 stall injections and
SWD boot-fault injection on the target (Table V). These reproduced the boot defect found by model
checking and its fix, and they exposed a second defect, retained memory not shared between bootloader and
application (F5). F5 is fixed and re-verified on the target (Section IV-B).

**Terms and figures (Reviewer 3).** The technical terms are now defined where they are first used, and
Fig. 1 is drawn at full scale.

Sincerely,
Borworntat Dendumrongkul, on behalf of the authors
