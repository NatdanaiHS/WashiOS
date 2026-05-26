#pragma once

#include <cstddef>
#include <cstdint>

#include "ISpiBus.hpp"

namespace test_mocks
{

template<std::size_t BufferCapacity = 128, std::size_t MaxChipSelects = 16>
class MockSpiBus final : public hal::ISpiBus
{
public:
    bool transfer(const uint8_t* txData,
                  uint8_t* rxData,
                  std::size_t length,
                  uint32_t timeout_ms) override
    {
        if (forcedFailure || forcedTimeout || (timeout_ms == 0U && length > 0U) ||
            length > BufferCapacity)
        {
            return false;
        }

        lastTransferLength = length;
        for (std::size_t i = 0; i < length; ++i)
        {
            const uint8_t tx = (txData != nullptr) ? txData[i] : 0U;
            lastTx[i] = tx;
            if (rxData != nullptr)
            {
                rxData[i] = (i < responseLength) ? response[i] : tx;
            }
        }

        return true;
    }

    void setFrequency(uint32_t hz) override
    {
        configuredFrequency = hz;
    }

    void selectChip(uint8_t csPinId) override
    {
        if (csPinId < MaxChipSelects)
        {
            selected[csPinId] = true;
        }
    }

    void deselectChip(uint8_t csPinId) override
    {
        if (csPinId < MaxChipSelects)
        {
            selected[csPinId] = false;
        }
    }

    bool setResponse(const uint8_t* data, std::size_t length)
    {
        if ((data == nullptr && length > 0U) || length > BufferCapacity)
        {
            return false;
        }

        responseLength = length;
        for (std::size_t i = 0; i < length; ++i)
        {
            response[i] = data[i];
        }

        return true;
    }

    bool isSelected(uint8_t csPinId) const
    {
        return (csPinId < MaxChipSelects) ? selected[csPinId] : false;
    }

    uint32_t frequency() const
    {
        return configuredFrequency;
    }

    std::size_t getLastTx(uint8_t* buffer, std::size_t capacity) const
    {
        const std::size_t count = (lastTransferLength < capacity) ? lastTransferLength : capacity;
        for (std::size_t i = 0; i < count; ++i)
        {
            buffer[i] = lastTx[i];
        }
        return count;
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
    uint8_t lastTx[BufferCapacity] = {};
    uint8_t response[BufferCapacity] = {};
    bool selected[MaxChipSelects] = {};
    std::size_t lastTransferLength = 0;
    std::size_t responseLength = 0;
    uint32_t configuredFrequency = 0;
    bool forcedTimeout = false;
    bool forcedFailure = false;
};

} /* namespace test_mocks */
