#pragma once

#include <cstdint>

#include "IPwm.hpp"

namespace test_mocks
{

template<uint8_t ChannelCount = 8>
class MockPwm final : public hal::IPwm
{
public:
    bool setFrequency(uint8_t channelId, uint32_t hz) noexcept override
    {
        if (!isValidChannel(channelId) || hz == 0U)
        {
            return false;
        }

        channels[channelId].frequencyHz = hz;
        return true;
    }

    bool setDutyCycle(uint8_t channelId, float percentage) noexcept override
    {
        if (!isValidChannel(channelId) || percentage < 0.0F || percentage > 100.0F)
        {
            return false;
        }

        channels[channelId].dutyCyclePercentage = percentage;
        return true;
    }

    void start(uint8_t channelId) noexcept override
    {
        if (isValidChannel(channelId))
        {
            channels[channelId].enabled = true;
        }
    }

    void stop(uint8_t channelId) noexcept override
    {
        if (isValidChannel(channelId))
        {
            channels[channelId].enabled = false;
            channels[channelId].dutyCyclePercentage = 0.0F;
        }
    }

    bool getChannelState(uint8_t channelId,
                         hal::PwmChannelState& outState) const noexcept override
    {
        if (!isValidChannel(channelId))
        {
            return false;
        }

        outState = channels[channelId];
        return true;
    }

private:
    hal::PwmChannelState channels[ChannelCount] = {};

    bool isValidChannel(uint8_t channelId) const
    {
        return channelId < ChannelCount;
    }
};

} /* namespace test_mocks */
