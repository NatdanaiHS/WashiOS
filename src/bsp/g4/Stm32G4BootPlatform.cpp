#include "bsp/g4/Stm32G4BootPlatform.hpp"

#include "stm32g4xx_hal.h"

namespace
{

constexpr uint32_t NvicRegisterCount = 8U;

using ApplicationEntry = void (*)();

} /* namespace */

namespace bsp
{

void Stm32G4BootPlatform::prepareForApplicationJump()
{
    __disable_irq();

    SysTick->CTRL = 0U;
    SysTick->LOAD = 0U;
    SysTick->VAL = 0U;

    HAL_RCC_DeInit();
    HAL_DeInit();

    for (uint32_t i = 0U; i < NvicRegisterCount; ++i)
    {
        NVIC->ICER[i] = 0xFFFFFFFFUL;
        NVIC->ICPR[i] = 0xFFFFFFFFUL;
    }

    __DSB();
    __ISB();
}

void Stm32G4BootPlatform::jumpToApplication(uintptr_t vectorTableBase)
{
    const volatile uint32_t* const vectorTable =
        reinterpret_cast<const volatile uint32_t*>(vectorTableBase);
    const uint32_t applicationStack = vectorTable[0];
    const uint32_t resetHandlerAddress = vectorTable[1];
    const ApplicationEntry applicationResetHandler =
        reinterpret_cast<ApplicationEntry>(resetHandlerAddress);

    SCB->VTOR = static_cast<uint32_t>(vectorTableBase);
    __set_MSP(applicationStack);
    __DSB();
    __ISB();

    applicationResetHandler();

    for (;;)
    {
    }
}

} /* namespace bsp */
