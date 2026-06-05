#pragma once

#include <cstddef>
#include <cstdint>

namespace core
{

struct Crc32LatencyProfile
{
    uint32_t samples;
    uint32_t lastCycles;
    uint32_t maxCycles;
    std::size_t maxBytes;
};

#if defined(WASHIOS_PROFILE_CRC)
void initializeCrc32Profiler();
uint32_t crc32Profiled(const uint8_t* data, std::size_t length);
const Crc32LatencyProfile& getCrc32LatencyProfile();
#endif

} /* namespace core */
