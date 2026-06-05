#pragma once

#include <cstdint>

#include "IGPIO.hpp"

namespace bsp::esp32
{

class GpioDriver final : public hal::IGPIO
{
public:
    explicit GpioDriver(uint8_t pinNumber);

    void setHigh() override;
    void setLow() override;
    void toggle() override;
    bool read() const override;
    bool setInterrupt(hal::GpioInterruptEdge edge,
                      hal::GpioInterruptCallback callback,
                      void* context) override;
    void clearInterrupt() override;

private:
    void initializePin() const;

    uint8_t pin;
    mutable bool state;
    mutable bool initialized;
};

} /* namespace bsp::esp32 */
