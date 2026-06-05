#include "bsp/rp2040/UartDriver.hpp"

#include <Arduino.h>

namespace bsp::rp2040
{

UartDriver::UartDriver()
    : baud(115200U)
{
}

bool UartDriver::writeBuffer(const uint8_t* data,
                             std::size_t length,
                             uint32_t timeout_ms)
{
    if (data == nullptr && length > 0U)
    {
        return false;
    }
    if (length == 0U)
    {
        return true;
    }

    Serial.setTimeout(timeout_ms);
    const std::size_t written = Serial.write(data, length);
    Serial.flush();
    return written == length;
}

bool UartDriver::readBuffer(uint8_t* buffer,
                            std::size_t length,
                            uint32_t timeout_ms)
{
    if (buffer == nullptr && length > 0U)
    {
        return false;
    }

    const uint32_t startMs = millis();
    std::size_t received = 0U;
    while (received < length)
    {
        if (Serial.available() > 0)
        {
            const int value = Serial.read();
            if (value >= 0)
            {
                buffer[received] = static_cast<uint8_t>(value);
                ++received;
            }
        }
        else if ((millis() - startMs) >= timeout_ms)
        {
            return false;
        }
    }

    return true;
}

std::size_t UartDriver::available() const
{
    return static_cast<std::size_t>(Serial.available());
}

void UartDriver::flush()
{
    Serial.flush();
}

void UartDriver::setBaudRate(uint32_t baudRate)
{
    baud = baudRate;
    Serial.begin(baud);
}

} /* namespace bsp::rp2040 */
