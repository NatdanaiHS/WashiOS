# Next Executable Milestone: F411 Source/Pin/VCP Feasibility

Time-box this milestone to 60 minutes. Perform feasibility only; do not modify or flash experimental firmware and do not begin pair bring-up.

Freshly enumerate all four NUCLEO-F411RE boards and record each ST-LINK serial identity and VCP port. Verify from authoritative Nucleo-F411RE/STM32F411 documentation and the installed PlatformIO `nucleo_f411re` definition that:

- USART2 PA2/PA3 remains dedicated to ST-LINK VCP host control/observation;
- USART1 PA9/PA10 is independently exposed on D8/D2 for the inter-board link;
- crossed PA9/PA10 plus common ground requires three jumper wires per pair and no solder-bridge change; and
- two simultaneous physical pairs can retain four independent VCP observation channels without electrical driver conflict.

Build the existing `genericSTM32F411RE` environment as a toolchain sanity check. Audit the controller, F4 UART/BSP, payload simulator, build environments, and host harness. Produce `research/icsec2026/extension/F411_FEASIBILITY_20260901.md` containing:

- the four-board identity/port table and locked host/link pin map;
- the exact current source gaps for controller and payload roles;
- the smallest file-level implementation plan for explicit standalone `nucleo_f411re` controller and payload environments;
- a semantic-equivalence table covering frame/CRC/sequence behavior, 115200 8N1, 500 ms poll cadence, 100 ms deadline, three-timeout OFFLINE rule, fault activation confirmation, NORMAL restoration, and stabilization;
- required receive-buffer/overflow tests and build/hardware checks; and
- a final `F411_GO` or `F411_NO_GO` decision with elapsed time and concrete reasons.

Declare `F411_GO` only if both roles can be supplied through isolated F4 board/UART implementations, interrupt-driven bounded receive buffers, F4 initialization, explicit build environments, and narrow compile guards while leaving the common protocol, supervision state machine, fault semantics, and evidence gates unchanged.

Declare `F411_NO_GO` and stop if feasibility requires common architectural refactoring, a bootloader port, shared VCP/link UART, solder-bridge changes, polling/blocking receive that changes supervision behavior, or any material semantic change. Preserve the feasibility record and redirect work to manuscript analysis and Friday scope/export preparation. Stop after recording the GO/NO-GO decision; a GO does not authorize Checkpoint 2 in this milestone.
