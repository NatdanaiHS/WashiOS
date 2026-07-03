# WashiBoot Flight Provisioning Notes

## Bootloader Protection Policy

WashiBoot is the recovery root for the A/B application slots. The flight
configuration shall not allow the running application to rewrite the
bootloader region.

Required flight-unit controls:

- Program WashiBoot into the protected bootloader flash region at `0x08000000`.
- Enable STM32 flash write protection for the bootloader pages before flight.
- Keep a factory recovery path available on engineering units through SWD or
  the STM32 ROM bootloader.
- Treat application-side bootloader CRC checks as read-only health monitoring.
  A mismatch shall be reported through retained fault telemetry; it shall not
  trigger in-field bootloader rewriting.

## A/B Slot Progress Model

The current milestone keeps the existing CRC-based integrity model and extends
it to deterministic A/B selection:

- Slot A starts at `0x08004000`.
- Slot B starts at `0x08012000`.
- WashiOS now has separate G431 linker targets for Slot A and Slot B.
- `BootMetadata` uses `WASHIOS_MAGIC_SIGNATURE` and a structure checksum.
- Legacy single-image metadata is migrated into the current A/B metadata shape.
- If the active slot fails state, vector, or CRC validation, WashiBoot attempts
  the fallback slot.
- If no slot is valid, WashiBoot records `SafeFail` and enters the beacon safe
  loop.

Signed firmware, anti-rollback counters, and golden rescue images are deferred
to the next security milestone.
