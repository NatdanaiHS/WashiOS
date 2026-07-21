#include "bsp/g4/Stm32G4Timing.hpp"

#include "FreeRTOS.h"
#include "task.h"
#include "stm32g4xx_hal.h"

namespace bsp
{

void Stm32G4Timing::initialize()
{
    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
    DWT->CYCCNT = 0U;
    DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;
    dwtReady = (DWT->CTRL & DWT_CTRL_CYCCNTENA_Msk) != 0U;
}

uint64_t Stm32G4Timing::getSystemTick() const noexcept
{
    if (xTaskGetSchedulerState() != taskSCHEDULER_NOT_STARTED)
    {
        return static_cast<uint64_t>(xTaskGetTickCount());
    }

    return HAL_GetTick();
}

void Stm32G4Timing::delayMs(uint32_t ms) noexcept
{
    HAL_Delay(ms);
}

void Stm32G4Timing::delayUs(uint32_t us) noexcept
{
    if (!dwtReady)
    {
        const uint32_t start = HAL_GetTick();
        while ((HAL_GetTick() - start) == 0U && us > 0U)
        {
        }
        return;
    }

    const uint32_t cyclesPerUs = SystemCoreClock / 1000000UL;
    const uint32_t start = DWT->CYCCNT;
    const uint32_t cycles = cyclesPerUs * us;
    while ((DWT->CYCCNT - start) < cycles)
    {
    }
}

} /* namespace bsp */
