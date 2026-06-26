#include "bsp/g4/Stm32G4Beacon.hpp"

#include "stm32g4xx_hal.h"

namespace
{

constexpr uint32_t BeaconPin = GPIO_PIN_5;
GPIO_TypeDef* const BeaconPort = GPIOA;

void delayCycles(uint32_t cycles)
{
    for (volatile uint32_t i = 0U; i < cycles; ++i)
    {
        __NOP();
    }
}

} /* namespace */

namespace bsp
{

void Stm32G4Beacon::initialize()
{
    __HAL_RCC_GPIOA_CLK_ENABLE();

    GPIO_InitTypeDef gpio = {};
    gpio.Pin = BeaconPin;
    gpio.Mode = GPIO_MODE_OUTPUT_PP;
    gpio.Pull = GPIO_NOPULL;
    gpio.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(BeaconPort, &gpio);
    HAL_GPIO_WritePin(BeaconPort, BeaconPin, GPIO_PIN_RESET);
}

void Stm32G4Beacon::enterSafeLoop()
{
    for (;;)
    {
        HAL_GPIO_TogglePin(BeaconPort, BeaconPin);
        delayCycles(1200000UL);
        __WFI();
    }
}

} /* namespace bsp */
