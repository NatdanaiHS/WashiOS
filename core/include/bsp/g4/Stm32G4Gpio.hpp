#pragma once

#include <cstdint>

#include "IGPIO.hpp"

namespace bsp
{

class Stm32G4Gpio final : public hal::IGPIO
{
public:
    Stm32G4Gpio(void* gpioPort, uint16_t gpioPin);

    void initializeOutput(bool initialHigh);
    void initializeInput();

    void setHigh() noexcept override;
    void setLow() noexcept override;
    void toggle() noexcept override;
    bool read() const noexcept override;

    bool setInterrupt(hal::GpioInterruptEdge edge,
                      hal::GpioInterruptCallback callback,
                      void* context) noexcept override;
    void clearInterrupt() noexcept override;

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
