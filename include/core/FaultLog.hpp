#pragma once

#include <cstddef>
#include <cstdint>

#include "CriticalSection.hpp"

namespace core
{

enum class FaultEventType
{
    TmrCorrection,
    TmrUnrecoverable,
    WatchdogTimeout,
    TaskCheckinFailure,
    StackOverflow,
    AssertFailure,
    SafeFail
};

struct FaultEvent
{
    FaultEventType type;
    uint64_t timestampMs;
    uint8_t taskId;
    uint32_t detailCode;
    uint32_t correctionCount;
};

template<std::size_t Capacity = 32>
class FaultLog
{
public:
    bool record(FaultEventType type,
                uint64_t timestampMs,
                uint8_t taskId,
                uint32_t detailCode,
                uint32_t correctionCount)
    {
        if (Capacity == 0U)
        {
            return false;
        }

        taskENTER_CRITICAL();
        entries[writeIndex] = {type, timestampMs, taskId, detailCode, correctionCount};
        writeIndex = advance(writeIndex);
        ++totalCount;
        if (storedCount < Capacity)
        {
            ++storedCount;
        }
        taskEXIT_CRITICAL();
        return true;
    }

    void clear()
    {
        writeIndex = 0;
        storedCount = 0;
        totalCount = 0;
    }

    std::size_t size() const
    {
        return storedCount;
    }

    uint32_t totalEvents() const
    {
        return totalCount;
    }

    bool read(std::size_t index, FaultEvent& outEvent) const
    {
        taskENTER_CRITICAL();
        if (index >= storedCount || Capacity == 0U)
        {
            taskEXIT_CRITICAL();
            return false;
        }

        outEvent = entries[physicalIndex(index)];
        taskEXIT_CRITICAL();
        return true;
    }

    bool latest(FaultEvent& outEvent) const
    {
        taskENTER_CRITICAL();
        if (storedCount == 0U || Capacity == 0U)
        {
            taskEXIT_CRITICAL();
            return false;
        }

        const std::size_t latestIndex = (writeIndex == 0U) ? (Capacity - 1U) : (writeIndex - 1U);
        outEvent = entries[latestIndex];
        taskEXIT_CRITICAL();
        return true;
    }

private:
    FaultEvent entries[Capacity == 0U ? 1U : Capacity] = {};
    std::size_t writeIndex = 0;
    std::size_t storedCount = 0;
    uint32_t totalCount = 0;

    static std::size_t advance(std::size_t index)
    {
        ++index;
        return (index >= Capacity) ? 0U : index;
    }

    std::size_t physicalIndex(std::size_t logicalIndex) const
    {
        if (storedCount < Capacity)
        {
            return logicalIndex;
        }

        std::size_t index = writeIndex + logicalIndex;
        if (index >= Capacity)
        {
            index -= Capacity;
        }
        return index;
    }
};

} /* namespace core */
