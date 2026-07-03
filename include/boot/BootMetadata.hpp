#pragma once

#include <cstdint>

#include "Crc32.hpp"
#include "FaultLog.hpp"

namespace boot
{

constexpr uint32_t BootMetadataConfirmed = 0xA5A55A5AUL;
constexpr uint32_t BootMetadataCurrentVersion = 2UL;
constexpr uint32_t InvalidExpectedCrc0 = 0x00000000UL;
constexpr uint32_t InvalidExpectedCrc1 = 0xFFFFFFFFUL;

enum class BootSlot : uint32_t
{
    SlotA = 0U,
    SlotB = 1U
};

enum class FirmwareSlotState : uint32_t
{
    Empty = 0U,
    Valid = 1U,
    Pending = 2U,
    Confirmed = 3U,
    Bad = 4U
};

struct BootMetadata
{
    uint32_t signature;
    uint32_t checksum;
    uint32_t boot_count;
    uint32_t confirmed_flag;
    uint32_t expected_firmware_crc32;
    uint32_t metadata_version;
    uint32_t active_slot;
    uint32_t slot_a_crc32;
    uint32_t slot_b_crc32;
    uint32_t slot_a_state;
    uint32_t slot_b_state;
    uint32_t last_boot_slot;
    uint32_t last_fail_reason;
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
    crc = crc32UpdateU32(crc, metadata.metadata_version);
    crc = crc32UpdateU32(crc, metadata.active_slot);
    crc = crc32UpdateU32(crc, metadata.slot_a_crc32);
    crc = crc32UpdateU32(crc, metadata.slot_b_crc32);
    crc = crc32UpdateU32(crc, metadata.slot_a_state);
    crc = crc32UpdateU32(crc, metadata.slot_b_state);
    crc = crc32UpdateU32(crc, metadata.last_boot_slot);
    crc = crc32UpdateU32(crc, metadata.last_fail_reason);
    return ~crc;
}

inline uint32_t calculateLegacyBootMetadataChecksum(const BootMetadata& metadata)
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
    metadata.metadata_version = BootMetadataCurrentVersion;
    metadata.checksum = calculateBootMetadataChecksum(metadata);
}

inline bool hasValidBootMetadata(const BootMetadata& metadata)
{
    return metadata.signature == core::WASHIOS_MAGIC_SIGNATURE &&
           metadata.metadata_version == BootMetadataCurrentVersion &&
           metadata.checksum == calculateBootMetadataChecksum(metadata);
}

inline bool hasValidLegacyBootMetadata(const BootMetadata& metadata)
{
    return metadata.signature == core::WASHIOS_MAGIC_SIGNATURE &&
           metadata.checksum == calculateLegacyBootMetadataChecksum(metadata);
}

inline bool isValidBootSlot(uint32_t value)
{
    return value == static_cast<uint32_t>(BootSlot::SlotA) ||
           value == static_cast<uint32_t>(BootSlot::SlotB);
}

inline bool isValidFirmwareSlotState(uint32_t value)
{
    return value == static_cast<uint32_t>(FirmwareSlotState::Empty) ||
           value == static_cast<uint32_t>(FirmwareSlotState::Valid) ||
           value == static_cast<uint32_t>(FirmwareSlotState::Pending) ||
           value == static_cast<uint32_t>(FirmwareSlotState::Confirmed) ||
           value == static_cast<uint32_t>(FirmwareSlotState::Bad);
}

inline bool isBootableFirmwareSlotState(uint32_t value)
{
    return value == static_cast<uint32_t>(FirmwareSlotState::Valid) ||
           value == static_cast<uint32_t>(FirmwareSlotState::Pending) ||
           value == static_cast<uint32_t>(FirmwareSlotState::Confirmed);
}

inline void initializeBootMetadata(BootMetadata& metadata, uint32_t defaultExpectedCrc)
{
    metadata.boot_count = 0U;
    metadata.confirmed_flag = 0U;
    metadata.expected_firmware_crc32 = defaultExpectedCrc;
    metadata.active_slot = static_cast<uint32_t>(BootSlot::SlotA);
    metadata.slot_a_crc32 = defaultExpectedCrc;
    metadata.slot_b_crc32 = InvalidExpectedCrc0;
    metadata.slot_a_state = isExpectedCrcProvisioned(defaultExpectedCrc) ?
        static_cast<uint32_t>(FirmwareSlotState::Valid) :
        static_cast<uint32_t>(FirmwareSlotState::Empty);
    metadata.slot_b_state = static_cast<uint32_t>(FirmwareSlotState::Empty);
    metadata.last_boot_slot = static_cast<uint32_t>(BootSlot::SlotA);
    metadata.last_fail_reason = 0U;
    commitBootMetadata(metadata);
}

inline void migrateLegacyBootMetadata(BootMetadata& metadata, uint32_t defaultExpectedCrc)
{
    const uint32_t expectedCrc = isExpectedCrcProvisioned(metadata.expected_firmware_crc32) ?
        metadata.expected_firmware_crc32 :
        defaultExpectedCrc;

    metadata.expected_firmware_crc32 = expectedCrc;
    metadata.active_slot = static_cast<uint32_t>(BootSlot::SlotA);
    metadata.slot_a_crc32 = expectedCrc;
    metadata.slot_b_crc32 = InvalidExpectedCrc0;
    metadata.slot_a_state = isExpectedCrcProvisioned(expectedCrc) ?
        static_cast<uint32_t>(FirmwareSlotState::Valid) :
        static_cast<uint32_t>(FirmwareSlotState::Empty);
    metadata.slot_b_state = static_cast<uint32_t>(FirmwareSlotState::Empty);
    metadata.last_boot_slot = static_cast<uint32_t>(BootSlot::SlotA);
    metadata.last_fail_reason = 0U;
    commitBootMetadata(metadata);
}

inline bool hasSaneBootMetadataFields(const BootMetadata& metadata)
{
    return isValidBootSlot(metadata.active_slot) &&
           isValidBootSlot(metadata.last_boot_slot) &&
           isValidFirmwareSlotState(metadata.slot_a_state) &&
           isValidFirmwareSlotState(metadata.slot_b_state);
}

inline bool recoverBootMetadata(BootMetadata& metadata, uint32_t defaultExpectedCrc)
{
    if (hasValidBootMetadata(metadata))
    {
        if (!hasSaneBootMetadataFields(metadata))
        {
            initializeBootMetadata(metadata, defaultExpectedCrc);
            return false;
        }

        return true;
    }

    if (hasValidLegacyBootMetadata(metadata))
    {
        migrateLegacyBootMetadata(metadata, defaultExpectedCrc);
        return true;
    }

    initializeBootMetadata(metadata, defaultExpectedCrc);
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
        if (metadata.active_slot == static_cast<uint32_t>(BootSlot::SlotA))
        {
            metadata.slot_a_state = static_cast<uint32_t>(FirmwareSlotState::Confirmed);
        }
        else if (metadata.active_slot == static_cast<uint32_t>(BootSlot::SlotB))
        {
            metadata.slot_b_state = static_cast<uint32_t>(FirmwareSlotState::Confirmed);
        }
        commitBootMetadata(metadata);
    }
}

inline void noteBootAttempt(BootMetadata& metadata, BootSlot slot)
{
    ++metadata.boot_count;
    metadata.last_boot_slot = static_cast<uint32_t>(slot);
    commitBootMetadata(metadata);
}

inline void noteBootFailure(BootMetadata& metadata, uint32_t reason)
{
    metadata.last_fail_reason = reason;
    commitBootMetadata(metadata);
}

inline void activateBootSlot(BootMetadata& metadata, BootSlot slot)
{
    metadata.active_slot = static_cast<uint32_t>(slot);
    commitBootMetadata(metadata);
}

inline uint32_t expectedFirmwareCrcForSlot(const BootMetadata& metadata,
                                           BootSlot slot,
                                           uint32_t defaultExpectedCrc)
{
    if (slot == BootSlot::SlotB)
    {
        return metadata.slot_b_crc32;
    }

    if (isExpectedCrcProvisioned(metadata.slot_a_crc32))
    {
        return metadata.slot_a_crc32;
    }

    return expectedFirmwareCrc(metadata, defaultExpectedCrc);
}

inline uint32_t firmwareSlotState(const BootMetadata& metadata, BootSlot slot)
{
    return (slot == BootSlot::SlotB) ? metadata.slot_b_state : metadata.slot_a_state;
}

} /* namespace boot */
