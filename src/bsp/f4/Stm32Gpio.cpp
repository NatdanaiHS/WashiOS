#include "bsp/f4/Stm32Gpio.hpp"

#include "stm32f4xx_hal.h"

namespace
{

constexpr uint8_t MaxInterruptPins = 16U;
bsp::Stm32Gpio* interruptPins[MaxInterruptPins] = {};

uint8_t pinToIndex(uint16_t pin)
{
    for (uint8_t index = 0U; index < MaxInterruptPins; ++index)
    {
        if ((pin & (1UL << index)) != 0U)
        {
            return index;
        }
    }

    return MaxInterruptPins;
}

uint32_t edgeToMode(hal::GpioInterruptEdge edge)
{
    switch (edge)
    {
    case hal::GpioInterruptEdge::Rising:
        return GPIO_MODE_IT_RISING;
    case hal::GpioInterruptEdge::Falling:
        return GPIO_MODE_IT_FALLING;
    case hal::GpioInterruptEdge::Both:
    default:
        return GPIO_MODE_IT_RISING_FALLING;
    }
}

} /* namespace */

namespace bsp
{

Stm32Gpio::Stm32Gpio(void* gpioPort, uint16_t gpioPin)
    : port(gpioPort),
      pin(gpioPin)
{
}

void Stm32Gpio::initializeOutput(bool initialHigh)
{
    GPIO_InitTypeDef init = {};
    init.Pin = pin;
    init.Mode = GPIO_MODE_OUTPUT_PP;
    init.Pull = GPIO_NOPULL;
    init.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(static_cast<GPIO_TypeDef*>(port), &init);

    if (initialHigh)
    {
        setHigh();
    }
    else
    {
        setLow();
    }
}

void Stm32Gpio::initializeInput()
{
    GPIO_InitTypeDef init = {};
    init.Pin = pin;
    init.Mode = GPIO_MODE_INPUT;
    init.Pull = GPIO_NOPULL;
    init.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(static_cast<GPIO_TypeDef*>(port), &init);
}

void Stm32Gpio::setHigh()
{
    HAL_GPIO_WritePin(static_cast<GPIO_TypeDef*>(port), pin, GPIO_PIN_SET);
}

void Stm32Gpio::setLow()
{
    HAL_GPIO_WritePin(static_cast<GPIO_TypeDef*>(port), pin, GPIO_PIN_RESET);
}

void Stm32Gpio::toggle()
{
    HAL_GPIO_TogglePin(static_cast<GPIO_TypeDef*>(port), pin);
}

bool Stm32Gpio::read() const
{
    return HAL_GPIO_ReadPin(static_cast<GPIO_TypeDef*>(port), pin) == GPIO_PIN_SET;
}

bool Stm32Gpio::setInterrupt(hal::GpioInterruptEdge edge,
                             hal::GpioInterruptCallback callback,
                             void* context)
{
    if (callback == nullptr)
    {
        return false;
    }

    const uint8_t index = pinToIndex(pin);
    if (index >= MaxInterruptPins)
    {
        return false;
    }

    GPIO_InitTypeDef init = {};
    init.Pin = pin;
    init.Mode = edgeToMode(edge);
    init.Pull = GPIO_NOPULL;
    init.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(static_cast<GPIO_TypeDef*>(port), &init);

    interruptEdge = edge;
    interruptCallback = callback;
    interruptContext = context;
    interruptPins[index] = this;
    return true;
}

void Stm32Gpio::clearInterrupt()
{
    const uint8_t index = pinToIndex(pin);
    if (index < MaxInterruptPins && interruptPins[index] == this)
    {
        interruptPins[index] = nullptr;
    }

    interruptCallback = nullptr;
    interruptContext = nullptr;
}

bool Stm32Gpio::matchesPin(uint16_t gpioPin) const
{
    return pin == gpioPin;
}

void Stm32Gpio::dispatchInterrupt()
{
    if (interruptCallback != nullptr)
    {
        interruptCallback(interruptContext);
    }
}

} /* namespace bsp */

extern "C" void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
{
    const uint8_t index = pinToIndex(GPIO_Pin);
    if (index < MaxInterruptPins && interruptPins[index] != nullptr &&
        interruptPins[index]->matchesPin(GPIO_Pin))
    {
        interruptPins[index]->dispatchInterrupt();
    }
}
