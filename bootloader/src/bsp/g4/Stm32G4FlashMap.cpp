#include "bsp/g4/Stm32G4FlashMap.hpp"

namespace
{

constexpr uintptr_t SlotABase = 0x08004000UL;
constexpr std::size_t SlotALength = 56UL * 1024UL;
constexpr uintptr_t SlotBBase = 0x08012000UL;
constexpr std::size_t SlotBLength = 56UL * 1024UL;
constexpr uintptr_t RamBase = 0x20000000UL;
constexpr std::size_t RamLength = 32UL * 1024UL;
constexpr uintptr_t ThumbBitMask = 0x00000001UL;

bool isVectorValidAt(uintptr_t base, std::size_t length)
{
    const volatile uint32_t* const vectorTable =
        reinterpret_cast<const volatile uint32_t*>(base);
    const uintptr_t initialStack = static_cast<uintptr_t>(vectorTable[0]);
    const uintptr_t resetHandler = static_cast<uintptr_t>(vectorTable[1]);
    const uintptr_t resetHandlerAddress = resetHandler & ~ThumbBitMask;

    const bool stackInRam = initialStack >= RamBase &&
                            initialStack <= (RamBase + RamLength);
    const bool resetInSlot = resetHandlerAddress >= base &&
                             resetHandlerAddress < (base + length);
    const bool resetIsThumb = (resetHandler & ThumbBitMask) == ThumbBitMask;

    return stackInRam && resetInSlot && resetIsThumb;
}

} /* namespace */

namespace bsp
{

uintptr_t Stm32G4FlashMap::slotBase(hal::FirmwareSlot slot) const
{
    return (slot == hal::FirmwareSlot::SlotB) ? SlotBBase : SlotABase;
}

std::size_t Stm32G4FlashMap::slotLength(hal::FirmwareSlot slot) const
{
    return (slot == hal::FirmwareSlot::SlotB) ? SlotBLength : SlotALength;
}

bool Stm32G4FlashMap::isSlotVectorValid(hal::FirmwareSlot slot) const
{
    return isVectorValidAt(slotBase(slot), slotLength(slot));
}

uintptr_t Stm32G4FlashMap::applicationBase() const
{
    return slotBase(hal::FirmwareSlot::SlotA);
}

std::size_t Stm32G4FlashMap::applicationLength() const
{
    return slotLength(hal::FirmwareSlot::SlotA);
}

uintptr_t Stm32G4FlashMap::ramBase() const
{
    return RamBase;
}

std::size_t Stm32G4FlashMap::ramLength() const
{
    return RamLength;
}

bool Stm32G4FlashMap::isApplicationVectorValid() const
{
    return isSlotVectorValid(hal::FirmwareSlot::SlotA);
}

} /* namespace bsp */
