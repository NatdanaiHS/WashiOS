#pragma once

#include <cstddef>
#include <cstdint>

#include "hal/IFlashMap.hpp"

namespace bsp
{

class Stm32G4FlashMap final : public hal::IFlashMap
{
public:
    uintptr_t slotBase(hal::FirmwareSlot slot) const override;
    std::size_t slotLength(hal::FirmwareSlot slot) const override;
    bool isSlotVectorValid(hal::FirmwareSlot slot) const override;

    uintptr_t applicationBase() const override;
    std::size_t applicationLength() const override;
    uintptr_t ramBase() const override;
    std::size_t ramLength() const override;
    bool isApplicationVectorValid() const override;
};

} /* namespace bsp */
