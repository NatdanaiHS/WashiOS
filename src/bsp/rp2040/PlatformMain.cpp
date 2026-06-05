#include "bsp/CrossPlatformConfig.hpp"
#include "bsp/rp2040/GpioDriver.hpp"
#include "bsp/rp2040/UartDriver.hpp"

#include <Arduino.h>
#include <cstddef>
#include <cstdint>

namespace
{

constexpr std::size_t TelemetryFrameWireSize = 28U;
constexpr uint32_t TelemetryPeriodMs = 500U;

WASHIOS_RETAINED uint32_t retainedBootMarker;
bsp::rp2040::GpioDriver statusLed(25U);
bsp::rp2040::UartDriver consoleUart;
uint32_t telemetrySequence = 0U;
uint32_t lastTelemetryMs = 0U;

void writeU16Le(uint8_t* buffer, std::size_t offset, uint16_t value)
{
    buffer[offset] = static_cast<uint8_t>(value & 0xFFU);
    buffer[offset + 1U] = static_cast<uint8_t>((value >> 8U) & 0xFFU);
}

void writeU32Le(uint8_t* buffer, std::size_t offset, uint32_t value)
{
    buffer[offset] = static_cast<uint8_t>(value & 0xFFU);
    buffer[offset + 1U] = static_cast<uint8_t>((value >> 8U) & 0xFFU);
    buffer[offset + 2U] = static_cast<uint8_t>((value >> 16U) & 0xFFU);
    buffer[offset + 3U] = static_cast<uint8_t>((value >> 24U) & 0xFFU);
}

uint32_t crc32(const uint8_t* data, std::size_t length)
{
    static constexpr uint32_t Crc32NibbleTable[16] = {
        0x00000000UL, 0x1DB71064UL, 0x3B6E20C8UL, 0x26D930ACUL,
        0x76DC4190UL, 0x6B6B51F4UL, 0x4DB26158UL, 0x5005713CUL,
        0xEDB88320UL, 0xF00F9344UL, 0xD6D6A3E8UL, 0xCB61B38CUL,
        0x9B64C2B0UL, 0x86D3D2D4UL, 0xA00AE278UL, 0xBDBDF21CUL
    };

    uint32_t crc = 0xFFFFFFFFUL;
    for (std::size_t i = 0U; i < length; ++i)
    {
        crc ^= static_cast<uint32_t>(data[i]);
        crc = (crc >> 4U) ^ Crc32NibbleTable[crc & 0x0FUL];
        crc = (crc >> 4U) ^ Crc32NibbleTable[crc & 0x0FUL];
    }

    return ~crc;
}

void buildTelemetryFrame(uint8_t* frame, uint32_t uptimeMs)
{
    frame[0] = 0x4BU;
    frame[1] = 0x34U;
    frame[2] = 1U;
    frame[3] = static_cast<uint8_t>(TelemetryFrameWireSize);
    writeU32Le(frame, 4U, telemetrySequence);
    writeU32Le(frame, 8U, uptimeMs);
    writeU32Le(frame, 12U, 0x00000002UL);
    writeU32Le(frame, 16U, retainedBootMarker);
    frame[20] = 0xFFU;
    frame[21] = 0xFFU;
    writeU16Le(frame, 22U, 0U);
    writeU32Le(frame, 24U, crc32(frame, TelemetryFrameWireSize - sizeof(uint32_t)));
}

void emitTelemetry(uint32_t nowMs)
{
    uint8_t frame[TelemetryFrameWireSize] = {};
    buildTelemetryFrame(frame, nowMs);
    if (consoleUart.writeBuffer(frame, sizeof(frame), 10U))
    {
        ++telemetrySequence;
    }
}

} /* namespace */

extern "C" void setup()
{
    ++retainedBootMarker;
    statusLed.setLow();
    consoleUart.setBaudRate(115200U);
}

extern "C" void loop()
{
    const uint32_t nowMs = millis();
    if ((nowMs - lastTelemetryMs) >= TelemetryPeriodMs)
    {
        lastTelemetryMs = nowMs;
        statusLed.toggle();
        emitTelemetry(nowMs);
    }
}
