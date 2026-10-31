# ENGDIAG_001 static hypothesis audit

This record is engineering-only (`scientific_observation=false`, `manuscript_use=NONE`). Static inspection does not itself confirm a runtime hypothesis.

The F411 controller's `bsp::Stm32Timing::getSystemTick()` returns `HAL_GetTick()`. The linked FreeRTOS configuration aliases `xPortSysTickHandler` to `SysTick_Handler`, and that FreeRTOS handler advances the RTOS tick without calling `HAL_IncTick()`. The common `PayloadLinkTask` uses `timing.getSystemTick()` for its 500 ms poll and 5 s status schedules, while its 1 ms loop delay uses the FreeRTOS tick. This makes Hypothesis 1 directly plausible and predicts a live scheduler with advancing `xTickCount` but a fixed `uwTick` after scheduler start.

The existing G4 timing adapter already avoids this mismatch by returning `xTaskGetTickCount()` after scheduler start and using `HAL_GetTick()` only before scheduler start. If runtime evidence confirms Hypothesis 1, mirroring that adapter behavior in the F4 timing adapter is the pre-authorized single minimal candidate fix.

Symbols in the exact retained controller ELF:

- `xTickCount`: `0x2000292c`
- `uwTick`: `0x200029f8`
- `pxCurrentTCB`: `0x20002830`
- `uxSchedulerSuspended`: `0x200028a8`

