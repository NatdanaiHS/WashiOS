#pragma once

#include <cstddef>
#include <cstdint>

#include "CriticalSection.hpp"

namespace core
{

constexpr uint32_t WASHIOS_MAGIC_SIGNATURE = 0x55AA55AAUL;

enum class FaultEventType
{
    TmrCorrection,
    TmrUnrecoverable,
    WatchdogTimeout,
    TaskCheckinFailure,
    StackOverflow,
    AssertFailure,
    SafeFail
};

struct FaultEvent
{
    FaultEventType type;
    uint64_t timestampMs;
    uint8_t taskId;
    uint32_t detailCode;
    uint32_t correctionCount;
};

template<std::size_t Capacity = 32>
class FaultLog
{
public:
    bool record(FaultEventType type,
                uint64_t timestampMs,
                uint8_t taskId,
                uint32_t detailCode,
                uint32_t correctionCount)
    {
        if (Capacity == 0U)
        {
            return false;
        }

        taskENTER_CRITICAL();
        if (signature != WASHIOS_MAGIC_SIGNATURE)
        {
            initializeEmptyRetainedState();
        }

        entries[writeIndex] = {type, timestampMs, taskId, detailCode, correctionCount};
        writeIndex = advance(writeIndex);
        ++totalCount;
        if (storedCount < Capacity)
        {
            ++storedCount;
        }
        commitChecksum();
        taskEXIT_CRITICAL();
        return true;
    }

    void clear()
    {
        taskENTER_CRITICAL();
        initializeEmptyRetainedState();
        taskEXIT_CRITICAL();
    }

    bool recoverRetainedState()
    {
        if (!hasValidRetainedState())
        {
            taskENTER_CRITICAL();
            initializeEmptyRetainedState();
            taskEXIT_CRITICAL();
            return false;
        }

        return storedCount > 0U;
    }

    std::size_t size() const
    {
        return storedCount;
    }

    uint32_t totalEvents() const
    {
        return totalCount;
    }

    bool read(std::size_t index, FaultEvent& outEvent) const
    {
        taskENTER_CRITICAL();
        if (index >= storedCount || Capacity == 0U)
        {
            taskEXIT_CRITICAL();
            return false;
        }

        outEvent = entries[physicalIndex(index)];
        taskEXIT_CRITICAL();
        return true;
    }

    bool latest(FaultEvent& outEvent) const
    {
        taskENTER_CRITICAL();
        if (storedCount == 0U || Capacity == 0U)
        {
            taskEXIT_CRITICAL();
            return false;
        }

        const std::size_t latestIndex = (writeIndex == 0U) ? (Capacity - 1U) : (writeIndex - 1U);
        outEvent = entries[latestIndex];
        taskEXIT_CRITICAL();
        return true;
    }

private:
    uint32_t signature = WASHIOS_MAGIC_SIGNATURE;
    uint32_t checksum = 0U;
    FaultEvent entries[Capacity == 0U ? 1U : Capacity] = {};
    std::size_t writeIndex = 0;
    std::size_t storedCount = 0;
    uint32_t totalCount = 0;

    void initializeEmptyRetainedState()
    {
        for (std::size_t i = 0U; i < (Capacity == 0U ? 1U : Capacity); ++i)
        {
            entries[i] = {};
        }

        writeIndex = 0U;
        storedCount = 0U;
        totalCount = 0U;
        signature = WASHIOS_MAGIC_SIGNATURE;
        commitChecksum();
    }

    static uint32_t crc32UpdateByte(uint32_t crc, uint8_t value)
    {
        static constexpr uint32_t Crc32NibbleTable[16] = {
            0x00000000UL, 0x1DB71064UL, 0x3B6E20C8UL, 0x26D930ACUL,
            0x76DC4190UL, 0x6B6B51F4UL, 0x4DB26158UL, 0x5005713CUL,
            0xEDB88320UL, 0xF00F9344UL, 0xD6D6A3E8UL, 0xCB61B38CUL,
            0x9B64C2B0UL, 0x86D3D2D4UL, 0xA00AE278UL, 0xBDBDF21CUL
        };

        crc ^= static_cast<uint32_t>(value);
        crc = (crc >> 4U) ^ Crc32NibbleTable[crc & 0x0FUL];
        crc = (crc >> 4U) ^ Crc32NibbleTable[crc & 0x0FUL];
        return crc;
    }

    static uint32_t crc32UpdateU8(uint32_t crc, uint8_t value)
    {
        return crc32UpdateByte(crc, value);
    }

    static uint32_t crc32UpdateU32(uint32_t crc, uint32_t value)
    {
        for (std::size_t i = 0U; i < sizeof(value); ++i)
        {
            crc = crc32UpdateByte(crc,
                                  static_cast<uint8_t>((value >> (i * 8U)) & 0xFFU));
        }
        return crc;
    }

    static uint32_t crc32UpdateU64(uint32_t crc, uint64_t value)
    {
        for (std::size_t i = 0U; i < sizeof(value); ++i)
        {
            crc = crc32UpdateByte(crc,
                                  static_cast<uint8_t>((value >> (i * 8U)) & 0xFFU));
        }
        return crc;
    }

    static uint32_t crc32UpdateSize(uint32_t crc, std::size_t value)
    {
        for (std::size_t i = 0U; i < sizeof(value); ++i)
        {
            crc = crc32UpdateByte(
                crc,
                static_cast<uint8_t>((value >> (i * 8U)) & static_cast<std::size_t>(0xFFU)));
        }
        return crc;
    }

    uint32_t calculateChecksum() const
    {
        uint32_t crc = 0xFFFFFFFFUL;
        crc = crc32UpdateU32(crc, signature);

        for (std::size_t i = 0U; i < (Capacity == 0U ? 1U : Capacity); ++i)
        {
            crc = crc32UpdateU32(crc, static_cast<uint32_t>(entries[i].type));
            crc = crc32UpdateU64(crc, entries[i].timestampMs);
            crc = crc32UpdateU8(crc, entries[i].taskId);
            crc = crc32UpdateU32(crc, entries[i].detailCode);
            crc = crc32UpdateU32(crc, entries[i].correctionCount);
        }

        crc = crc32UpdateSize(crc, writeIndex);
        crc = crc32UpdateSize(crc, storedCount);
        crc = crc32UpdateU32(crc, totalCount);
        return ~crc;
    }

    void commitChecksum()
    {
        checksum = calculateChecksum();
    }

    static bool isValidEventType(FaultEventType type)
    {
        return type == FaultEventType::TmrCorrection ||
               type == FaultEventType::TmrUnrecoverable ||
               type == FaultEventType::WatchdogTimeout ||
               type == FaultEventType::TaskCheckinFailure ||
               type == FaultEventType::StackOverflow ||
               type == FaultEventType::AssertFailure ||
               type == FaultEventType::SafeFail;
    }

    bool hasValidRetainedState() const
    {
        if (signature != WASHIOS_MAGIC_SIGNATURE)
        {
            return false;
        }

        if (checksum != calculateChecksum())
        {
            return false;
        }

        if (Capacity == 0U)
        {
            return writeIndex == 0U && storedCount == 0U && totalCount == 0U;
        }

        if (writeIndex >= Capacity || storedCount > Capacity ||
            totalCount < storedCount)
        {
            return false;
        }

        for (std::size_t i = 0U; i < storedCount; ++i)
        {
            if (!isValidEventType(entries[physicalIndex(i)].type))
            {
                return false;
            }
        }

        return true;
    }

    static std::size_t advance(std::size_t index)
    {
        ++index;
        return (index >= Capacity) ? 0U : index;
    }

    std::size_t physicalIndex(std::size_t logicalIndex) const
    {
        if (storedCount < Capacity)
        {
            return logicalIndex;
        }

        std::size_t index = writeIndex + logicalIndex;
        if (index >= Capacity)
        {
            index -= Capacity;
        }
        return index;
    }

#if defined(WASHIOS_ENABLE_TEST_HOOKS)
public:
    void corruptRetainedStateForTest()
    {
        ++totalCount;
    }
#endif
};

} /* namespace core */
