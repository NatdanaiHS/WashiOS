#pragma once

#include <cstddef>
#include <cstdint>

#include "PayloadProtocol.hpp"

namespace comms
{

enum class PayloadLinkState : uint8_t
{
    Starting,
    Online,
    Offline
};

struct PayloadLinkStats
{
    uint32_t pollsSent = 0U;
    uint32_t responsesOk = 0U;
    uint32_t timeouts = 0U;
    uint32_t crcRejects = 0U;
    uint32_t frameRejects = 0U;
    uint32_t sequenceRejects = 0U;
    uint32_t recoveries = 0U;
};

class PayloadLinkController
{
public:
    static constexpr uint32_t PollPeriodMs = 500U;
    static constexpr uint32_t ResponseTimeoutMs = 100U;
    static constexpr uint8_t OfflineThreshold = 3U;

    void service(uint32_t nowMs)
    {
        if (awaitingResponse && deadlineReached(nowMs, responseDeadlineMs))
        {
            awaitingResponse = false;
            ++linkStats.timeouts;
            if (consecutiveTimeouts < 0xFFU)
            {
                ++consecutiveTimeouts;
            }
            if (consecutiveTimeouts >= OfflineThreshold)
            {
                linkState = PayloadLinkState::Offline;
            }
        }
    }

    bool preparePoll(uint32_t nowMs, uint8_t* outBuffer, std::size_t capacity)
    {
        service(nowMs);
        if (awaitingResponse || !deadlineReached(nowMs, nextPollMs))
        {
            return false;
        }

        const uint32_t sequence = nextSequence++;
        if (!encodePollRequest(sequence, outBuffer, capacity))
        {
            return false;
        }

        expectedSequence = sequence;
        awaitingResponse = true;
        responseDeadlineMs = nowMs + ResponseTimeoutMs;
        nextPollMs = nowMs + PollPeriodMs;
        ++linkStats.pollsSent;
        return true;
    }

    PayloadValidationResult acceptResponse(const uint8_t* buffer,
                                           std::size_t length,
                                           uint32_t nowMs)
    {
        (void)nowMs;
        PayloadFrame frame = {};
        const PayloadValidationResult result = decodePayloadFrame(buffer, length, frame);
        if (result != PayloadValidationResult::Ok)
        {
            if (result == PayloadValidationResult::BadCrc)
            {
                ++linkStats.crcRejects;
            }
            else
            {
                ++linkStats.frameRejects;
            }
            return result;
        }
        if (frame.type != PayloadMessageType::TelemetryResponse)
        {
            ++linkStats.frameRejects;
            return PayloadValidationResult::BadType;
        }
        if (!awaitingResponse || frame.sequence != expectedSequence)
        {
            ++linkStats.sequenceRejects;
            return PayloadValidationResult::BadSequence;
        }
        if (!decodePayloadTelemetry(frame, latestTelemetryValue))
        {
            ++linkStats.frameRejects;
            return PayloadValidationResult::BadLength;
        }

        const bool wasOffline = linkState == PayloadLinkState::Offline;
        awaitingResponse = false;
        consecutiveTimeouts = 0U;
        linkState = PayloadLinkState::Online;
        ++linkStats.responsesOk;
        if (wasOffline)
        {
            ++linkStats.recoveries;
        }
        return PayloadValidationResult::Ok;
    }

    PayloadLinkState state() const { return linkState; }
    const PayloadLinkStats& stats() const { return linkStats; }
    const PayloadTelemetry& latestTelemetry() const { return latestTelemetryValue; }
    uint8_t consecutiveFailures() const { return consecutiveTimeouts; }
    uint32_t awaitedSequence() const { return expectedSequence; }

private:
    PayloadLinkState linkState = PayloadLinkState::Starting;
    PayloadLinkStats linkStats = {};
    PayloadTelemetry latestTelemetryValue = {};
    uint32_t nextSequence = 0U;
    uint32_t expectedSequence = 0U;
    uint32_t nextPollMs = 0U;
    uint32_t responseDeadlineMs = 0U;
    uint8_t consecutiveTimeouts = 0U;
    bool awaitingResponse = false;

    static bool deadlineReached(uint32_t nowMs, uint32_t deadlineMs)
    {
        return static_cast<int32_t>(nowMs - deadlineMs) >= 0;
    }
};

} /* namespace comms */
