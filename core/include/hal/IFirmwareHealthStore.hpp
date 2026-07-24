#pragma once

#include <cstdint>

namespace hal
{

enum class FirmwareHealthSlot : uint8_t
{
    SlotA = 0U,
    SlotB = 1U
};

class IFirmwareHealthStore
{
public:
    virtual ~IFirmwareHealthStore() noexcept = default;

    virtual bool isMetadataValid() const noexcept = 0;
    virtual bool isSlotVectorValid(FirmwareHealthSlot slot) const noexcept = 0;
    virtual bool expectedSlotCrc(FirmwareHealthSlot slot,
                                 uint32_t& outCrc) const noexcept = 0;
    virtual bool calculateSlotCrc(FirmwareHealthSlot slot,
                                  uint32_t& outCrc) const noexcept = 0;
    virtual bool expectedBootloaderCrc(uint32_t& outCrc) const noexcept = 0;
    virtual bool calculateBootloaderCrc(uint32_t& outCrc) const noexcept = 0;
};

} /* namespace hal */
