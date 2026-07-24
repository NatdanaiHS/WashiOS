# WashiOS Simulated Payload

Hardware-in-the-loop payload firmware for a NUCLEO-G474RE. It imports the
payload wire protocol directly from `../core`.

## Equipment and wiring

- NUCLEO-G431RB running WashiOS
- NUCLEO-G474RE running this project
- Two Micro-USB cables
- Three male-to-male Dupont wires

| G431 OBC | G474 payload |
| --- | --- |
| D1 / PC4 / USART1_TX | D0 / PC5 / USART1_RX |
| D0 / PC5 / USART1_RX | D1 / PC4 / USART1_TX |
| GND | GND |

Power both boards from their own USB cables. Do not connect their 3V3 or 5V
rails. Make or change signal connections only while both boards are unpowered.

## Build and upload

From the monorepo root, build and flash the OBC side first:

```powershell
.\tools\flash_payload_demo.ps1
```

This builds the G431 OBC core first, then builds and uploads WashiBoot with the
provisioned CRC, then uploads the OBC application.

Finally flash the payload responder:

```powershell
.\tools\build_payload_responder.ps1
.\tools\flash_payload_responder.ps1
```

Manual payload responder commands:

```powershell
cd demo-payload
pio run -e nucleo_g474re
pio run -e nucleo_g474re -t upload
```

Flash one ST-LINK board at a time to avoid selecting the wrong probe.

## Fault modes

Press the G474 user button to cycle:

```text
NORMAL -> SILENT -> BAD_CRC -> DELAYED -> NORMAL
```

- NORMAL returns valid telemetry.
- SILENT receives polls but sends no response.
- BAD_CRC corrupts the response CRC.
- DELAYED waits 250 ms, exceeding the OBC's 100 ms deadline.

The G474 user LED toggles for every valid poll request.

## Monitors

With both boards connected, identify their COM ports and open two terminals:

```powershell
pio device list
pio device monitor -p COM_OBC -b 115200
pio device monitor -p COM_PAYLOAD -b 115200
```

The OBC must continue its heartbeat while the payload is silent, corrupt, late,
or disconnected. Returning the payload to NORMAL must produce
`PAYLOAD_RECOVERED` without resetting the OBC.

The consoles intentionally log transitions instead of every 500 ms poll. In
NORMAL, use the OBC's five-second `PAYLOAD_STATUS` line and verify that `ok`
keeps increasing. In SILENT, the OBC logs timeout 1, timeout 2, and one
`PAYLOAD_OFFLINE` transition; it continues polling silently so that recovery is
automatic. The payload console logs only READY, LINK_ACTIVE, mode changes, and
errors.

Record at least ten NORMAL responses, then test SILENT, BAD_CRC, DELAYED,
physical TX disconnection, and recovery. Use `docs/experiment-results.md` to
capture the evidence and limitations honestly.
