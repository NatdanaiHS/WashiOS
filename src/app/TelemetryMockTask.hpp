#pragma once

#include <cstdint>

#include "FreeRTOS.h"
#include "task.h"
#include "FaultLog.hpp"
#include "ITiming.hpp"
#include "IUart.hpp"
#include "TaskHealth.hpp"
#include "Telemetry.hpp"
#include "WashiTask.hpp"

class TelemetryMockTask final : public rtos_config::WashiTask<512>
{
public:
    volatile uint32_t telemetry_count = 0;

    void ConfigureHealth(core::TaskHealthRegistry<>* registry,
                         hal::ITiming* timing,
                         core::TaskId taskId)
    {
        healthRegistry = registry;
        timingSource = timing;
        healthTaskId = taskId;
    }

    void ConfigureTelemetry(core::FaultLog<>* faults,
                            hal::IUart* transport)
    {
        faultLog = faults;
        telemetryTransport = transport;
    }

protected:
    void Run() override
    {
        for (;;)
        {
            ++telemetry_count;
            checkIn();
            sendTelemetry();
            vTaskDelay(pdMS_TO_TICKS(500));
        }
    }

private:
    core::TaskHealthRegistry<>* healthRegistry = nullptr;
    hal::ITiming* timingSource = nullptr;
    core::FaultLog<>* faultLog = nullptr;
    hal::IUart* telemetryTransport = nullptr;
    core::TaskId healthTaskId = 0U;
    uint32_t telemetrySequence = 0U;

    void checkIn()
    {
        if (healthRegistry != nullptr && timingSource != nullptr)
        {
            (void)healthRegistry->checkIn(healthTaskId, timingSource->getSystemTick());
        }
    }

    void sendTelemetry()
    {
        if (healthRegistry == nullptr || timingSource == nullptr ||
            faultLog == nullptr || telemetryTransport == nullptr)
        {
            return;
        }

        core::TelemetryFrame frame = {};
        uint8_t buffer[core::TelemetryFrameWireSize] = {};
        std::size_t length = 0U;

        if (!core::buildTelemetryFrame(telemetrySequence,
                                       static_cast<uint32_t>(timingSource->getSystemTick()),
                                       *healthRegistry,
                                       *faultLog,
                                       frame))
        {
            return;
        }

        if (!core::serializeTelemetryFrame(frame, buffer, sizeof(buffer), length))
        {
            return;
        }

        if (telemetryTransport->writeBuffer(buffer, length, 10U))
        {
            ++telemetrySequence;
        }
    }
};
