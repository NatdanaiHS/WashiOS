#pragma once

#include <cstddef>
#include <cstdint>

namespace comms
{

constexpr uint8_t FsoSync0 = 0xAAU;
constexpr uint8_t FsoSync1 = 0x55U;
constexpr uint8_t FsoFrameData = 0x03U;
constexpr std::size_t FsoMaxPayloadSize = 64U;
constexpr std::size_t FsoHeaderSize = 5U;
constexpr std::size_t FsoCrcSize = 1U;
constexpr std::size_t FsoMaxWireSize = FsoHeaderSize + FsoMaxPayloadSize + FsoCrcSize;

struct FsoFrame
{
    uint8_t type;
    uint8_t sequence;
    uint8_t length;
    uint8_t payload[FsoMaxPayloadSize];
    uint8_t crc;
};

inline uint8_t fsoCrc8(const uint8_t* data, std::size_t length)
{
    uint8_t crc = 0x00U;

    if (data == nullptr && length > 0U)
    {
        return crc;
    }

    for (std::size_t i = 0U; i < length; ++i)
    {
        crc ^= data[i];
        for (uint8_t bit = 0U; bit < 8U; ++bit)
        {
            crc = (crc & 0x80U) != 0U
                      ? static_cast<uint8_t>((crc << 1U) ^ 0x07U)
                      : static_cast<uint8_t>(crc << 1U);
        }
    }

    return crc;
}

inline uint8_t computeFsoFrameCrc(const FsoFrame& frame)
{
    uint8_t buffer[3U + FsoMaxPayloadSize] = {};
    buffer[0] = frame.type;
    buffer[1] = frame.sequence;
    buffer[2] = frame.length;

    for (std::size_t i = 0U; i < frame.length; ++i)
    {
        buffer[3U + i] = frame.payload[i];
    }

    return fsoCrc8(buffer, 3U + frame.length);
}

inline bool buildFsoDataFrame(uint8_t sequence,
                              const uint8_t* payload,
                              std::size_t payloadLength,
                              FsoFrame& outFrame)
{
    if (payload == nullptr || payloadLength > FsoMaxPayloadSize)
    {
        return false;
    }

    outFrame = {};
    outFrame.type = FsoFrameData;
    outFrame.sequence = sequence;
    outFrame.length = static_cast<uint8_t>(payloadLength);

    for (std::size_t i = 0U; i < payloadLength; ++i)
    {
        outFrame.payload[i] = payload[i];
    }

    outFrame.crc = computeFsoFrameCrc(outFrame);
    return true;
}

inline bool serializeFsoFrame(const FsoFrame& frame,
                              uint8_t* outBuffer,
                              std::size_t outCapacity,
                              std::size_t& outLength)
{
    const std::size_t totalLength =
        FsoHeaderSize + static_cast<std::size_t>(frame.length) + FsoCrcSize;

    if (outBuffer == nullptr || frame.length > FsoMaxPayloadSize ||
        outCapacity < totalLength)
    {
        outLength = 0U;
        return false;
    }

    outBuffer[0] = FsoSync0;
    outBuffer[1] = FsoSync1;
    outBuffer[2] = frame.type;
    outBuffer[3] = frame.sequence;
    outBuffer[4] = frame.length;

    for (std::size_t i = 0U; i < frame.length; ++i)
    {
        outBuffer[5U + i] = frame.payload[i];
    }

    outBuffer[5U + frame.length] = frame.crc;
    outLength = totalLength;
    return true;
}

} /* namespace comms */
