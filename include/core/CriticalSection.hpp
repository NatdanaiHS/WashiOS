#pragma once

#if defined(NATIVE) || defined(WASHIOS_ENABLE_TEST_HOOKS)
#ifndef taskENTER_CRITICAL
#define taskENTER_CRITICAL() do { } while (0)
#endif
#ifndef taskEXIT_CRITICAL
#define taskEXIT_CRITICAL() do { } while (0)
#endif
#ifndef taskDISABLE_INTERRUPTS
#define taskDISABLE_INTERRUPTS() do { } while (0)
#endif
#elif __has_include("FreeRTOS.h") && __has_include("task.h")
#include "FreeRTOS.h"
#include "task.h"
#endif
