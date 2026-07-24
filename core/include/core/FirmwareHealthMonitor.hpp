#pragma once

#include <cstdint>

#include "FaultLog.hpp"
#include "IFirmwareHealthStore.hpp"

namespace core
{

constexpr uint32_t FirmwareHealthOk = 0x00000000UL;
constexpr uint32_t FirmwareHealthMetadataInvalid = 0xF17E0001UL;
constexpr uint32_t FirmwareHealthSlotVectorInvalid = 0xF17E0002UL;
constexpr uint32_t FirmwareHealthSlotCrcUnavailable = 0xF17E0003UL;
constexpr uint32_t FirmwareHealthSlotCrcMismatch = 0xF17E0004UL;
constexpr uint32_t FirmwareHealthBootloaderCrcUnavailable = 0xF17E0005UL;
constexpr uint32_t FirmwareHealthBootloaderCrcMismatch = 0xF17E0006UL;

struct FirmwareHealthResult
{
    bool metadataValid;
    bool fallbackSlotValid;
    bool bootloaderValid;
    uint32_t detailCode;
};

template<std::size_t FaultLogCapacity = 32>
class FirmwareHealthMonitor
{
public:
    FirmwareHealthMonitor(hal::IFirmwareHealthStore& storeRef,
                          FaultLog<FaultLogCapacity>& faultLogRef)
        : store(storeRef),
          faultLog(faultLogRef)
    {
    }

    FirmwareHealthResult checkFallbackReadiness(uint64_t timestampMs,
                                                uint8_t taskId)
    {
        FirmwareHealthResult result = {false, false, false, FirmwareHealthOk};

        if (!store.isMetadataValid())
        {
            result.detailCode = FirmwareHealthMetadataInvalid;
            recordHealthFault(result.detailCode, timestampMs, taskId);
            return result;
        }
        result.metadataValid = true;

        result.fallbackSlotValid =
            checkSlot(hal::FirmwareHealthSlot::SlotB, result.detailCode);
        if (!result.fallbackSlotValid)
        {
            recordHealthFault(result.detailCode, timestampMs, taskId);
            return result;
        }

        result.bootloaderValid = checkBootloader(result.detailCode);
        if (!result.bootloaderValid)
        {
            recordHealthFault(result.detailCode, timestampMs, taskId);
            return result;
        }

        result.detailCode = FirmwareHealthOk;
        return result;
    }

private:
    hal::IFirmwareHealthStore& store;
    FaultLog<FaultLogCapacity>& faultLog;

    bool checkSlot(hal::FirmwareHealthSlot slot, uint32_t& detailCode) const
    {
        if (!store.isSlotVectorValid(slot))
        {
            detailCode = FirmwareHealthSlotVectorInvalid;
            return false;
        }

        uint32_t expectedCrc = 0U;
        uint32_t actualCrc = 0U;
        if (!store.expectedSlotCrc(slot, expectedCrc) ||
            !store.calculateSlotCrc(slot, actualCrc))
        {
            detailCode = FirmwareHealthSlotCrcUnavailable;
            return false;
        }

        if (expectedCrc != actualCrc)
        {
            detailCode = FirmwareHealthSlotCrcMismatch;
            return false;
        }

        return true;
    }

    bool checkBootloader(uint32_t& detailCode) const
    {
        uint32_t expectedCrc = 0U;
        uint32_t actualCrc = 0U;
        if (!store.expectedBootloaderCrc(expectedCrc) ||
            !store.calculateBootloaderCrc(actualCrc))
        {
            detailCode = FirmwareHealthBootloaderCrcUnavailable;
            return false;
        }

        if (expectedCrc != actualCrc)
        {
            detailCode = FirmwareHealthBootloaderCrcMismatch;
            return false;
        }

        return true;
    }

    void recordHealthFault(uint32_t detailCode,
                           uint64_t timestampMs,
                           uint8_t taskId)
    {
        (void)faultLog.record(FaultEventType::SafeFail,
                              timestampMs,
                              taskId,
                              detailCode,
                              0U);
    }
};

} /* namespace core */
