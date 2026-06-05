#include "CrcProfiler.hpp"

#if defined(WASHIOS_PROFILE_CRC)

#include "Telemetry.hpp"

#if defined(STM32G431xx)
#include "stm32g4xx.h"
#elif defined(STM32F411xE)
#include "stm32f4xx.h"
#endif

namespace core
{

namespace
{

Crc32LatencyProfile profile = {};

uint32_t readCycleCounter()
{
#if defined(DWT) && defined(DWT_CTRL_CYCCNTENA_Msk)
    return DWT->CYCCNT;
#else
    return 0U;
#endif
}

} /* namespace */

void initializeCrc32Profiler()
{
#if defined(CoreDebug) && defined(CoreDebug_DEMCR_TRCENA_Msk) && \
    defined(DWT) && defined(DWT_CTRL_CYCCNTENA_Msk)
    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
    DWT->CYCCNT = 0U;
    DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;
#endif
}

uint32_t crc32Profiled(const uint8_t* data, std::size_t length)
{
    const uint32_t startCycles = readCycleCounter();
    const uint32_t crc = crc32(data, length);
    const uint32_t elapsedCycles = readCycleCounter() - startCycles;

    ++profile.samples;
    profile.lastCycles = elapsedCycles;
    if (elapsedCycles > profile.maxCycles)
    {
        profile.maxCycles = elapsedCycles;
        profile.maxBytes = length;
    }

    return crc;
}

const Crc32LatencyProfile& getCrc32LatencyProfile()
{
    return profile;
}

} /* namespace core */

#endif
