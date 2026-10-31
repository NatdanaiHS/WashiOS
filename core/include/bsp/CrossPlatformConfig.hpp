#pragma once

#if defined(STM32G431xx) && defined(__GNUC__)
/* Shared with WashiBoot at a fixed address; see the .retained section in the linker scripts. */
#define WASHIOS_RETAINED __attribute__((section(".retained.fault_log"), aligned(8)))
#else
#define WASHIOS_RETAINED
#endif
