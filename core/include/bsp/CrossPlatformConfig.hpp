#pragma once

#if defined(STM32G431xx) && defined(__GNUC__)
#define WASHIOS_RETAINED __attribute__((section(".noinit"), aligned(8)))
#else
#define WASHIOS_RETAINED
#endif
