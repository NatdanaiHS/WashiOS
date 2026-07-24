#pragma once

#include <cstdint>

#include "hal/IBootPlatform.hpp"

namespace bsp
{

class Stm32G4BootPlatform final : public hal::IBootPlatform
{
public:
    void prepareForApplicationJump() override;
    void jumpToApplication(uintptr_t vectorTableBase) override;
};

} /* namespace bsp */
