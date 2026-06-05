#pragma once

#include <cstdint>

#include "FaultLog.hpp"

namespace core
{

using BootRecoveryCallback = void (*)(void* context);

template<std::size_t LogCapacity>
inline bool handleBootTaskStartFailure(bool tasksStarted,
                                       FaultLog<LogCapacity>& faultLog,
                                       uint64_t timestampMs,
                                       BootRecoveryCallback recoveryCallback,
                                       void* recoveryContext)
{
    if (tasksStarted)
    {
        return true;
    }

    (void)faultLog.record(FaultEventType::SafeFail,
                          timestampMs,
                          0U,
                          0U,
                          0U);

    if (recoveryCallback != nullptr)
    {
        recoveryCallback(recoveryContext);
    }

    return false;
}

} /* namespace core */
