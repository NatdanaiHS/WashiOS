#pragma once

#include <cstddef>
#include <cstdint>

namespace bsp
{

template<std::size_t Capacity>
class F411RxRing final
{
    static_assert(Capacity >= 2U, "RX ring needs at least two slots");

public:
    bool pushFromInterrupt(uint8_t byte) noexcept
    {
        const std::size_t next = increment(head);
        if (next == tail)
        {
            ++overflowCounter;
            return false;
        }
        bytes[head] = byte;
        head = next;
        return true;
    }

    bool pop(uint8_t& byte) noexcept
    {
        if (tail == head)
        {
            return false;
        }
        byte = bytes[tail];
        tail = increment(tail);
        return true;
    }

    std::size_t available() const noexcept
    {
        const std::size_t currentHead = head;
        const std::size_t currentTail = tail;
        return (currentHead >= currentTail) ?
            (currentHead - currentTail) :
            (Capacity - currentTail + currentHead);
    }

    void noteHardwareError() noexcept
    {
        ++hardwareErrorCounter;
    }

    uint32_t overflowCount() const noexcept
    {
        return overflowCounter;
    }

    uint32_t hardwareErrorCount() const noexcept
    {
        return hardwareErrorCounter;
    }

    void clear() noexcept
    {
        head = 0U;
        tail = 0U;
    }

private:
    static constexpr std::size_t increment(std::size_t value) noexcept
    {
        return (value + 1U) % Capacity;
    }

    uint8_t bytes[Capacity] = {};
    volatile std::size_t head = 0U;
    volatile std::size_t tail = 0U;
    volatile uint32_t overflowCounter = 0U;
    volatile uint32_t hardwareErrorCounter = 0U;
};

} /* namespace bsp */
