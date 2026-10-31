# WashiOS Payload HIL Experiment Record

Date:

Operator:

WashiOS commit:

WashiBoot commit:

Payload commit:

## Results

| Scenario | Expected result | Observed result | Pass/Fail | Evidence |
| --- | --- | --- | --- | --- |
| NORMAL, 10 polls | 10 valid responses | | | |
| SILENT | Offline after 3 timeouts; heartbeat continues | | | |
| BAD_CRC | CRC frame rejected | | | |
| DELAYED | Timeout and stale sequence rejected | | | |
| Payload TX disconnected | OBC remains alive for 10 seconds | | | |
| Return to NORMAL | Recovery within one poll cycle, no reset | | | |

## Timing and counters

Fault detection time:

Recovery time:

Valid response count:

Timeout count:

CRC reject count:

Sequence reject count:

## Known limitations

- Payload values are simulated, not physical sensor measurements.
- UART is polling-based; DMA/interrupt reception is future work.
- This is a hardware integration milestone, not flight qualification.
- No radiation, vibration, thermal-vacuum, or long-duration test is claimed.
