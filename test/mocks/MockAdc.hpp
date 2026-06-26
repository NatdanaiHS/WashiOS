#pragma once

#include <cstdint>

#include "IAdc.hpp"

namespace test_mocks
{

template<uint8_t ChannelCount = 16>
class MockAdc final : public hal::IAdc
{
public:
    bool readRaw(uint8_t channelId,
                 uint16_t& outRawValue,
                 uint32_t timeout_ms) noexcept override
    {
        if (!isValidChannel(channelId) || status != hal::AdcStatus::Ready ||
            forcedTimeout || timeout_ms == 0U)
        {
            return false;
        }

        outRawValue = rawValues[channelId];
        return true;
    }

    bool readVoltage(uint8_t channelId,
                     float& outVoltage,
                     uint32_t timeout_ms) noexcept override
    {
        uint16_t raw = 0;
        if (!readRaw(channelId, raw, timeout_ms))
        {
            return false;
        }

        const float maxRaw = static_cast<float>((1UL << resolutionBits) - 1UL);
        outVoltage = (static_cast<float>(raw) / maxRaw) * referenceVoltage;
        return true;
    }

    bool setResolution(uint8_t bits) noexcept override
    {
        if (bits < 8U || bits > 16U)
        {
            return false;
        }

        resolutionBits = bits;
        return true;
    }

    hal::AdcStatus getStatus() const noexcept override
    {
        return status;
    }

    bool setRawValue(uint8_t channelId, uint16_t rawValue)
    {
        if (!isValidChannel(channelId))
        {
            return false;
        }

        rawValues[channelId] = rawValue;
        return true;
    }

    void setReferenceVoltage(float voltage)
    {
        referenceVoltage = voltage;
    }

    void setStatus(hal::AdcStatus newStatus)
    {
        status = newStatus;
    }

    void setForcedTimeout(bool enabled)
    {
        forcedTimeout = enabled;
    }

    uint8_t resolution() const
    {
        return resolutionBits;
    }

private:
    uint16_t rawValues[ChannelCount] = {};
    uint8_t resolutionBits = 12;
    float referenceVoltage = 3.3F;
    bool forcedTimeout = false;
    hal::AdcStatus status = hal::AdcStatus::Ready;

    bool isValidChannel(uint8_t channelId) const
    {
        return channelId < ChannelCount;
    }
};

} /* namespace test_mocks */
