# WashiOS Stage 2 Compliance Checklist

Status date: 2026-06-05

## Stage 2 Final Status

Stage 2 is **100% Completed**.

| Task | Requirement | Status | Evidence |
|---|---|---:|---|
| 3.6.1 | Structure-wide CRC-32 data integrity for `FaultLog` retained state | Complete | `FaultLog` commits CRC-32 on `record()` and retained-state initialization; recovery validates magic signature, then CRC-32, then structural bounds before accepting retained data. |
| 3.6.2 | Neutralize data race in `healthSummaryMask()` | Complete | `healthSummaryMask()` evaluation loop is bracketed with `taskENTER_CRITICAL()` / `taskEXIT_CRITICAL()`. |
| 3.6.3 | Target macro verification and Git synchronization | Complete | STM32G4 UART RX-ready macro selection prefers `UART_FLAG_RXNE_RXFNE` and falls back to `UART_FLAG_RXNE`; native SITL and all firmware target builds passed. |

## Verification

| Pipeline | Result |
|---|---:|
| `pio test -e native` | 19/19 SITL tests passed |
| `pio run -e genericSTM32F411RE` | Passed |
| `pio run -e nucleo_g431rb` | Passed |
| `pio run -e nucleo_g431rb_stress` | Passed |
| `pio run -e raspberrypi_pico` | Passed |
| `pio run -e esp32_dev` | Passed |

Runtime dynamic heap profile remains **0 bytes** for WashiOS-controlled flight code.
