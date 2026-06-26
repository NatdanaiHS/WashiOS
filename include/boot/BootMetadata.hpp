#pragma once

#include <cstdint>

#include "Crc32.hpp"
#include "FaultLog.hpp"

namespace boot
{

constexpr uint32_t BootMetadataConfirmed = 0xA5A55A5AUL;
constexpr uint32_t InvalidExpectedCrc0 = 0x00000000UL;
constexpr uint32_t InvalidExpectedCrc1 = 0xFFFFFFFFUL;

struct BootMetadata
{
    uint32_t signature;
    uint32_t checksum;
    uint32_t boot_count;
    uint32_t confirmed_flag;
    uint32_t expected_firmware_crc32;
};

inline bool isExpectedCrcProvisioned(uint32_t value)
{
    return value != InvalidExpectedCrc0 && value != InvalidExpectedCrc1;
}

inline uint32_t calculateBootMetadataChecksum(const BootMetadata& metadata)
{
    uint32_t crc = 0xFFFFFFFFUL;
    crc = crc32UpdateU32(crc, metadata.signature);
    crc = crc32UpdateU32(crc, metadata.boot_count);
    crc = crc32UpdateU32(crc, metadata.confirmed_flag);
    crc = crc32UpdateU32(crc, metadata.expected_firmware_crc32);
    return ~crc;
}

inline void commitBootMetadata(BootMetadata& metadata)
{
    metadata.signature = core::WASHIOS_MAGIC_SIGNATURE;
    metadata.checksum = calculateBootMetadataChecksum(metadata);
}

inline bool hasValidBootMetadata(const BootMetadata& metadata)
{
    return metadata.signature == core::WASHIOS_MAGIC_SIGNATURE &&
           metadata.checksum == calculateBootMetadataChecksum(metadata);
}

inline bool recoverBootMetadata(BootMetadata& metadata, uint32_t defaultExpectedCrc)
{
    if (hasValidBootMetadata(metadata))
    {
        if (!isExpectedCrcProvisioned(metadata.expected_firmware_crc32))
        {
            metadata.expected_firmware_crc32 = defaultExpectedCrc;
            commitBootMetadata(metadata);
        }

        return true;
    }

    metadata.boot_count = 0U;
    metadata.confirmed_flag = 0U;
    metadata.expected_firmware_crc32 = defaultExpectedCrc;
    commitBootMetadata(metadata);
    return false;
}

inline uint32_t expectedFirmwareCrc(const BootMetadata& metadata,
                                    uint32_t defaultExpectedCrc)
{
    if (isExpectedCrcProvisioned(metadata.expected_firmware_crc32))
    {
        return metadata.expected_firmware_crc32;
    }

    return defaultExpectedCrc;
}

inline void normalizeConfirmedBoot(BootMetadata& metadata)
{
    if (metadata.confirmed_flag == BootMetadataConfirmed)
    {
        metadata.boot_count = 0U;
        metadata.confirmed_flag = 0U;
        commitBootMetadata(metadata);
    }
}

inline void noteBootAttempt(BootMetadata& metadata)
{
    ++metadata.boot_count;
    commitBootMetadata(metadata);
}

} /* namespace boot */
