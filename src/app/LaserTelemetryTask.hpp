#pragma once

#include <cstddef>
#include <cstdint>

#include "FaultLog.hpp"
#include "ITiming.hpp"
#include "LaserPdmTx.hpp"
#include "FsoFrame.hpp"
#include "TaskHealthReporter.hpp"
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
#if defined(WASHIOS_LASERCOM_ASCII_TEST)
    static constexpr uint8_t SyncRepeats = 3U;
    static constexpr uint32_t SyncHighUs = 100000U;
    static constexpr uint32_t SyncLowUs = 100000U;
    static constexpr uint8_t MessageRepeats = 1U;
#endif

    void ConfigureHealth(core::TaskHealthRegistry<>* registry,
                         hal::ITiming* timing,
                         core::TaskId taskId)
    {
        healthReporter.configure(registry, timing, taskId);
        healthRegistry = registry;
        timingSource = timing;
    }

    uint32_t telemetryCount() const { return laserTelemetryCounter; }

    void ConfigureTelemetry(core::FaultLog<>* faults,
                            comms::LaserPdmTx* laserTransport)
    {
        faultLog = faults;
        transport = laserTransport;
    }

    bool RunOnce()
    {
        ++laserTelemetryCounter;
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
    core::TaskHealthReporter<> healthReporter;
    hal::ITiming* timingSource = nullptr;
    core::FaultLog<>* faultLog = nullptr;
    comms::LaserPdmTx* transport = nullptr;
    uint8_t telemetrySequence = 0U;
    uint32_t laserTelemetryCounter = 0U;

    void checkIn()
    {
        (void)healthReporter.checkIn();
    }

    bool sendTelemetry()
    {
        if (healthRegistry == nullptr || timingSource == nullptr ||
            faultLog == nullptr || transport == nullptr)
        {
            return false;
        }

#if defined(WASHIOS_LASERCOM_ASCII_TEST)
        static constexpr uint8_t Message[] =
            "SVD is Diamond in Linear Algebra\r\n";

        if (!transport->sendSyncPulses(SyncRepeats, SyncHighUs, SyncLowUs))
        {
            return false;
        }

        for (uint8_t repeat = 0U; repeat < MessageRepeats; ++repeat)
        {
            if (!transport->sendBuffer(Message, sizeof(Message) - 1U))
            {
                return false;
            }
        }

        ++telemetrySequence;
        return true;
#else
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
#endif
    }
};
