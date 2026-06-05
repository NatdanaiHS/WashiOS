#pragma once

#include <cstdint>

#include "FreeRTOS.h"
#include "task.h"
#include "IGPIO.hpp"
#include "ITiming.hpp"
#include "TaskHealth.hpp"
#include "WashiTask.hpp"

class HeartbeatTask final : public rtos_config::WashiTask<256>
{
public:
    volatile uint32_t heartbeat_count = 0;

    void ConfigureHealth(core::TaskHealthRegistry<>* registry,
                         hal::ITiming* timing,
                         core::TaskId taskId)
    {
        healthRegistry = registry;
        timingSource = timing;
        healthTaskId = taskId;
    }

    void ConfigureLed(hal::IGPIO* indicatorLed)
    {
        led = indicatorLed;
    }

#if defined(WASHIOS_STRESS_TEST)
    void SetHealthReportingEnabled(bool enabled)
    {
        healthReportingEnabled = enabled;
    }
#endif

protected:
    void Run() override
    {
        for (;;)
        {
            ++heartbeat_count;
            toggleLed();
            checkIn();
            vTaskDelay(pdMS_TO_TICKS(1000));
        }
    }

private:
    core::TaskHealthRegistry<>* healthRegistry = nullptr;
    hal::ITiming* timingSource = nullptr;
    hal::IGPIO* led = nullptr;
    core::TaskId healthTaskId = 0U;
#if defined(WASHIOS_STRESS_TEST)
    volatile bool healthReportingEnabled = true;
#endif

    void checkIn()
    {
#if defined(WASHIOS_STRESS_TEST)
        if (!healthReportingEnabled)
        {
            return;
        }
#endif
        if (healthRegistry != nullptr && timingSource != nullptr)
        {
            (void)healthRegistry->checkIn(healthTaskId, timingSource->getSystemTick());
        }
    }

    void toggleLed()
    {
        if (led != nullptr)
        {
            led->toggle();
        }
    }
};
