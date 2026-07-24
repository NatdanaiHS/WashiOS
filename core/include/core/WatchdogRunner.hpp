#pragma once

#include <cstdint>

#include "ITiming.hpp"
#include "Watchdog.hpp"

namespace core
{

template<std::size_t RegistryCapacity = 8, std::size_t LogCapacity = 32>
class WatchdogRunner
{
public:
    WatchdogRunner(hal::ITiming& timingSource,
                   Watchdog<RegistryCapacity, LogCapacity>& watchdogMonitor,
                   uint32_t pollPeriodMs)
        : timing(timingSource),
          watchdog(watchdogMonitor),
          periodMs(pollPeriodMs),
          lastPollMs(timingSource.getSystemTick())
    {
    }

    bool runOnce()
    {
        const uint64_t nowMs = timing.getSystemTick();
        if ((nowMs - lastPollMs) < periodMs)
        {
            return false;
        }

        lastPollMs = nowMs;
        lastEvaluation = watchdog.poll();
        return true;
    }

    TaskHealthEvaluation getLastEvaluation() const
    {
        return lastEvaluation;
    }

private:
    hal::ITiming& timing;
    Watchdog<RegistryCapacity, LogCapacity>& watchdog;
    uint32_t periodMs;
    uint64_t lastPollMs;
    TaskHealthEvaluation lastEvaluation = {TaskHealthStatus::Healthy, 0U, false};
};

} /* namespace core */
