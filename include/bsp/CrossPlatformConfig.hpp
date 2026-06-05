#pragma once

#if defined(STM32G431xx) && defined(__GNUC__)
#define WASHIOS_RETAINED __attribute__((section(".noinit"), aligned(8)))
#elif defined(WASHIOS_TARGET_RP2040) && defined(__GNUC__)
#define WASHIOS_RETAINED __attribute__((section(".uninitialized_data"), aligned(8)))
#elif defined(WASHIOS_TARGET_ESP32)
#if defined(__NOINIT_ATTR)
#define WASHIOS_RETAINED __NOINIT_ATTR __attribute__((aligned(8)))
#elif defined(__GNUC__)
#define WASHIOS_RETAINED __attribute__((section(".noinit"), aligned(8)))
#else
#define WASHIOS_RETAINED
#endif
#else
#define WASHIOS_RETAINED
#endif
