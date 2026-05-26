#pragma once

#include <cstddef>
#include <cstdint>

#include "ICanBus.hpp"

namespace test_mocks
{

template<std::size_t QueueCapacity = 16>
class MockCanBus final : public hal::ICanBus
{
public:
    bool begin(uint32_t baudRate) override
    {
        configuredBaudRate = baudRate;
        state = hal::CanBusState::Ready;
        return baudRate > 0U;
    }

    bool transmit(const hal::CanFrame& frame, uint32_t timeout_ms) override
    {
        if (state != hal::CanBusState::Ready || forcedFailure || forcedTimeout ||
            timeout_ms == 0U || frame.dataLength > 8U || txCount >= QueueCapacity)
        {
            return false;
        }

        push(txQueue, txHead, txCount, frame);
        if (loopbackEnabled && rxCount < QueueCapacity && accepts(frame.messageId))
        {
            push(rxQueue, rxHead, rxCount, frame);
        }

        return true;
    }

    bool receive(hal::CanFrame& frame, uint32_t timeout_ms) override
    {
        if (state != hal::CanBusState::Ready || forcedFailure || forcedTimeout ||
            timeout_ms == 0U || rxCount == 0U)
        {
            return false;
        }

        frame = pop(rxQueue, rxTail, rxCount);
        return true;
    }

    bool setFilter(uint32_t targetMessageId, uint32_t mask) override
    {
        filterId = targetMessageId;
        filterMask = mask;
        filterEnabled = true;
        return true;
    }

    hal::CanBusState getState() const override
    {
        return state;
    }

    void recoverBus() override
    {
        if (state == hal::CanBusState::BusOff || state == hal::CanBusState::Error)
        {
            state = hal::CanBusState::Ready;
        }
        forcedFailure = false;
        forcedTimeout = false;
    }

    bool injectRx(const hal::CanFrame& frame)
    {
        if (frame.dataLength > 8U || rxCount >= QueueCapacity || !accepts(frame.messageId))
        {
            return false;
        }

        push(rxQueue, rxHead, rxCount, frame);
        return true;
    }

    bool readTx(hal::CanFrame& frame)
    {
        if (txCount == 0U)
        {
            return false;
        }

        frame = pop(txQueue, txTail, txCount);
        return true;
    }

    void setLoopback(bool enabled)
    {
        loopbackEnabled = enabled;
    }

    void setState(hal::CanBusState newState)
    {
        state = newState;
    }

    void setForcedTimeout(bool enabled)
    {
        forcedTimeout = enabled;
    }

    void setForcedFailure(bool enabled)
    {
        forcedFailure = enabled;
    }

    uint32_t baudRate() const
    {
        return configuredBaudRate;
    }

private:
    hal::CanFrame txQueue[QueueCapacity] = {};
    hal::CanFrame rxQueue[QueueCapacity] = {};
    std::size_t txHead = 0;
    std::size_t txTail = 0;
    std::size_t txCount = 0;
    std::size_t rxHead = 0;
    std::size_t rxTail = 0;
    std::size_t rxCount = 0;
    uint32_t configuredBaudRate = 0;
    uint32_t filterId = 0;
    uint32_t filterMask = 0;
    bool filterEnabled = false;
    bool loopbackEnabled = false;
    bool forcedTimeout = false;
    bool forcedFailure = false;
    hal::CanBusState state = hal::CanBusState::Uninitialized;

    static std::size_t advance(std::size_t value)
    {
        ++value;
        return (value >= QueueCapacity) ? 0U : value;
    }

    static void push(hal::CanFrame* queue,
                     std::size_t& head,
                     std::size_t& count,
                     const hal::CanFrame& frame)
    {
        queue[head] = frame;
        head = advance(head);
        ++count;
    }

    static hal::CanFrame pop(hal::CanFrame* queue, std::size_t& tail, std::size_t& count)
    {
        const hal::CanFrame frame = queue[tail];
        tail = advance(tail);
        --count;
        return frame;
    }

    bool accepts(uint32_t messageId) const
    {
        if (!filterEnabled)
        {
            return true;
        }

        return (messageId & filterMask) == (filterId & filterMask);
    }
};

} /* namespace test_mocks */
