#pragma once

#include <cstddef>
#include <cstdint>

#include "BootMetadata.hpp"
#include "Crc32.hpp"
#include "FaultLog.hpp"
#include "hal/IBootPlatform.hpp"
#include "hal/IBeacon.hpp"
#include "hal/IFlashMap.hpp"

namespace boot
{

constexpr uint32_t MaxUnconfirmedBootAttempts = 3U;
constexpr uint32_t DetailFaultLogRecoveryFailed = 0xB0010001UL;
constexpr uint32_t DetailBootLoopLimit = 0xB0010002UL;
constexpr uint32_t DetailPriorCriticalFault = 0xB0010003UL;
constexpr uint32_t DetailInvalidVectorTable = 0xB0010004UL;
constexpr uint32_t DetailFirmwareCrcMismatch = 0xB0010005UL;
constexpr uint32_t DetailNoValidFirmwareSlot = 0xB0010006UL;
constexpr uint32_t DetailInvalidSlotState = 0xB0010007UL;

class BootPolicy
{
public:
    BootPolicy(hal::IFlashMap& flashMapRef,
               hal::IBootPlatform& platformRef,
               hal::IBeacon& beaconRef,
               BootMetadata& metadataRef,
               core::FaultLog<>& faultLogRef,
               uint32_t defaultExpectedCrc,
               std::size_t defaultSlotACrcLength = 0U)
        : flashMap(flashMapRef),
          platform(platformRef),
          beacon(beaconRef),
          metadata(metadataRef),
          faultLog(faultLogRef),
          fallbackExpectedCrc(defaultExpectedCrc),
          fallbackSlotACrcLength(defaultSlotACrcLength)
    {
    }

    void run()
    {
        const core::RetainedStateRecoveryStatus recoveryStatus =
            faultLog.recoverRetainedStateWithStatus();
        const bool metadataRecovered =
            recoverBootMetadata(metadata, fallbackExpectedCrc);
        normalizeConfirmedBoot(metadata);

        if (recoveryStatus == core::RetainedStateRecoveryStatus::Corrupt)
        {
            safeFail(DetailFaultLogRecoveryFailed);
            return;
        }

        if (!metadataRecovered)
        {
            noteBootFailure(metadata, DetailFaultLogRecoveryFailed);
        }

        if (isPendingBootAttemptLimitExceeded())
        {
            safeFail(DetailBootLoopLimit);
            return;
        }

        if (hasPriorCriticalFault())
        {
            safeFail(DetailPriorCriticalFault);
            return;
        }

        const BootSlot activeSlot = activeBootSlot();
        const BootSlot fallbackSlot = otherBootSlot(activeSlot);

        uint32_t activeFailReason = 0U;
        if (isSlotBootable(activeSlot, activeFailReason))
        {
            bootSlot(activeSlot);
            return;
        }
        noteBootFailure(metadata, activeFailReason);

        uint32_t fallbackFailReason = 0U;
        if (isSlotBootable(fallbackSlot, fallbackFailReason))
        {
            activateBootSlot(metadata, fallbackSlot);
            bootSlot(fallbackSlot);
            return;
        }
        noteBootFailure(metadata, fallbackFailReason);

        safeFail(DetailNoValidFirmwareSlot);
    }

private:
    hal::IFlashMap& flashMap;
    hal::IBootPlatform& platform;
    hal::IBeacon& beacon;
    BootMetadata& metadata;
    core::FaultLog<>& faultLog;
    uint32_t fallbackExpectedCrc;
    std::size_t fallbackSlotACrcLength;

    static hal::FirmwareSlot toHalSlot(BootSlot slot)
    {
        return (slot == BootSlot::SlotB) ? hal::FirmwareSlot::SlotB :
                                           hal::FirmwareSlot::SlotA;
    }

    BootSlot activeBootSlot() const
    {
        return (metadata.active_slot == static_cast<uint32_t>(BootSlot::SlotB)) ?
            BootSlot::SlotB :
            BootSlot::SlotA;
    }

    static BootSlot otherBootSlot(BootSlot slot)
    {
        return (slot == BootSlot::SlotB) ? BootSlot::SlotA : BootSlot::SlotB;
    }

    bool isPendingBootAttemptLimitExceeded() const
    {
        return firmwareSlotState(metadata, activeBootSlot()) ==
                   static_cast<uint32_t>(FirmwareSlotState::Pending) &&
               metadata.boot_count > MaxUnconfirmedBootAttempts;
    }

    std::size_t crcLengthForSlot(BootSlot slot, uint32_t expectedCrc) const
    {
        const hal::FirmwareSlot halSlot = toHalSlot(slot);
        const std::size_t slotLength = flashMap.slotLength(halSlot);

        if (slot == BootSlot::SlotA &&
            expectedCrc == fallbackExpectedCrc &&
            fallbackSlotACrcLength > 0U &&
            fallbackSlotACrcLength <= slotLength)
        {
            return fallbackSlotACrcLength;
        }

        return slotLength;
    }

    bool slotMatchesCrc(BootSlot slot, uint32_t expectedCrc) const
    {
        const hal::FirmwareSlot halSlot = toHalSlot(slot);
        const volatile uint8_t* const application =
            reinterpret_cast<const volatile uint8_t*>(flashMap.slotBase(halSlot));
        const uint32_t runtimeCrc =
            crc32(application, crcLengthForSlot(slot, expectedCrc));

        return runtimeCrc == expectedCrc;
    }

    bool canTryDefaultSlotACrc(BootSlot slot, uint32_t expectedCrc) const
    {
        return slot == BootSlot::SlotA &&
               isExpectedCrcProvisioned(fallbackExpectedCrc) &&
               fallbackExpectedCrc != expectedCrc &&
               fallbackSlotACrcLength > 0U &&
               fallbackSlotACrcLength <= flashMap.slotLength(toHalSlot(slot));
    }

    void adoptDefaultSlotACrc()
    {
        metadata.expected_firmware_crc32 = fallbackExpectedCrc;
        metadata.slot_a_crc32 = fallbackExpectedCrc;
        metadata.slot_a_state = static_cast<uint32_t>(FirmwareSlotState::Confirmed);
        metadata.boot_count = 0U;
        commitBootMetadata(metadata);
    }

    bool isSlotBootable(BootSlot slot, uint32_t& failReason)
    {
        failReason = 0U;
        const uint32_t slotState = firmwareSlotState(metadata, slot);
        if (!isBootableFirmwareSlotState(slotState))
        {
            failReason = DetailInvalidSlotState;
            return false;
        }

        const hal::FirmwareSlot halSlot = toHalSlot(slot);
        if (!flashMap.isSlotVectorValid(halSlot))
        {
            failReason = DetailInvalidVectorTable;
            return false;
        }

        const uint32_t expectedCrc =
            expectedFirmwareCrcForSlot(metadata, slot, fallbackExpectedCrc);
        if (!isExpectedCrcProvisioned(expectedCrc))
        {
            failReason = DetailFirmwareCrcMismatch;
            return false;
        }

        if (slotMatchesCrc(slot, expectedCrc))
        {
            return true;
        }

        if (canTryDefaultSlotACrc(slot, expectedCrc) &&
            slotMatchesCrc(slot, fallbackExpectedCrc))
        {
            adoptDefaultSlotACrc();
            return true;
        }

        failReason = DetailFirmwareCrcMismatch;
        return false;
    }

    void bootSlot(BootSlot slot)
    {
        noteBootAttempt(metadata, slot);
        platform.prepareForApplicationJump();
        platform.jumpToApplication(flashMap.slotBase(toHalSlot(slot)));

#if defined(WASHIBOOT_ENABLE_TEST_HOOKS)
        return;
#else
        safeFail(DetailInvalidVectorTable);
#endif
    }

    bool hasPriorCriticalFault() const
    {
        const std::size_t eventCount = faultLog.size();
        for (std::size_t i = 0U; i < eventCount; ++i)
        {
            core::FaultEvent event = {};
            if (!faultLog.read(i, event))
            {
                return true;
            }

            if (event.type == core::FaultEventType::TaskCheckinFailure ||
                event.type == core::FaultEventType::WatchdogTimeout)
            {
                return true;
            }
        }

        return false;
    }

    void safeFail(uint32_t detailCode)
    {
        noteBootFailure(metadata, detailCode);
        (void)faultLog.record(core::FaultEventType::SafeFail,
                              0U,
                              0U,
                              detailCode,
                              0U);
        beacon.enterSafeLoop();

#if !defined(WASHIBOOT_ENABLE_TEST_HOOKS)
        for (;;)
        {
        }
#endif
    }
};

} /* namespace boot */
