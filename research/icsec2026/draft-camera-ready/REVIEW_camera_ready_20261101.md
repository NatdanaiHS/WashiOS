# Pre-submission check: camera-ready manuscript (2026-11-01)

Reviewed: `draft-camera-ready/manuscript/build/main.pdf` (6 pages, built 2026-11-01) against the ICSEC
2026 reviews in `submission/EMAIL_REVIEW.md`. Deadline 2026-11-05 (IEEE PDF eXpress).

## Rejection and embarrassment risks, ranked

### 1. The bounds changed after acceptance, and the paper never connects this to the reviewers' "17 ms"

**What.** The reviewed version stated a first-timeout bound of 605 ms, OFFLINE 1609 ms and recovery 506 ms
(`submission/main.tex`). The camera-ready states 603, 1607 and 516 ms. Reviewers 2 and 3 both asked about
"the unresolved 17 ms difference" (522.8 ms against 506 ms). The camera-ready now reports the same interval
as "522.8 ms against 516 ms, is 6.8 ms over" (§IV-E).
**Where.** Abstract; Table III; §IV-E, second paragraph.
**So what.** A reviewer or chair checking the revision will search for 17 ms and not find it. They will see
the excess shrink because the bound grew by 10 ms, which reads as moving the goalposts. The reason is sound:
the round trip is now derived from source (§III-B) instead of covering one frame. But the paper does not
say the bound was revised.
**Fix.** Say it in the cover note to the chairs: the recovery bound grew from 506 to 516 ms after the round
trip was re-derived, and the 17 ms excess is now 6.8 ms and attributed to the serial reader (Table V). If
a line can be freed, add a clause in §IV-E: "(17 ms over the reviewed version's 506 ms bound, whose round
trip covered one frame)".

### 2. "Pre-declared oracle" is not quite true

**What.** The abstract says "every verdict matches a pre-declared oracle", and §IV-A and the Conclusion
repeat it. §IV-A then says the DELAYED 90 recovery result was "contrary to our oracle, which was corrected
with the reason recorded". `EXPECTED_VERDICTS.md` confirms the DELAYED 90 rows were "corrected after the
run".
**So what.** For 2 of the 21 configurations the oracle was declared after the run. The disclosure is
there, but the headline claim ignores it. That is easy to catch and costly to explain afterward.
**Fix (same length).** In the abstract and Conclusion write "matches the verdict oracle (one prediction
corrected, with the reason recorded)", or drop "pre-declared". Keep the §IV-A sentence.

### 3. F5 lost its causal mechanism in today's trim (my edit)

**What.** §IV-B now reads: "the application its fault log at 0x20000088, above initialized data from
0x20000000". The earlier wording said the application's initialized data covered 0x20000000–0x20000088.
That range overlaps both bootloader objects (0x20000018 and 0x20000050), and the overlap is what explains
"a Pending slot's boot count restarted whenever the application ran".
**So what.** As written, a reader can see why the bootloader found no fault (it read a different address),
but not why the boot count reset.
**Fix (shorter than now).** "the application its fault log at 0x20000088 and initialized data over both."

### 4. Table V lets a reader derive an IWDG period below the model's minimum

**What.** Table V gives stall-to-expiry of 801.4–801.8 ms and stall-to-reset of 2675.3–2676.1 ms for the
link task. So expiry-to-reset is about 1874 ms (2675.3 − 801.4 = 1873.9). The model's IWDG bracket starts
at 1882 ms (Table I, §III-C).
**Where.** §IV-D answers this only in its last sentence: "Stall-to-reset times include one IWDG period from
the last refresh, before the recorded expiry."
**So what.** The explanation is correct but terse. The supervisor refreshes at each 100 ms evaluation, so
the last refresh comes before the recorded expiry. However, the refresh instant is not probed (B3 records
only stall, record and reset), so the IWDG period itself was never measured. Reviewer 2 asked for measured
assumptions.
**Fix.** State the number and the reason: "expiry to reset is 1874 ms; the IWDG period starts at the last
refresh, an evaluation up to 100 ms earlier, which was not probed". Also add the IWDG period to §V-A's
list of unmeasured quantities.

### 5. No link to the released artifact

**What.** §V-B says the artifact "is released with this paper", but gives no URL, DOI or contact.
**So what.** In the review copy, "on acceptance" was enough. In the published version the claim cannot be
checked.
**Fix.** Add the repository or archive URL, or change the wording to "available from the authors".

### 6. The R085 attribution rests on 5 comparable trials

**What.** §IV-E: "MCU-timed recoveries stay within 503.5 ms (Table V), so we attribute the excess to the
observation path". Table V's 15 MCU-timed trials are 5 SILENT, 5 BAD_CRC and 5 DELAYED
(`runs/labB6_g431_f411_s20261101/results.csv`), with an F411 payload. R085 was a BAD_CRC trial with the
G474 payload.
**So what.** The measured reader lag (up to 63.8 ms) carries the argument; the MCU-timed recoveries are
weaker support. The text hedges ("we attribute", "reported as unresolved"), so this is a loose end, not a
flaw.
**Fix (optional).** "(15 trials, 5 BAD\_CRC)".

## Fits the time left (four days)

Items 2, 3 and 5 are wording changes that keep the page count. Item 1 belongs in the cover note, plus the
clause only if a line frees up. Item 4 is one sentence that needs a line from elsewhere. Item 6 is
optional. Rebuild and re-run the checker after each change, since page 6 is full.

## Already strong (do not cut)

- The on-target evidence directly answers both substantive reviewer requests. Reviewer 2: J is measured
  (poll period within 0.57 ms of nominal) and the slip is traced to the reader. Reviewer 3: there are now 67
  stall injections and SWD boot-fault injection (Table I, Table V).
- F5 is reported plainly as a defect the models assume away, with its fix and re-verification. §V-A turns
  it into a limitation statement instead of hiding it.
- §V-A states the important deviations: the substitute F411 payload, the single stall phase and cold
  starts emulated over SWD.
- Code-level conformance (§IV-C) answers Reviewer 2's request to narrow the model–code gap.

## Checked and clean

- 6 pages; every font embedded and subset (`pdffonts`). Still run IEEE PDF eXpress; it was not tested here.
- "pinned to a tagged internal revision" is true: commit `cf8fa9b` carries tag `icsec-2026-submission-final`.
- Every Table V cell matches the lab runs (now enforced by `verify_manuscript.py`). The Section and Table
  cross-references resolve.
- Arithmetic: 2 / 0.57 ≈ 3.5, so "more than threefold" holds. The Q9 band edges follow from 98 + J + S with
  J = 2 and S ∈ {0, 60}.

Not checked: the UPPAAL models themselves and the proofs behind the closed-form bounds, beyond the oracle
match the checker enforces.
