#pragma once

#include <cstddef>
#include <cstdint>

#include "IUart.hpp"

namespace test_mocks
{

template<std::size_t RxCapacity = 128, std::size_t TxCapacity = 128>
class MockUart final : public hal::IUart
{
public:
    bool writeBuffer(const uint8_t* data,
                     std::size_t length,
                     uint32_t timeout_ms) noexcept override
    {
        if ((data == nullptr && length > 0U) || forcedFailure || forcedTimeout ||
            (timeout_ms == 0U && length > 0U) || length > txRemaining())
        {
            return false;
        }

        for (std::size_t i = 0; i < length; ++i)
        {
            txBuffer[txHead] = data[i];
            txHead = advance(txHead, TxCapacity);
            ++txCount;
        }

        return true;
    }

    bool readBuffer(uint8_t* buffer,
                    std::size_t length,
                    uint32_t timeout_ms) noexcept override
    {
        if ((buffer == nullptr && length > 0U) || forcedFailure || forcedTimeout ||
            (timeout_ms == 0U && length > 0U) || length > rxCount)
        {
            return false;
        }

        for (std::size_t i = 0; i < length; ++i)
        {
            buffer[i] = rxBuffer[rxTail];
            rxTail = advance(rxTail, RxCapacity);
            --rxCount;
        }

        return true;
    }

    std::size_t available() const noexcept override
    {
        return rxCount;
    }

    void flush() noexcept override
    {
        rxHead = 0;
        rxTail = 0;
        rxCount = 0;
        txHead = 0;
        txTail = 0;
        txCount = 0;
    }

    void setBaudRate(uint32_t baudRate) noexcept override
    {
        configuredBaudRate = baudRate;
    }

    bool injectRx(const uint8_t* data, std::size_t length)
    {
        if ((data == nullptr && length > 0U) || length > rxRemaining())
        {
            return false;
        }

        for (std::size_t i = 0; i < length; ++i)
        {
            rxBuffer[rxHead] = data[i];
            rxHead = advance(rxHead, RxCapacity);
            ++rxCount;
        }

        return true;
    }

    bool readTx(uint8_t* buffer, std::size_t length)
    {
        if ((buffer == nullptr && length > 0U) || length > txCount)
        {
            return false;
        }

        for (std::size_t i = 0; i < length; ++i)
        {
            buffer[i] = txBuffer[txTail];
            txTail = advance(txTail, TxCapacity);
            --txCount;
        }

        return true;
    }

    std::size_t txAvailable() const
    {
        return txCount;
    }

    uint32_t baudRate() const
    {
        return configuredBaudRate;
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
    uint8_t rxBuffer[RxCapacity] = {};
    uint8_t txBuffer[TxCapacity] = {};
    std::size_t rxHead = 0;
    std::size_t rxTail = 0;
    std::size_t rxCount = 0;
    std::size_t txHead = 0;
    std::size_t txTail = 0;
    std::size_t txCount = 0;
    uint32_t configuredBaudRate = 0;
    bool forcedTimeout = false;
    bool forcedFailure = false;

    static std::size_t advance(std::size_t value, std::size_t capacity)
    {
        ++value;
        return (value >= capacity) ? 0U : value;
    }

    std::size_t rxRemaining() const
    {
        return RxCapacity - rxCount;
    }

    std::size_t txRemaining() const
    {
        return TxCapacity - txCount;
    }
};

} /* namespace test_mocks */
