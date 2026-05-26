#include "SystemReset.hpp"

#include "stm32f4xx_hal.h"
#include "FreeRTOS.h"
#include "task.h"

namespace core
{

[[noreturn]] void requestSystemReset()
{
    taskDISABLE_INTERRUPTS();
    NVIC_SystemReset();

    for (;;)
    {
    }
}

} /* namespace core */
