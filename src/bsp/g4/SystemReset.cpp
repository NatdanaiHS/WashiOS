#include "SystemReset.hpp"

#include "FreeRTOS.h"
#include "stm32g4xx_hal.h"
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
