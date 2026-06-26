#include "bsp/g4/Stm32G4FlashMap.hpp"

namespace
{

constexpr uintptr_t ApplicationBase = 0x08004000UL;
constexpr std::size_t ApplicationLength = 112UL * 1024UL;
constexpr uintptr_t RamBase = 0x20000000UL;
constexpr std::size_t RamLength = 32UL * 1024UL;
constexpr uintptr_t ThumbBitMask = 0x00000001UL;

} /* namespace */

namespace bsp
{

uintptr_t Stm32G4FlashMap::applicationBase() const
{
    return ApplicationBase;
}

std::size_t Stm32G4FlashMap::applicationLength() const
{
    return ApplicationLength;
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
    const volatile uint32_t* const vectorTable =
        reinterpret_cast<const volatile uint32_t*>(ApplicationBase);
    const uintptr_t initialStack = static_cast<uintptr_t>(vectorTable[0]);
    const uintptr_t resetHandler = static_cast<uintptr_t>(vectorTable[1]);
    const uintptr_t resetHandlerAddress = resetHandler & ~ThumbBitMask;

    const bool stackInRam = initialStack >= RamBase &&
                            initialStack <= (RamBase + RamLength);
    const bool resetInApplication = resetHandlerAddress >= ApplicationBase &&
                                    resetHandlerAddress < (ApplicationBase + ApplicationLength);
    const bool resetIsThumb = (resetHandler & ThumbBitMask) == ThumbBitMask;

    return stackInRam && resetInApplication && resetIsThumb;
}

} /* namespace bsp */
