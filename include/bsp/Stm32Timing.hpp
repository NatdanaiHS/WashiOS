#pragma once

#include <cstdint>

#include "ITiming.hpp"

namespace bsp
{

class Stm32Timing final : public hal::ITiming
{
public:
    void initialize();

    uint64_t getSystemTick() const override;
    void delayMs(uint32_t ms) override;
    void delayUs(uint32_t us) override;

private:
    bool dwtReady = false;
};

} /* namespace bsp */
