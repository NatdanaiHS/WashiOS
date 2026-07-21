#pragma once

#include <cstddef>
#include <cstdint>

namespace comms
{

constexpr uint8_t PayloadSync0 = 0x57U;
constexpr uint8_t PayloadSync1 = 0x50U;
constexpr uint8_t PayloadProtocolVersion = 1U;
constexpr std::size_t PayloadWireSize = 32U;
constexpr std::size_t PayloadDataSize = 16U;
constexpr std::size_t PayloadHeaderSize = 12U;
constexpr std::size_t PayloadCrcOffset = 28U;

enum class PayloadMessageType : uint8_t
{
    PollRequest = 0x01U,
    TelemetryResponse = 0x81U
};

enum class PayloadMode : uint8_t
{
    Normal = 0U,
    Silent = 1U,
    BadCrc = 2U,
    Delayed = 3U
};

enum class PayloadValidationResult : uint8_t
{
    Ok,
    NullBuffer,
    BadSize,
    BadSync,
    BadVersion,
    BadType,
    BadLength,
    BadCrc,
    BadSequence
};

struct PayloadFrame
{
    PayloadMessageType type = PayloadMessageType::PollRequest;
    uint32_t sequence = 0U;
    uint16_t payloadLength = 0U;
    uint16_t flags = 0U;
    uint8_t payload[PayloadDataSize] = {};
};

struct PayloadTelemetry
{
    uint32_t uptimeMs = 0U;
    uint32_t sampleCounter = 0U;
    int32_t simulatedSensorMilliunits = 0;
    PayloadMode mode = PayloadMode::Normal;
};

inline void payloadWriteU16Le(uint8_t* buffer, std::size_t offset, uint16_t value)
{
    buffer[offset] = static_cast<uint8_t>(value & 0xFFU);
    buffer[offset + 1U] = static_cast<uint8_t>((value >> 8U) & 0xFFU);
}

inline void payloadWriteU32Le(uint8_t* buffer, std::size_t offset, uint32_t value)
{
    buffer[offset] = static_cast<uint8_t>(value & 0xFFU);
    buffer[offset + 1U] = static_cast<uint8_t>((value >> 8U) & 0xFFU);
    buffer[offset + 2U] = static_cast<uint8_t>((value >> 16U) & 0xFFU);
    buffer[offset + 3U] = static_cast<uint8_t>((value >> 24U) & 0xFFU);
}

inline uint16_t payloadReadU16Le(const uint8_t* buffer, std::size_t offset)
{
    return static_cast<uint16_t>(buffer[offset]) |
           static_cast<uint16_t>(static_cast<uint16_t>(buffer[offset + 1U]) << 8U);
}

inline uint32_t payloadReadU32Le(const uint8_t* buffer, std::size_t offset)
{
    return static_cast<uint32_t>(buffer[offset]) |
           (static_cast<uint32_t>(buffer[offset + 1U]) << 8U) |
           (static_cast<uint32_t>(buffer[offset + 2U]) << 16U) |
           (static_cast<uint32_t>(buffer[offset + 3U]) << 24U);
}

inline uint32_t payloadCrc32(const uint8_t* data, std::size_t length)
{
    static constexpr uint32_t Crc32NibbleTable[16] = {
        0x00000000UL, 0x1DB71064UL, 0x3B6E20C8UL, 0x26D930ACUL,
        0x76DC4190UL, 0x6B6B51F4UL, 0x4DB26158UL, 0x5005713CUL,
        0xEDB88320UL, 0xF00F9344UL, 0xD6D6A3E8UL, 0xCB61B38CUL,
        0x9B64C2B0UL, 0x86D3D2D4UL, 0xA00AE278UL, 0xBDBDF21CUL
    };

    uint32_t crc = 0xFFFFFFFFUL;
    if (data == nullptr)
    {
        return ~crc;
    }

    for (std::size_t i = 0U; i < length; ++i)
    {
        crc ^= static_cast<uint32_t>(data[i]);
        crc = (crc >> 4U) ^ Crc32NibbleTable[crc & 0x0FUL];
        crc = (crc >> 4U) ^ Crc32NibbleTable[crc & 0x0FUL];
    }
    return ~crc;
}

inline bool encodePayloadFrame(const PayloadFrame& frame,
                               uint8_t* outBuffer,
                               std::size_t capacity)
{
    if (outBuffer == nullptr || capacity < PayloadWireSize ||
        frame.payloadLength > PayloadDataSize)
    {
        return false;
    }

    for (std::size_t i = 0U; i < PayloadWireSize; ++i)
    {
        outBuffer[i] = 0U;
    }
    outBuffer[0U] = PayloadSync0;
    outBuffer[1U] = PayloadSync1;
    outBuffer[2U] = PayloadProtocolVersion;
    outBuffer[3U] = static_cast<uint8_t>(frame.type);
    payloadWriteU32Le(outBuffer, 4U, frame.sequence);
    payloadWriteU16Le(outBuffer, 8U, frame.payloadLength);
    payloadWriteU16Le(outBuffer, 10U, frame.flags);
    for (std::size_t i = 0U; i < frame.payloadLength; ++i)
    {
        outBuffer[PayloadHeaderSize + i] = frame.payload[i];
    }
    payloadWriteU32Le(outBuffer, PayloadCrcOffset,
                      payloadCrc32(outBuffer, PayloadCrcOffset));
    return true;
}

inline bool encodePollRequest(uint32_t sequence,
                              uint8_t* outBuffer,
                              std::size_t capacity)
{
    PayloadFrame frame = {};
    frame.type = PayloadMessageType::PollRequest;
    frame.sequence = sequence;
    return encodePayloadFrame(frame, outBuffer, capacity);
}

inline bool encodeTelemetryResponse(uint32_t sequence,
                                    const PayloadTelemetry& telemetry,
                                    uint8_t* outBuffer,
                                    std::size_t capacity)
{
    PayloadFrame frame = {};
    frame.type = PayloadMessageType::TelemetryResponse;
    frame.sequence = sequence;
    frame.payloadLength = static_cast<uint16_t>(PayloadDataSize);
    payloadWriteU32Le(frame.payload, 0U, telemetry.uptimeMs);
    payloadWriteU32Le(frame.payload, 4U, telemetry.sampleCounter);
    payloadWriteU32Le(frame.payload, 8U,
                      static_cast<uint32_t>(telemetry.simulatedSensorMilliunits));
    frame.payload[12U] = static_cast<uint8_t>(telemetry.mode);
    return encodePayloadFrame(frame, outBuffer, capacity);
}

inline PayloadValidationResult decodePayloadFrame(const uint8_t* buffer,
                                                  std::size_t length,
                                                  PayloadFrame& outFrame)
{
    if (buffer == nullptr)
    {
        return PayloadValidationResult::NullBuffer;
    }
    if (length != PayloadWireSize)
    {
        return PayloadValidationResult::BadSize;
    }
    if (buffer[0U] != PayloadSync0 || buffer[1U] != PayloadSync1)
    {
        return PayloadValidationResult::BadSync;
    }
    if (buffer[2U] != PayloadProtocolVersion)
    {
        return PayloadValidationResult::BadVersion;
    }
    if (buffer[3U] != static_cast<uint8_t>(PayloadMessageType::PollRequest) &&
        buffer[3U] != static_cast<uint8_t>(PayloadMessageType::TelemetryResponse))
    {
        return PayloadValidationResult::BadType;
    }

    const uint16_t payloadLength = payloadReadU16Le(buffer, 8U);
    const PayloadMessageType type = static_cast<PayloadMessageType>(buffer[3U]);
    const uint16_t expectedLength =
        (type == PayloadMessageType::PollRequest) ? 0U : static_cast<uint16_t>(PayloadDataSize);
    if (payloadLength != expectedLength)
    {
        return PayloadValidationResult::BadLength;
    }
    if (payloadReadU32Le(buffer, PayloadCrcOffset) !=
        payloadCrc32(buffer, PayloadCrcOffset))
    {
        return PayloadValidationResult::BadCrc;
    }

    outFrame.type = type;
    outFrame.sequence = payloadReadU32Le(buffer, 4U);
    outFrame.payloadLength = payloadLength;
    outFrame.flags = payloadReadU16Le(buffer, 10U);
    for (std::size_t i = 0U; i < PayloadDataSize; ++i)
    {
        outFrame.payload[i] = buffer[PayloadHeaderSize + i];
    }
    return PayloadValidationResult::Ok;
}

inline bool decodePayloadTelemetry(const PayloadFrame& frame,
                                   PayloadTelemetry& outTelemetry)
{
    if (frame.type != PayloadMessageType::TelemetryResponse ||
        frame.payloadLength != PayloadDataSize)
    {
        return false;
    }
    outTelemetry.uptimeMs = payloadReadU32Le(frame.payload, 0U);
    outTelemetry.sampleCounter = payloadReadU32Le(frame.payload, 4U);
    outTelemetry.simulatedSensorMilliunits =
        static_cast<int32_t>(payloadReadU32Le(frame.payload, 8U));
    outTelemetry.mode = static_cast<PayloadMode>(frame.payload[12U]);
    return true;
}

enum class PayloadDecodeEvent : uint8_t
{
    None,
    FrameReady,
    FrameRejected
};

class PayloadFrameDecoder
{
public:
    PayloadDecodeEvent consume(uint8_t byte)
    {
        if (used == 0U)
        {
            if (byte == PayloadSync0)
            {
                bytes[used++] = byte;
            }
            return PayloadDecodeEvent::None;
        }
        if (used == 1U && byte != PayloadSync1)
        {
            used = 0U;
            if (byte == PayloadSync0)
            {
                bytes[used++] = byte;
            }
            return PayloadDecodeEvent::None;
        }

        bytes[used++] = byte;
        if (used < PayloadWireSize)
        {
            return PayloadDecodeEvent::None;
        }

        PayloadFrame ignored = {};
        lastResult = decodePayloadFrame(bytes, PayloadWireSize, ignored);
        used = 0U;
        return (lastResult == PayloadValidationResult::Ok)
                   ? PayloadDecodeEvent::FrameReady
                   : PayloadDecodeEvent::FrameRejected;
    }

    const uint8_t* frameData() const { return bytes; }
    PayloadValidationResult validationResult() const { return lastResult; }
    void reset() { used = 0U; lastResult = PayloadValidationResult::BadSize; }

private:
    uint8_t bytes[PayloadWireSize] = {};
    std::size_t used = 0U;
    PayloadValidationResult lastResult = PayloadValidationResult::BadSize;
};

} /* namespace comms */
