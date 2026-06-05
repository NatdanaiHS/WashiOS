#pragma once

#include <cstddef>
#include <cstdint>

#include "ITiming.hpp"
#include "FaultLog.hpp"
#include "TaskHealth.hpp"

namespace core
{

using SafeFailCallback = void (*)(void* context);
using HardwareWatchdogRefreshCallback = void (*)(void* context);

template<std::size_t RegistryCapacity = 8, std::size_t LogCapacity = 32>
class Watchdog
{
public:
    Watchdog(hal::ITiming& timingSource,
             TaskHealthRegistry<RegistryCapacity>& taskRegistry,
             FaultLog<LogCapacity>& faultLog,
             SafeFailCallback callback,
             void* callbackContext,
             HardwareWatchdogRefreshCallback refreshCallback = nullptr,
             void* refreshContext = nullptr)
        : timing(timingSource),
          registry(taskRegistry),
          log(faultLog),
          safeFailCallback(callback),
          safeFailContext(callbackContext),
          hardwareRefreshCallback(refreshCallback),
          hardwareRefreshContext(refreshContext)
    {
    }

    TaskHealthEvaluation poll()
    {
        const uint64_t nowMs = timing.getSystemTick();
        const TaskHealthEvaluation result = registry.evaluate(nowMs, log);

        if (result.status == TaskHealthStatus::CriticalFailure &&
            result.newlyReportedFailure)
        {
            (void)log.record(FaultEventType::WatchdogTimeout,
                             nowMs,
                             result.firstFailedTaskId,
                             0U,
                             0U);
            (void)log.record(FaultEventType::SafeFail,
                             nowMs,
                             result.firstFailedTaskId,
                             0U,
                             0U);
            if (safeFailCallback != nullptr)
            {
                safeFailCallback(safeFailContext);
            }
        }

        if (registry.areAllCriticalTasksHealthy() &&
            hardwareRefreshCallback != nullptr)
        {
            hardwareRefreshCallback(hardwareRefreshContext);
        }

        return result;
    }

private:
    hal::ITiming& timing;
    TaskHealthRegistry<RegistryCapacity>& registry;
    FaultLog<LogCapacity>& log;
    SafeFailCallback safeFailCallback;
    void* safeFailContext;
    HardwareWatchdogRefreshCallback hardwareRefreshCallback;
    void* hardwareRefreshContext;
};

} /* namespace core */
