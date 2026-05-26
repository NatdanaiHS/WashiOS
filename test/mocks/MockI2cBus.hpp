#pragma once

#include <cstddef>
#include <cstdint>

#include "II2cBus.hpp"

namespace test_mocks
{

template<std::size_t BufferCapacity = 128>
class MockI2cBus final : public hal::II2cBus
{
public:
    bool write(uint16_t address,
               const uint8_t* data,
               std::size_t length,
               uint32_t timeout_ms) override
    {
        if ((data == nullptr && length > 0U) || forcedFailure || forcedTimeout ||
            (timeout_ms == 0U && length > 0U) || length > BufferCapacity)
        {
            return false;
        }

        lastAddress = address;
        lastWriteLength = length;
        for (std::size_t i = 0; i < length; ++i)
        {
            lastWrite[i] = data[i];
        }

        return true;
    }

    bool read(uint16_t address,
              uint8_t* buffer,
              std::size_t length,
              uint32_t timeout_ms) override
    {
        if ((buffer == nullptr && length > 0U) || forcedFailure || forcedTimeout ||
            (timeout_ms == 0U && length > 0U) || length > readDataLength)
        {
            return false;
        }

        lastAddress = address;
        for (std::size_t i = 0; i < length; ++i)
        {
            buffer[i] = readData[i];
        }

        return true;
    }

    void resetBus() override
    {
        forcedFailure = false;
        forcedTimeout = false;
        ++resetCount;
    }

    bool setReadData(const uint8_t* data, std::size_t length)
    {
        if ((data == nullptr && length > 0U) || length > BufferCapacity)
        {
            return false;
        }

        readDataLength = length;
        for (std::size_t i = 0; i < length; ++i)
        {
            readData[i] = data[i];
        }

        return true;
    }

    std::size_t getLastWrite(uint8_t* buffer, std::size_t capacity) const
    {
        const std::size_t count = (lastWriteLength < capacity) ? lastWriteLength : capacity;
        for (std::size_t i = 0; i < count; ++i)
        {
            buffer[i] = lastWrite[i];
        }
        return count;
    }

    uint16_t getLastAddress() const
    {
        return lastAddress;
    }

    uint32_t getResetCount() const
    {
        return resetCount;
    }

    void setForcedTimeout(bool enabled)
    {
        forcedTimeout = enabled;
    }

    void setForcedFailure(bool enabled)
    {
        forcedFailure = enabled;
    }

private:
    uint8_t lastWrite[BufferCapacity] = {};
    uint8_t readData[BufferCapacity] = {};
    std::size_t lastWriteLength = 0;
    std::size_t readDataLength = 0;
    uint16_t lastAddress = 0;
    uint32_t resetCount = 0;
    bool forcedTimeout = false;
    bool forcedFailure = false;
};

} /* namespace test_mocks */
