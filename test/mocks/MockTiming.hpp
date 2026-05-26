#pragma once

#include <cstdint>

#include "ITiming.hpp"

namespace test_mocks
{

class MockTiming final : public hal::ITiming
{
public:
    uint64_t getSystemTick() const override
    {
        return tickMs;
    }

    void delayMs(uint32_t ms) override
    {
        tickMs += ms;
        tickUs += static_cast<uint64_t>(ms) * 1000ULL;
    }

    void delayUs(uint32_t us) override
    {
        tickUs += us;
        tickMs = tickUs / 1000ULL;
    }

    void setTickMs(uint64_t value)
    {
        tickMs = value;
        tickUs = value * 1000ULL;
    }

    uint64_t getTickUs() const
    {
        return tickUs;
    }

private:
    uint64_t tickMs = 0;
    uint64_t tickUs = 0;
};

} /* namespace test_mocks */
