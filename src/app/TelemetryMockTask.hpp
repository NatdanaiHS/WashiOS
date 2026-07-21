#pragma once

#include <cstdint>

#include "FreeRTOS.h"
#include "task.h"
#include "FaultLog.hpp"
#include "ITiming.hpp"
#include "IUart.hpp"
#include "TaskHealthReporter.hpp"
#include "Telemetry.hpp"
#include "WashiTask.hpp"

class TelemetryMockTask final : public rtos_config::WashiTask<512>
{
public:
    void ConfigureHealth(core::TaskHealthRegistry<>* registry,
                         hal::ITiming* timing,
                         core::TaskId taskId)
    {
        healthReporter.configure(registry, timing, taskId);
        healthRegistry = registry;
        timingSource = timing;
    }

    uint32_t telemetryCount() const { return telemetryCounter; }

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
            ++telemetryCounter;
            checkIn();
            sendTelemetry();
            vTaskDelay(pdMS_TO_TICKS(500));
        }
    }

private:
    core::TaskHealthRegistry<>* healthRegistry = nullptr;
    core::TaskHealthReporter<> healthReporter;
    hal::ITiming* timingSource = nullptr;
    core::FaultLog<>* faultLog = nullptr;
    hal::IUart* telemetryTransport = nullptr;
    uint32_t telemetrySequence = 0U;
    uint32_t telemetryCounter = 0U;

    void checkIn()
    {
        (void)healthReporter.checkIn();
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
