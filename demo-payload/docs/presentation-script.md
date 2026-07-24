# Friday HIL Demo Script

## Claim

WashiOS has reached a hardware-in-the-loop subsystem integration milestone. It
is not being presented as a flight-qualified operating system.

## 10-15 minute flow

1. Explain the previous limitation: software tasks and SITL existed, but there
   was no independently running hardware payload.
2. Show the G431 OBC, G474 payload, crossed UART wiring, and separate USB debug
   terminals.
3. Leave the payload in NORMAL and show the `ok` counter increase by at least
   ten valid telemetry responses across the periodic status lines.
4. Press the payload button once for SILENT. Show three timeouts, OFFLINE, and
   the G431 heartbeat continuing.
5. Press again for BAD_CRC. Show CRC rejection rather than telemetry acceptance.
6. Press again for DELAYED. Show timeout/stale-sequence rejection.
7. Press again for NORMAL. Show RECOVERED without resetting the OBC.
8. End with the native test result and the experiment record.

## Honest limitations

- The sensor value is simulated.
- UART receive is interrupt-driven with a fixed 128-byte ring buffer, but does
  not yet use DMA.
- The protocol is deterministic and CRC-protected but is not CCSDS.
- Radiation, vibration, thermal-vacuum, and long-duration qualification remain
  future work.

## Next engineering step

Turn this demonstration into a repeatable HIL test fixture with captured logs,
automated fault injection, DMA reception, and a requirements-to-test trace.
