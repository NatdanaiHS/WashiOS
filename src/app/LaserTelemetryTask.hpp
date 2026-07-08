#pragma once

#include <cstddef>
#include <cstdint>

#include "FaultLog.hpp"
#include "ITiming.hpp"
#include "LaserPdmTx.hpp"
#include "FsoFrame.hpp"
#include "TaskHealth.hpp"
#include "Telemetry.hpp"

#if !defined(WASHIOS_ENABLE_TEST_HOOKS)
#include "FreeRTOS.h"
#include "task.h"
#include "WashiTask.hpp"
#endif

#if defined(WASHIOS_ENABLE_TEST_HOOKS)
class LaserTelemetryTask final
#else
class LaserTelemetryTask final : public rtos_config::WashiTask<768>
#endif
{
public:
    static constexpr uint32_t PeriodMs = 1000U;
    static constexpr uint8_t FrameRepeats = 4U;

    volatile uint32_t laserTelemetryCount = 0U;

    void ConfigureHealth(core::TaskHealthRegistry<>* registry,
                         hal::ITiming* timing,
                         core::TaskId taskId)
    {
        healthRegistry = registry;
        timingSource = timing;
        healthTaskId = taskId;
    }

    void ConfigureTelemetry(core::FaultLog<>* faults,
                            comms::LaserPdmTx* laserTransport)
    {
        faultLog = faults;
        transport = laserTransport;
    }

    bool RunOnce()
    {
        ++laserTelemetryCount;
        checkIn();
        return sendTelemetry();
    }

#if !defined(WASHIOS_ENABLE_TEST_HOOKS)
protected:
    void Run() override
    {
        for (;;)
        {
            (void)RunOnce();
            vTaskDelay(pdMS_TO_TICKS(PeriodMs));
        }
    }
#endif

private:
    core::TaskHealthRegistry<>* healthRegistry = nullptr;
    hal::ITiming* timingSource = nullptr;
    core::FaultLog<>* faultLog = nullptr;
    comms::LaserPdmTx* transport = nullptr;
    core::TaskId healthTaskId = 0U;
    uint8_t telemetrySequence = 0U;

    void checkIn()
    {
        if (healthRegistry != nullptr && timingSource != nullptr)
        {
            (void)healthRegistry->checkIn(healthTaskId, timingSource->getSystemTick());
        }
    }

    bool sendTelemetry()
    {
        if (healthRegistry == nullptr || timingSource == nullptr ||
            faultLog == nullptr || transport == nullptr)
        {
            return false;
        }

        core::TelemetryFrame telemetryFrame = {};
        uint8_t telemetryBuffer[core::TelemetryFrameWireSize] = {};
        std::size_t telemetryLength = 0U;

        if (!core::buildTelemetryFrame(telemetrySequence,
                                       static_cast<uint32_t>(timingSource->getSystemTick()),
                                       *healthRegistry,
                                       *faultLog,
                                       telemetryFrame))
        {
            return false;
        }

        if (!core::serializeTelemetryFrame(telemetryFrame,
                                           telemetryBuffer,
                                           sizeof(telemetryBuffer),
                                           telemetryLength))
        {
            return false;
        }

        comms::FsoFrame fsoFrame = {};
        uint8_t frameBuffer[comms::FsoMaxWireSize] = {};
        std::size_t frameLength = 0U;

        if (!comms::buildFsoDataFrame(telemetrySequence,
                                      telemetryBuffer,
                                      telemetryLength,
                                      fsoFrame))
        {
            return false;
        }

        if (!comms::serializeFsoFrame(fsoFrame,
                                      frameBuffer,
                                      sizeof(frameBuffer),
                                      frameLength))
        {
            return false;
        }

        for (uint8_t repeat = 0U; repeat < FrameRepeats; ++repeat)
        {
            if (!transport->sendBuffer(frameBuffer, frameLength))
            {
                return false;
            }
        }

        ++telemetrySequence;
        return true;
    }
};
