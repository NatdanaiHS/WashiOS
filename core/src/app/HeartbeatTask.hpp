#pragma once

#include <cstdint>

#include "FreeRTOS.h"
#include "task.h"
#include "IGPIO.hpp"
#include "ITiming.hpp"
#include "TaskHealthReporter.hpp"
#include "WashiTask.hpp"

class HeartbeatTask final : public rtos_config::WashiTask<256>
{
public:
    void ConfigureHealth(core::TaskHealthRegistry<>* registry,
                         hal::ITiming* timing,
                         core::TaskId taskId)
    {
        healthReporter.configure(registry, timing, taskId);
    }

    uint32_t heartbeatCount() const { return heartbeatCounter; }

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
            ++heartbeatCounter;
            toggleLed();
            checkIn();
            vTaskDelay(pdMS_TO_TICKS(1000));
        }
    }

private:
    core::TaskHealthReporter<> healthReporter;
    hal::IGPIO* led = nullptr;
    uint32_t heartbeatCounter = 0U;
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
        (void)healthReporter.checkIn();
    }

    void toggleLed()
    {
        if (led != nullptr)
        {
            led->toggle();
        }
    }
};
