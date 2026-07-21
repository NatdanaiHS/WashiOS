#pragma once

#include <cstddef>
#include <cstdint>

#include "IGPIO.hpp"
#include "ITiming.hpp"

namespace comms
{

constexpr uint32_t LaserPdmShortPulseUs = 2000U;
constexpr uint32_t LaserPdmLongPulseUs = 4000U;
constexpr uint32_t LaserPdmGapUs = 2000U;

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

    bool sendSyncPulses(uint8_t repeats,
                        uint32_t highDurationUs,
                        uint32_t lowDurationUs) noexcept
    {
        if (repeats == 0U)
        {
            output.setLow();
            return true;
        }

        for (uint8_t repeat = 0U; repeat < repeats; ++repeat)
        {
            output.setHigh();
            timing.delayUs(highDurationUs);
            output.setLow();
            timing.delayUs(lowDurationUs);
        }

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
