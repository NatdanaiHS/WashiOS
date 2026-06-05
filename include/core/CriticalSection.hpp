#pragma once

#if defined(NATIVE) || defined(WASHIOS_ENABLE_TEST_HOOKS)
#if defined(WASHIOS_ENABLE_TEST_HOOKS)
namespace core
{

void testEnterCriticalSection();
void testExitCriticalSection();

} /* namespace core */
#endif

#ifndef taskENTER_CRITICAL
#if defined(WASHIOS_ENABLE_TEST_HOOKS)
#define taskENTER_CRITICAL() core::testEnterCriticalSection()
#else
#define taskENTER_CRITICAL() do { } while (0)
#endif
#endif

#ifndef taskEXIT_CRITICAL
#if defined(WASHIOS_ENABLE_TEST_HOOKS)
#define taskEXIT_CRITICAL() core::testExitCriticalSection()
#else
#define taskEXIT_CRITICAL() do { } while (0)
#endif
#endif

#ifndef taskDISABLE_INTERRUPTS
#define taskDISABLE_INTERRUPTS() do { } while (0)
#endif
#elif __has_include("FreeRTOS.h") && __has_include("task.h")
#include "FreeRTOS.h"
#include "task.h"
#endif
