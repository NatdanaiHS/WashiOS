#pragma once

#include <cstdint>

#include "IGPIO.hpp"

namespace bsp
{

class Stm32Gpio final : public hal::IGPIO
{
public:
    Stm32Gpio(void* gpioPort, uint16_t gpioPin);

    void initializeOutput(bool initialHigh);
    void initializeInput();

    void setHigh() override;
    void setLow() override;
    void toggle() override;
    bool read() const override;

    bool setInterrupt(hal::GpioInterruptEdge edge,
                      hal::GpioInterruptCallback callback,
                      void* context) override;
    void clearInterrupt() override;

    bool matchesPin(uint16_t gpioPin) const;
    void dispatchInterrupt();

private:
    void* port;
    uint16_t pin;
    hal::GpioInterruptEdge interruptEdge = hal::GpioInterruptEdge::Rising;
    hal::GpioInterruptCallback interruptCallback = nullptr;
    void* interruptContext = nullptr;
};

} /* namespace bsp */
