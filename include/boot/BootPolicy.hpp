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

class BootPolicy
{
public:
    BootPolicy(hal::IFlashMap& flashMapRef,
               hal::IBootPlatform& platformRef,
               hal::IBeacon& beaconRef,
               BootMetadata& metadataRef,
               core::FaultLog<>& faultLogRef,
               uint32_t defaultExpectedCrc)
        : flashMap(flashMapRef),
          platform(platformRef),
          beacon(beaconRef),
          metadata(metadataRef),
          faultLog(faultLogRef),
          fallbackExpectedCrc(defaultExpectedCrc)
    {
    }

    void run()
    {
        const core::RetainedStateRecoveryStatus recoveryStatus =
            faultLog.recoverRetainedStateWithStatus();
        (void)recoverBootMetadata(metadata, fallbackExpectedCrc);
        normalizeConfirmedBoot(metadata);

        if (recoveryStatus == core::RetainedStateRecoveryStatus::Corrupt)
        {
            safeFail(DetailFaultLogRecoveryFailed);
        }

        if (metadata.boot_count > MaxUnconfirmedBootAttempts)
        {
            safeFail(DetailBootLoopLimit);
        }

        if (hasPriorCriticalFault())
        {
            safeFail(DetailPriorCriticalFault);
        }

        if (!flashMap.isApplicationVectorValid())
        {
            safeFail(DetailInvalidVectorTable);
        }

        const volatile uint8_t* const application =
            reinterpret_cast<const volatile uint8_t*>(flashMap.applicationBase());
        const uint32_t runtimeCrc = crc32(application, flashMap.applicationLength());
        const uint32_t expectedCrc = expectedFirmwareCrc(metadata, fallbackExpectedCrc);

        if (runtimeCrc != expectedCrc)
        {
            safeFail(DetailFirmwareCrcMismatch);
        }

        noteBootAttempt(metadata);
        platform.prepareForApplicationJump();
        platform.jumpToApplication(flashMap.applicationBase());

        safeFail(DetailInvalidVectorTable);
    }

private:
    hal::IFlashMap& flashMap;
    hal::IBootPlatform& platform;
    hal::IBeacon& beacon;
    BootMetadata& metadata;
    core::FaultLog<>& faultLog;
    uint32_t fallbackExpectedCrc;

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
        (void)faultLog.record(core::FaultEventType::SafeFail,
                              0U,
                              0U,
                              detailCode,
                              0U);
        beacon.enterSafeLoop();

        for (;;)
        {
        }
    }
};

} /* namespace boot */
