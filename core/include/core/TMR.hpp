#pragma once

#include <cstddef>
#include <cstdint>

#include "CriticalSection.hpp"
#include "FaultLog.hpp"
#include "SystemReset.hpp"

namespace core
{

template<typename T>
class TMR
{
public:
    TMR() = default;

    explicit TMR(const T& value)
    {
        set(value);
    }

    void set(const T& value)
    {
        copies[0] = value;
        copies[1] = value;
        copies[2] = value;
    }

    template<std::size_t Capacity>
    T get(FaultLog<Capacity>& faultLog,
          uint64_t timestampMs,
          uint8_t taskId = 0U,
          uint32_t detailCode = 0U)
    {
        if (copies[0] == copies[1])
        {
            repairIfNeeded(2U, copies[0], faultLog, timestampMs, taskId, detailCode);
            return copies[0];
        }

        if (copies[0] == copies[2])
        {
            repairIfNeeded(1U, copies[0], faultLog, timestampMs, taskId, detailCode);
            return copies[0];
        }

        if (copies[1] == copies[2])
        {
            repairIfNeeded(0U, copies[1], faultLog, timestampMs, taskId, detailCode);
            return copies[1];
        }

        (void)faultLog.record(FaultEventType::TmrUnrecoverable,
                              timestampMs,
                              taskId,
                              detailCode,
                              correctionCount);
        triggerUnrecoverableReset();
        return T{};
    }

    uint32_t corrections() const
    {
        return correctionCount;
    }

#ifdef WASHIOS_ENABLE_TEST_HOOKS
    static bool didTriggerUnrecoverablePanic()
    {
        return unrecoverablePanicTriggered;
    }

    static void clearUnrecoverablePanic()
    {
        unrecoverablePanicTriggered = false;
    }

    bool corruptCopy(std::size_t index, const T& value)
    {
        if (index >= 3U)
        {
            return false;
        }

        copies[index] = value;
        return true;
    }

    bool readCopy(std::size_t index, T& outValue) const
    {
        if (index >= 3U)
        {
            return false;
        }

        outValue = copies[index];
        return true;
    }
#endif

private:
    T copies[3] = {};
    uint32_t correctionCount = 0;

#ifdef WASHIOS_ENABLE_TEST_HOOKS
    inline static bool unrecoverablePanicTriggered = false;
#endif

    template<std::size_t Capacity>
    void repairIfNeeded(std::size_t index,
                        const T& votedValue,
                        FaultLog<Capacity>& faultLog,
                        uint64_t timestampMs,
                        uint8_t taskId,
                        uint32_t detailCode)
    {
        if (copies[index] == votedValue)
        {
            return;
        }

        copies[index] = votedValue;
        ++correctionCount;
        (void)faultLog.record(FaultEventType::TmrCorrection,
                              timestampMs,
                              taskId,
                              detailCode,
                              correctionCount);
    }

    static void triggerUnrecoverableReset()
    {
#if defined(WASHIOS_ENABLE_TEST_HOOKS) || defined(NATIVE)
#ifdef WASHIOS_ENABLE_TEST_HOOKS
        unrecoverablePanicTriggered = true;
#endif
#else
        core::requestSystemReset();
#endif
    }
};

} /* namespace core */
