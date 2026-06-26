#pragma once

#include "hal/IBeacon.hpp"

namespace bsp
{

class Stm32G4Beacon final : public hal::IBeacon
{
public:
    void initialize();
    void enterSafeLoop() override;
};

} /* namespace bsp */
