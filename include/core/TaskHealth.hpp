#pragma once

#include <cstddef>
#include <cstdint>

#include "FaultLog.hpp"

namespace core
{

using TaskId = uint8_t;

enum class TaskHealthStatus
{
    Healthy,
    NonCriticalFailure,
    CriticalFailure
};

struct TaskHealthEvaluation
{
    TaskHealthStatus status;
    TaskId firstFailedTaskId;
    bool newlyReportedFailure;
};

struct TaskHealthEntry
{
    TaskId id;
    uint32_t deadlineMs;
    uint64_t lastCheckInMs;
    bool critical;
    bool registered;
    bool healthy;
    bool violationReported;
};

template<std::size_t Capacity = 8>
class TaskHealthRegistry
{
public:
    bool registerTask(TaskId id, uint32_t deadlineMs, bool critical, uint64_t nowMs)
    {
        if (deadlineMs == 0U)
        {
            return false;
        }

        TaskHealthEntry* existing = findMutable(id);
        if (existing != nullptr)
        {
            *existing = {id, deadlineMs, nowMs, critical, true, true, false};
            return true;
        }

        for (std::size_t i = 0; i < Capacity; ++i)
        {
            if (!entries[i].registered)
            {
                entries[i] = {id, deadlineMs, nowMs, critical, true, true, false};
                ++registeredCount;
                return true;
            }
        }

        return false;
    }

    bool checkIn(TaskId id, uint64_t nowMs)
    {
        taskENTER_CRITICAL();
        TaskHealthEntry* entry = findMutable(id);
        if (entry == nullptr)
        {
            taskEXIT_CRITICAL();
            return false;
        }

        entry->lastCheckInMs = nowMs;
        entry->healthy = true;
        entry->violationReported = false;
        taskEXIT_CRITICAL();
        return true;
    }

    template<std::size_t LogCapacity>
    TaskHealthEvaluation evaluate(uint64_t nowMs, FaultLog<LogCapacity>& faultLog)
    {
        TaskHealthEvaluation result = {TaskHealthStatus::Healthy, 0U, false};
        TaskId failureTaskIds[Capacity == 0U ? 1U : Capacity] = {};
        uint32_t failureDeadlines[Capacity == 0U ? 1U : Capacity] = {};
        std::size_t failureCount = 0U;

        taskENTER_CRITICAL();
        for (std::size_t i = 0; i < Capacity; ++i)
        {
            if (!entries[i].registered)
            {
                continue;
            }

            const uint32_t deltaMs = static_cast<uint32_t>(nowMs - entries[i].lastCheckInMs);
            const bool expired = deltaMs > entries[i].deadlineMs;
            if (!expired)
            {
                continue;
            }

            entries[i].healthy = false;

            if (!entries[i].violationReported)
            {
                entries[i].violationReported = true;
                result.newlyReportedFailure = true;
                if (failureCount < Capacity)
                {
                    failureTaskIds[failureCount] = entries[i].id;
                    failureDeadlines[failureCount] = entries[i].deadlineMs;
                    ++failureCount;
                }
            }

            if (entries[i].critical)
            {
                if (result.status != TaskHealthStatus::CriticalFailure)
                {
                    result.status = TaskHealthStatus::CriticalFailure;
                    result.firstFailedTaskId = entries[i].id;
                }
            }
            else if (result.status == TaskHealthStatus::Healthy)
            {
                result.status = TaskHealthStatus::NonCriticalFailure;
                result.firstFailedTaskId = entries[i].id;
            }
        }
        taskEXIT_CRITICAL();

        for (std::size_t i = 0U; i < failureCount; ++i)
        {
            (void)faultLog.record(FaultEventType::TaskCheckinFailure,
                                  nowMs,
                                  failureTaskIds[i],
                                  failureDeadlines[i],
                                  0U);
        }

        return result;
    }

    std::size_t size() const
    {
        return registeredCount;
    }

    bool isHealthy(TaskId id) const
    {
        const TaskHealthEntry* entry = find(id);
        return entry != nullptr && entry->healthy;
    }

    uint32_t healthSummaryMask() const
    {
        uint32_t mask = 0U;

        for (std::size_t i = 0; i < Capacity; ++i)
        {
            if (entries[i].registered && entries[i].healthy && entries[i].id < 32U)
            {
                mask |= (1UL << entries[i].id);
            }
        }

        return mask;
    }

private:
    TaskHealthEntry entries[Capacity == 0U ? 1U : Capacity] = {};
    std::size_t registeredCount = 0;

    TaskHealthEntry* findMutable(TaskId id)
    {
        for (std::size_t i = 0; i < Capacity; ++i)
        {
            if (entries[i].registered && entries[i].id == id)
            {
                return &entries[i];
            }
        }
        return nullptr;
    }

    const TaskHealthEntry* find(TaskId id) const
    {
        for (std::size_t i = 0; i < Capacity; ++i)
        {
            if (entries[i].registered && entries[i].id == id)
            {
                return &entries[i];
            }
        }
        return nullptr;
    }
};

} /* namespace core */
