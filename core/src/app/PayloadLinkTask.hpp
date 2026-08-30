#pragma once

#include <cstddef>
#include <cstdint>

#include "FixedTextWriter.hpp"
#include "ITiming.hpp"
#include "IGPIO.hpp"
#include "IUart.hpp"
#include "PayloadLinkController.hpp"
#include "TaskHealthReporter.hpp"
#include "WashiTask.hpp"

class PayloadLinkTask final : public rtos_config::WashiTask<768>
{
public:
    static constexpr uint32_t LoopPeriodMs = 1U;
    static constexpr uint32_t HealthPeriodMs = 100U;
    static constexpr uint32_t StatusPeriodMs = 5000U;
    static constexpr uint32_t UartTimeoutMs = 10U;
    static constexpr std::size_t MaxBytesPerCycle = 64U;

    PayloadLinkTask(hal::IUart& payloadTransport,
                    hal::IUart& consoleTransport,
                    hal::ITiming& timingSource,
                    core::TaskHealthRegistry<>& registry,
                    core::TaskId taskId,
                    hal::IGPIO* timeoutMarkerPin = nullptr)
        : payloadUart(payloadTransport),
          consoleUart(consoleTransport),
          timing(timingSource),
          timeoutMarker(timeoutMarkerPin)
    {
        healthReporter.configure(&registry, &timingSource, taskId);
    }

protected:
    void Run() override
    {
        logLiteral("[OBC] PAYLOAD_LINK_START baud=115200\r\n");
        for (;;)
        {
            clearTimeoutMarker();
            const uint32_t nowMs = static_cast<uint32_t>(timing.getSystemTick());
            receiveFrames(nowMs);
            serviceController(nowMs);
            sendPoll(nowMs);
            reportHealth(nowMs);
            reportStatus(nowMs);
            vTaskDelay(pdMS_TO_TICKS(LoopPeriodMs));
        }
    }

private:
    hal::IUart& payloadUart;
    hal::IUart& consoleUart;
    hal::ITiming& timing;
    hal::IGPIO* timeoutMarker;
    core::TaskHealthReporter<> healthReporter;
    comms::PayloadLinkController controller;
    comms::PayloadFrameDecoder decoder;
    uint32_t nextHealthMs = 0U;
    uint32_t nextStatusMs = StatusPeriodMs;
    comms::PayloadValidationResult lastRejection =
        comms::PayloadValidationResult::Ok;
    bool pollWriteFailureLogged = false;
    bool timeoutMarkerHigh = false;

    void clearTimeoutMarker()
    {
        if (timeoutMarker != nullptr && timeoutMarkerHigh)
        {
            timeoutMarker->setLow();
            timeoutMarkerHigh = false;
        }
    }

    void markTimeoutDetection()
    {
        if (timeoutMarker != nullptr)
        {
            /* Rising edge follows the timeout state update and precedes logging. */
            timeoutMarker->setHigh();
            timeoutMarkerHigh = true;
        }
    }

    void receiveFrames(uint32_t nowMs)
    {
        for (std::size_t count = 0U;
             count < MaxBytesPerCycle && payloadUart.available() > 0U;
             ++count)
        {
            uint8_t byte = 0U;
            if (!payloadUart.readBuffer(&byte, 1U, 1U))
            {
                return;
            }

            const comms::PayloadDecodeEvent event = decoder.consume(byte);
            if (event == comms::PayloadDecodeEvent::FrameReady)
            {
                const comms::PayloadLinkState previousState = controller.state();
                const comms::PayloadValidationResult result =
                    controller.acceptResponse(decoder.frameData(), comms::PayloadWireSize, nowMs);
                if (result == comms::PayloadValidationResult::Ok)
                {
                    lastRejection = comms::PayloadValidationResult::Ok;
                    logAccepted();
                    if (previousState == comms::PayloadLinkState::Offline)
                    {
                        logRecovery();
                    }
                    else if (previousState == comms::PayloadLinkState::Starting)
                    {
                        logOnline();
                    }
                }
                else
                {
                    logRejection(result);
                }
            }
            else if (event == comms::PayloadDecodeEvent::FrameRejected)
            {
                const comms::PayloadValidationResult result =
                    controller.acceptResponse(decoder.frameData(), comms::PayloadWireSize, nowMs);
                logRejection(result);
            }
        }
    }

    void serviceController(uint32_t nowMs)
    {
        const uint32_t previousTimeouts = controller.stats().timeouts;
        const comms::PayloadLinkState previousState = controller.state();
        controller.service(nowMs);
        if (controller.stats().timeouts != previousTimeouts)
        {
            markTimeoutDetection();
            if (previousState != comms::PayloadLinkState::Offline &&
                controller.state() == comms::PayloadLinkState::Offline)
            {
                logOffline();
            }
            else if (previousState != comms::PayloadLinkState::Offline)
            {
                logTimeout();
            }
        }
    }

    void sendPoll(uint32_t nowMs)
    {
        uint8_t request[comms::PayloadWireSize] = {};
        if (controller.preparePoll(nowMs, request, sizeof(request)))
        {
            const bool sent = payloadUart.writeBuffer(request, sizeof(request), UartTimeoutMs);
            if (!sent && !pollWriteFailureLogged)
            {
                logPollWriteFailure();
                pollWriteFailureLogged = true;
            }
            else if (sent)
            {
                pollWriteFailureLogged = false;
            }
        }
    }

    void reportHealth(uint32_t nowMs)
    {
        if (static_cast<int32_t>(nowMs - nextHealthMs) >= 0)
        {
            (void)healthReporter.checkIn();
            nextHealthMs = nowMs + HealthPeriodMs;
        }
    }

    void reportStatus(uint32_t nowMs)
    {
        if (static_cast<int32_t>(nowMs - nextStatusMs) < 0)
        {
            return;
        }

        const comms::PayloadLinkStats& stats = controller.stats();
        core::FixedTextWriter<192U> line;
        (void)line.append("[OBC] PAYLOAD_STATUS state=");
        (void)line.append(stateName(controller.state()));
        (void)line.append(" polls=");
        (void)line.appendU32(stats.pollsSent);
        (void)line.append(" ok=");
        (void)line.appendU32(stats.responsesOk);
        (void)line.append(" timeout=");
        (void)line.appendU32(stats.timeouts);
        (void)line.append(" crc=");
        (void)line.appendU32(stats.crcRejects);
        (void)line.append(" seq=");
        (void)line.appendU32(stats.sequenceRejects);
        (void)line.append(" recovery=");
        (void)line.appendU32(stats.recoveries);
        (void)line.append(" heartbeat=OK watchdog=OK\r\n");
        writeLine(line);
        nextStatusMs = nowMs + StatusPeriodMs;
    }

    void logOnline()
    {
        const comms::PayloadTelemetry& telemetry = controller.latestTelemetry();
        core::FixedTextWriter<128U> line;
        (void)line.append("[OBC] PAYLOAD_ONLINE seq=");
        (void)line.appendU32(controller.awaitedSequence());
        (void)line.append(" sample=");
        (void)line.appendU32(telemetry.sampleCounter);
        (void)line.append(" sensor=");
        (void)line.appendI32(telemetry.simulatedSensorMilliunits);
        (void)line.append(" mode=");
        (void)line.appendU32(static_cast<uint32_t>(telemetry.mode));
        (void)line.append("\r\n");
        writeLine(line);
    }

    void logAccepted()
    {
        core::FixedTextWriter<88U> line;
        (void)line.append("[OBC] PAYLOAD_ACCEPTED seq=");
        (void)line.appendU32(controller.awaitedSequence());
        (void)line.append(" mode=");
        (void)line.appendU32(static_cast<uint32_t>(controller.latestTelemetry().mode));
        (void)line.append("\r\n");
        writeLine(line);
    }

    void logRecovery()
    {
        core::FixedTextWriter<72U> line;
        (void)line.append("[OBC] PAYLOAD_RECOVERED recoveries=");
        (void)line.appendU32(controller.stats().recoveries);
        (void)line.append("\r\n");
        writeLine(line);
    }

    void logRejection(comms::PayloadValidationResult result)
    {
        if (result == lastRejection)
        {
            return;
        }
        lastRejection = result;

        core::FixedTextWriter<80U> line;
        (void)line.append("[OBC] PAYLOAD_REJECT reason=");
        (void)line.append(validationName(result));
        (void)line.append("\r\n");
        writeLine(line);
    }

    void logTimeout()
    {
        core::FixedTextWriter<96U> line;
        (void)line.append("[OBC] PAYLOAD_TIMEOUT consecutive=");
        (void)line.appendU32(controller.consecutiveFailures());
        (void)line.append("\r\n");
        writeLine(line);
    }

    void logOffline()
    {
        core::FixedTextWriter<112U> line;
        (void)line.append("[OBC] PAYLOAD_OFFLINE consecutive=");
        (void)line.appendU32(controller.consecutiveFailures());
        (void)line.append(" heartbeat=OK watchdog=OK\r\n");
        writeLine(line);
    }

    void logPollWriteFailure()
    {
        core::FixedTextWriter<80U> line;
        (void)line.append("[OBC] PAYLOAD_POLL_WRITE_FAILED seq=");
        (void)line.appendU32(controller.awaitedSequence());
        (void)line.append("\r\n");
        writeLine(line);
    }

    static const char* stateName(comms::PayloadLinkState state)
    {
        switch (state)
        {
        case comms::PayloadLinkState::Starting: return "STARTING";
        case comms::PayloadLinkState::Online: return "ONLINE";
        case comms::PayloadLinkState::Offline: return "OFFLINE";
        default: return "UNKNOWN";
        }
    }

    static const char* validationName(comms::PayloadValidationResult result)
    {
        switch (result)
        {
        case comms::PayloadValidationResult::BadCrc: return "CRC";
        case comms::PayloadValidationResult::BadSequence: return "SEQUENCE";
        case comms::PayloadValidationResult::BadVersion: return "VERSION";
        case comms::PayloadValidationResult::BadLength: return "LENGTH";
        case comms::PayloadValidationResult::BadType: return "TYPE";
        case comms::PayloadValidationResult::BadSync: return "SYNC";
        default: return "FRAME";
        }
    }

    template<std::size_t Capacity>
    void writeLine(const core::FixedTextWriter<Capacity>& line)
    {
        (void)consoleUart.writeBuffer(line.data(), line.size(), UartTimeoutMs);
    }

    void logLiteral(const char* text)
    {
        core::FixedTextWriter<96U> line;
        (void)line.append(text);
        writeLine(line);
    }
};
