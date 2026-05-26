#pragma once

#include <cstddef>
#include <cstdint>

#include "FreeRTOS.h"
#include "task.h"
#include "WatchdogRunner.hpp"
#include "WashiTask.hpp"

template<std::size_t RegistryCapacity = 8, std::size_t LogCapacity = 32>
class WatchdogTask final : public rtos_config::WashiTask<256>
{
public:
    WatchdogTask(core::WatchdogRunner<RegistryCapacity, LogCapacity>& runner,
                 uint32_t pollDelayMs)
        : watchdogRunner(runner),
          delayMs(pollDelayMs)
    {
    }

protected:
    void Run() override
    {
        for (;;)
        {
            (void)watchdogRunner.runOnce();
            vTaskDelay(pdMS_TO_TICKS(delayMs));
        }
    }

private:
    core::WatchdogRunner<RegistryCapacity, LogCapacity>& watchdogRunner;
    uint32_t delayMs;
};
