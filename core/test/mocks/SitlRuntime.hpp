#pragma once

#include <cstdint>

#include "FaultLog.hpp"
#include "MockTiming.hpp"
#include "MockUart.hpp"
#include "TaskHealth.hpp"
#include "Telemetry.hpp"
#include "Watchdog.hpp"
#include "WatchdogRunner.hpp"

namespace test_mocks
{

constexpr core::TaskId SitlHeartbeatTaskId = 1U;
constexpr core::TaskId SitlTelemetryTaskId = 2U;

struct SitlSafeFailState
{
    uint32_t resetCount;
    bool fatalPanic;
};

inline void recordSitlSafeFail(void* context)
{
    SitlSafeFailState* const state = static_cast<SitlSafeFailState*>(context);
    if (state != nullptr)
    {
        ++state->resetCount;
        state->fatalPanic = true;
    }
}

class SitlHeartbeatTask
{
public:
    SitlHeartbeatTask(core::TaskHealthRegistry<>& taskRegistry,
                      hal::ITiming& timingSource)
        : registry(taskRegistry),
          timing(timingSource)
    {
    }

    bool registerHealth()
    {
        return registry.registerTask(SitlHeartbeatTaskId,
                                     DeadlineMs,
                                     true,
                                     timing.getSystemTick());
    }

    void runOnce()
    {
        ++heartbeatCount;
        (void)registry.checkIn(SitlHeartbeatTaskId, timing.getSystemTick());
    }

    uint32_t count() const
    {
        return heartbeatCount;
    }

    static constexpr uint32_t DeadlineMs = 1200U;

private:
    core::TaskHealthRegistry<>& registry;
    hal::ITiming& timing;
    uint32_t heartbeatCount = 0;
};

class SitlTelemetryTask
{
public:
    SitlTelemetryTask(core::TaskHealthRegistry<>& taskRegistry,
                      core::FaultLog<>& faults,
                      hal::ITiming& timingSource,
                      hal::IUart& telemetryTransport)
        : registry(taskRegistry),
          faultLog(faults),
          timing(timingSource),
          transport(telemetryTransport)
    {
    }

    bool registerHealth()
    {
        return registry.registerTask(SitlTelemetryTaskId,
                                     DeadlineMs,
                                     true,
                                     timing.getSystemTick());
    }

    void runOnce()
    {
        ++telemetryCount;
        (void)registry.checkIn(SitlTelemetryTaskId, timing.getSystemTick());
        sendTelemetry();
    }

    uint32_t count() const
    {
        return telemetryCount;
    }

    static constexpr uint32_t DeadlineMs = 700U;

private:
    core::TaskHealthRegistry<>& registry;
    core::FaultLog<>& faultLog;
    hal::ITiming& timing;
    hal::IUart& transport;
    uint32_t telemetryCount = 0;
    uint32_t sequence = 0U;

    void sendTelemetry()
    {
        core::TelemetryFrame frame = {};
        uint8_t buffer[core::TelemetryFrameWireSize] = {};
        std::size_t length = 0U;

        if (!core::buildTelemetryFrame(sequence,
                                       static_cast<uint32_t>(timing.getSystemTick()),
                                       registry,
                                       faultLog,
                                       frame))
        {
            return;
        }

        if (!core::serializeTelemetryFrame(frame, buffer, sizeof(buffer), length))
        {
            return;
        }

        if (transport.writeBuffer(buffer, length, 10U))
        {
            ++sequence;
        }
    }
};

class SitlRuntime
{
public:
    SitlRuntime()
        : watchdog(timing, registry, faultLog, recordSitlSafeFail, &safeFailState),
          watchdogRunner(timing, watchdog, WatchdogPeriodMs),
          heartbeatTask(registry, timing),
          telemetryTask(registry, faultLog, timing, telemetryTransport)
    {
    }

    bool initialize()
    {
        const bool heartbeatRegistered = heartbeatTask.registerHealth();
        const bool telemetryRegistered = telemetryTask.registerHealth();
        return heartbeatRegistered && telemetryRegistered;
    }

    void runNominalCycle(uint32_t elapsedMs)
    {
        timing.delayMs(elapsedMs);
        watchdogRunner.runOnce();
        heartbeatTask.runOnce();
        telemetryTask.runOnce();
        watchdogRunner.runOnce();
    }

    void runCycleWithTelemetryStalled(uint32_t elapsedMs)
    {
        timing.delayMs(elapsedMs);
        watchdogRunner.runOnce();
        heartbeatTask.runOnce();
        watchdogRunner.runOnce();
    }

    MockTiming timing;
    MockUart<256, 1024> telemetryTransport;
    core::FaultLog<> faultLog;
    core::TaskHealthRegistry<> registry;
    SitlSafeFailState safeFailState = {0U, false};
    core::Watchdog<> watchdog;
    core::WatchdogRunner<> watchdogRunner;
    SitlHeartbeatTask heartbeatTask;
    SitlTelemetryTask telemetryTask;

    static constexpr uint32_t WatchdogPeriodMs = 100U;
};

} /* namespace test_mocks */
