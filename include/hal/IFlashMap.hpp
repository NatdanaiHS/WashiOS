#pragma once

#include <cstddef>
#include <cstdint>

namespace hal
{

enum class FirmwareSlot : uint8_t
{
    SlotA = 0U,
    SlotB = 1U
};

class IFlashMap
{
public:
    ~IFlashMap() = default;

    virtual uintptr_t slotBase(FirmwareSlot slot) const = 0;
    virtual std::size_t slotLength(FirmwareSlot slot) const = 0;
    virtual bool isSlotVectorValid(FirmwareSlot slot) const = 0;

    virtual uintptr_t applicationBase() const = 0;
    virtual std::size_t applicationLength() const = 0;
    virtual uintptr_t ramBase() const = 0;
    virtual std::size_t ramLength() const = 0;
    virtual bool isApplicationVectorValid() const = 0;
};

} /* namespace hal */
