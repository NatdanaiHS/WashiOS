#pragma once

#include <cstddef>
#include <cstdint>

#include "IGPIO.hpp"
#include "ITiming.hpp"

namespace comms
{

constexpr uint32_t LaserPdmShortPulseUs = 200U;
constexpr uint32_t LaserPdmLongPulseUs = 400U;
constexpr uint32_t LaserPdmGapUs = 200U;

class LaserPdmTx
{
public:
    LaserPdmTx(hal::IGPIO& outputPin, hal::ITiming& timingSource)
        : output(outputPin),
          timing(timingSource)
    {
    }

    bool sendBuffer(const uint8_t* data, std::size_t length) noexcept
    {
        if (data == nullptr && length > 0U)
        {
            output.setLow();
            return false;
        }

        for (std::size_t i = 0U; i < length; ++i)
        {
            sendByte(data[i]);
        }

        output.setLow();
        return true;
    }

    void sendByte(uint8_t value) noexcept
    {
        for (int8_t bit = 7; bit >= 0; --bit)
        {
            const bool bitSet = ((value >> bit) & 0x01U) != 0U;
            sendBit(bitSet);
        }
    }

    void sendBit(bool bitSet) noexcept
    {
        output.setHigh();
        timing.delayUs(bitSet ? LaserPdmLongPulseUs : LaserPdmShortPulseUs);
        output.setLow();
        timing.delayUs(LaserPdmGapUs);
    }

private:
    hal::IGPIO& output;
    hal::ITiming& timing;
};

} /* namespace comms */
