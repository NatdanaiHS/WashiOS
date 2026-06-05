#include "bsp/esp32/GpioDriver.hpp"

#include <Arduino.h>

namespace bsp::esp32
{

GpioDriver::GpioDriver(uint8_t pinNumber)
    : pin(pinNumber),
      state(false),
      initialized(false)
{
}

void GpioDriver::setHigh()
{
    initializePin();
    state = true;
    digitalWrite(pin, HIGH);
}

void GpioDriver::setLow()
{
    initializePin();
    state = false;
    digitalWrite(pin, LOW);
}

void GpioDriver::toggle()
{
    if (read())
    {
        setLow();
    }
    else
    {
        setHigh();
    }
}

bool GpioDriver::read() const
{
    initializePin();
    state = (digitalRead(pin) == HIGH);
    return state;
}

bool GpioDriver::setInterrupt(hal::GpioInterruptEdge edge,
                              hal::GpioInterruptCallback callback,
                              void* context)
{
    (void)edge;
    (void)callback;
    (void)context;
    return false;
}

void GpioDriver::clearInterrupt()
{
}

void GpioDriver::initializePin() const
{
    if (!initialized)
    {
        pinMode(pin, OUTPUT);
        digitalWrite(pin, state ? HIGH : LOW);
        initialized = true;
    }
}

} /* namespace bsp::esp32 */
