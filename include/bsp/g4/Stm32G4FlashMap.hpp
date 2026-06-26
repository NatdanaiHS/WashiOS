#pragma once

#include <cstddef>
#include <cstdint>

#include "hal/IFlashMap.hpp"

namespace bsp
{

class Stm32G4FlashMap final : public hal::IFlashMap
{
public:
    uintptr_t applicationBase() const override;
    std::size_t applicationLength() const override;
    uintptr_t ramBase() const override;
    std::size_t ramLength() const override;
    bool isApplicationVectorValid() const override;
};

} /* namespace bsp */
