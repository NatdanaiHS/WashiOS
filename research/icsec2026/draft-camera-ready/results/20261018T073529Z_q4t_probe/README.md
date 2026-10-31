# Q4T tightness probe (2026-10-18)

Run after `../20261018T073529Z/` reported Q4T satisfied for `payload_delayed_90` and
`payload_delayed_90_status` (oracle predicted NOT satisfied). Each `.q` holds
`A[] (H.Restored && H.zr >= X) imply link == ONLINE` for X = 500..520 and 560..580, against the
instantiated models retained in `../20261018T073529Z/`.

Result: `payload_silent` fails up to X = 516 and holds from 517 (bound 516 attained, as designed).
`payload_delayed_90` fails up to 513 and holds from 514; `payload_delayed_90_status` fails up to 573 and
holds from 574. In the d = 90 band the link is OFFLINE at restoration only if the delayed response
arrived after the earliest deadline check (100 ms), so the request was decoded later than
100 - 90 - DELAY_EXTRA(1) - RESP_MAX(4) = 5 ms after its poll; restoration can come no earlier than that
decode, so the worst case is 516 - (5 - DECODE_MIN(2)) = 513 ms (+60 with the status block). The inclusive
bound Q4 holds; it is tight only in the timeout-mode configurations.
