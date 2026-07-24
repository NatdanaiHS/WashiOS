#pragma once

#include <cstddef>
#include <cstdint>

#include "FaultLog.hpp"
#include "TaskHealth.hpp"

namespace core
{

constexpr uint8_t TelemetrySync0 = 0x4BU;
constexpr uint8_t TelemetrySync1 = 0x34U;
constexpr uint8_t TelemetryVersion = 1U;
constexpr std::size_t TelemetryFrameWireSize = 28U;

#if defined(__GNUC__)
#define WASHIOS_PACKED __attribute__((packed))
#else
#define WASHIOS_PACKED
#endif

struct WASHIOS_PACKED TelemetryFrame
{
    uint8_t sync0;
    uint8_t sync1;
    uint8_t version;
    uint8_t frameSize;
    uint32_t sequence;
    uint32_t uptimeMs;
    uint32_t taskHealthMask;
    uint32_t faultEventCount;
    uint8_t latestFaultType;
    uint8_t latestFaultTaskId;
    uint16_t reserved;
    uint32_t crc32;
};

#undef WASHIOS_PACKED

static_assert(sizeof(TelemetryFrame) == TelemetryFrameWireSize,
              "TelemetryFrame must stay fixed-size and packed");

inline void writeU16Le(uint8_t* buffer, std::size_t offset, uint16_t value)
{
    buffer[offset] = static_cast<uint8_t>(value & 0xFFU);
    buffer[offset + 1U] = static_cast<uint8_t>((value >> 8U) & 0xFFU);
}

inline void writeU32Le(uint8_t* buffer, std::size_t offset, uint32_t value)
{
    buffer[offset] = static_cast<uint8_t>(value & 0xFFU);
    buffer[offset + 1U] = static_cast<uint8_t>((value >> 8U) & 0xFFU);
    buffer[offset + 2U] = static_cast<uint8_t>((value >> 16U) & 0xFFU);
    buffer[offset + 3U] = static_cast<uint8_t>((value >> 24U) & 0xFFU);
}

inline uint32_t readU32Le(const uint8_t* buffer, std::size_t offset)
{
    return static_cast<uint32_t>(buffer[offset]) |
           (static_cast<uint32_t>(buffer[offset + 1U]) << 8U) |
           (static_cast<uint32_t>(buffer[offset + 2U]) << 16U) |
           (static_cast<uint32_t>(buffer[offset + 3U]) << 24U);
}

inline uint32_t crc32(const uint8_t* data, std::size_t length)
{
    static constexpr uint32_t Crc32NibbleTable[16] = {
        0x00000000UL, 0x1DB71064UL, 0x3B6E20C8UL, 0x26D930ACUL,
        0x76DC4190UL, 0x6B6B51F4UL, 0x4DB26158UL, 0x5005713CUL,
        0xEDB88320UL, 0xF00F9344UL, 0xD6D6A3E8UL, 0xCB61B38CUL,
        0x9B64C2B0UL, 0x86D3D2D4UL, 0xA00AE278UL, 0xBDBDF21CUL
    };

    uint32_t crc = 0xFFFFFFFFUL;

    for (std::size_t i = 0; i < length; ++i)
    {
        crc ^= static_cast<uint32_t>(data[i]);
        crc = (crc >> 4U) ^ Crc32NibbleTable[crc & 0x0FUL];
        crc = (crc >> 4U) ^ Crc32NibbleTable[crc & 0x0FUL];
    }

    return ~crc;
}

inline bool serializeTelemetryFrame(const TelemetryFrame& frame,
                                    uint8_t* outBuffer,
                                    std::size_t outCapacity,
                                    std::size_t& outLength)
{
    if (outBuffer == nullptr || outCapacity < TelemetryFrameWireSize)
    {
        outLength = 0U;
        return false;
    }

    outBuffer[0] = frame.sync0;
    outBuffer[1] = frame.sync1;
    outBuffer[2] = frame.version;
    outBuffer[3] = frame.frameSize;
    writeU32Le(outBuffer, 4U, frame.sequence);
    writeU32Le(outBuffer, 8U, frame.uptimeMs);
    writeU32Le(outBuffer, 12U, frame.taskHealthMask);
    writeU32Le(outBuffer, 16U, frame.faultEventCount);
    outBuffer[20] = frame.latestFaultType;
    outBuffer[21] = frame.latestFaultTaskId;
    writeU16Le(outBuffer, 22U, frame.reserved);
    writeU32Le(outBuffer, 24U, frame.crc32);
    outLength = TelemetryFrameWireSize;
    return true;
}

inline uint32_t computeTelemetryCrc(TelemetryFrame frame)
{
    uint8_t buffer[TelemetryFrameWireSize] = {};
    std::size_t length = 0U;
    frame.crc32 = 0U;
    (void)serializeTelemetryFrame(frame, buffer, sizeof(buffer), length);
    return crc32(buffer, TelemetryFrameWireSize - sizeof(uint32_t));
}

inline bool finalizeTelemetryFrame(TelemetryFrame& frame)
{
    frame.sync0 = TelemetrySync0;
    frame.sync1 = TelemetrySync1;
    frame.version = TelemetryVersion;
    frame.frameSize = static_cast<uint8_t>(TelemetryFrameWireSize);
    frame.crc32 = computeTelemetryCrc(frame);
    return true;
}

inline bool validateTelemetryBuffer(const uint8_t* buffer, std::size_t length)
{
    if (buffer == nullptr || length != TelemetryFrameWireSize)
    {
        return false;
    }

    if (buffer[0] != TelemetrySync0 || buffer[1] != TelemetrySync1 ||
        buffer[2] != TelemetryVersion || buffer[3] != TelemetryFrameWireSize)
    {
        return false;
    }

    const uint32_t expected = readU32Le(buffer, 24U);
    const uint32_t actual = crc32(buffer, TelemetryFrameWireSize - sizeof(uint32_t));
    return expected == actual;
}

template<std::size_t RegistryCapacity, std::size_t LogCapacity>
inline bool buildTelemetryFrame(uint32_t sequence,
                                uint32_t uptimeMs,
                                const TaskHealthRegistry<RegistryCapacity>& registry,
                                const FaultLog<LogCapacity>& faultLog,
                                TelemetryFrame& outFrame)
{
    FaultEvent latest = {};
    const bool hasFault = faultLog.latest(latest);

    outFrame.sync0 = TelemetrySync0;
    outFrame.sync1 = TelemetrySync1;
    outFrame.version = TelemetryVersion;
    outFrame.frameSize = static_cast<uint8_t>(TelemetryFrameWireSize);
    outFrame.sequence = sequence;
    outFrame.uptimeMs = uptimeMs;
    outFrame.taskHealthMask = registry.healthSummaryMask();
    outFrame.faultEventCount = faultLog.totalEvents();
    outFrame.latestFaultType = hasFault ? static_cast<uint8_t>(latest.type) : 0xFFU;
    outFrame.latestFaultTaskId = hasFault ? latest.taskId : 0xFFU;
    outFrame.reserved = 0U;
    outFrame.crc32 = 0U;
    return finalizeTelemetryFrame(outFrame);
}

} /* namespace core */
