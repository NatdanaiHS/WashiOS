#pragma once

#include <cstdint>

#include "ITiming.hpp"

namespace bsp
{

class Stm32G4Timing final : public hal::ITiming
{
public:
    void initialize();

    uint64_t getSystemTick() const noexcept override;
    void delayMs(uint32_t ms) noexcept override;
    void delayUs(uint32_t us) noexcept override;

private:
    bool dwtReady = false;
};

} /* namespace bsp */
