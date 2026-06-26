#pragma once

#if defined(WASHIOS_STRESS_TEST)

#include <cstdint>

#include "FreeRTOS.h"
#include "task.h"
#include "ITiming.hpp"
#include "WashiTask.hpp"
#include "app/HeartbeatTask.hpp"

#ifndef WASHIOS_STRESS_PRIORITY
#define WASHIOS_STRESS_PRIORITY (tskIDLE_PRIORITY + 1U)
#endif

#ifndef WASHIOS_STRESS_BOOT_ARM_MS
#define WASHIOS_STRESS_BOOT_ARM_MS 5000U
#endif

#ifndef WASHIOS_STRESS_CPU_BURST_ITERATIONS
#define WASHIOS_STRESS_CPU_BURST_ITERATIONS 320U
#endif

#ifndef WASHIOS_STRESS_ACTIVE_MS
#define WASHIOS_STRESS_ACTIVE_MS 95U
#endif

#ifndef WASHIOS_STRESS_PERIOD_MS
#define WASHIOS_STRESS_PERIOD_MS 100U
#endif

#ifndef WASHIOS_STRESS_INJECT_HEARTBEAT_STALL
#define WASHIOS_STRESS_INJECT_HEARTBEAT_STALL 1
#endif

#if WASHIOS_STRESS_ACTIVE_MS > WASHIOS_STRESS_PERIOD_MS
#error "WASHIOS_STRESS_ACTIVE_MS must be <= WASHIOS_STRESS_PERIOD_MS"
#endif

class StressTestTask final : public rtos_config::WashiTask<384>
{
public:
    enum Command : uint32_t
    {
        CommandNone = 0U,
        CommandEnableCpuStress = 1UL << 0U,
        CommandInjectHeartbeatStall = 1UL << 1U
    };

    void Configure(hal::ITiming* timing,
                   HeartbeatTask* heartbeat)
    {
        timingSource = timing;
        heartbeatTask = heartbeat;
    }

    void SubmitCommand(uint32_t command)
    {
        pendingCommands |= command;
    }

    uint32_t GetCompletedBursts() const
    {
        return completedBursts;
    }

protected:
    void Run() override
    {
        for (;;)
        {
            armDeterministicTrigger();
            processCommands();

            if (cpuStressEnabled)
            {
                burnCpuBudget();
            }
            else
            {
                vTaskDelay(pdMS_TO_TICKS(WASHIOS_STRESS_PERIOD_MS));
            }
        }
    }

private:
    hal::ITiming* timingSource = nullptr;
    HeartbeatTask* heartbeatTask = nullptr;
    volatile uint32_t pendingCommands = CommandNone;
    volatile uint32_t completedBursts = 0U;
    bool bootTriggerArmed = true;
    bool cpuStressEnabled = false;
    uint32_t matrixState[16] = {
        0x13579BDFUL, 0x2468ACE0UL, 0x10203040UL, 0x55667788UL,
        0x89ABCDEFUL, 0x0F1E2D3CUL, 0xA5A5A5A5UL, 0x5A5A5A5AUL,
        0xC001D00DUL, 0x12345678UL, 0xDEADBEEFUL, 0x01010101UL,
        0x31415926UL, 0x27182818UL, 0xFEEDFACEUL, 0xCAFEBABEUL
    };

    void armDeterministicTrigger()
    {
        if (!bootTriggerArmed || timingSource == nullptr)
        {
            return;
        }

        if (timingSource->getSystemTick() >= WASHIOS_STRESS_BOOT_ARM_MS)
        {
            bootTriggerArmed = false;
            SubmitCommand(CommandEnableCpuStress);
#if WASHIOS_STRESS_INJECT_HEARTBEAT_STALL
            SubmitCommand(CommandInjectHeartbeatStall);
#endif
        }
    }

    void processCommands()
    {
        const uint32_t commands = pendingCommands;
        pendingCommands = CommandNone;

        if ((commands & CommandEnableCpuStress) != 0U)
        {
            cpuStressEnabled = true;
        }

        if ((commands & CommandInjectHeartbeatStall) != 0U &&
            heartbeatTask != nullptr)
        {
            heartbeatTask->SetHealthReportingEnabled(false);
        }
    }

    void burnCpuBudget()
    {
        const uint64_t startMs =
            (timingSource != nullptr) ? timingSource->getSystemTick() : 0U;

        do
        {
            runFixedPointTransform();
            ++completedBursts;
        } while (timingSource != nullptr &&
                 (timingSource->getSystemTick() - startMs) <
                     WASHIOS_STRESS_ACTIVE_MS);

        vTaskDelay(pdMS_TO_TICKS(WASHIOS_STRESS_PERIOD_MS -
                                 WASHIOS_STRESS_ACTIVE_MS));
    }

    void runFixedPointTransform()
    {
        for (uint32_t iteration = 0U;
             iteration < WASHIOS_STRESS_CPU_BURST_ITERATIONS;
             ++iteration)
        {
            for (uint32_t i = 0U; i < 16U; ++i)
            {
                const uint32_t left = matrixState[(i + 15U) & 0x0FU];
                const uint32_t center = matrixState[i];
                const uint32_t right = matrixState[(i + 1U) & 0x0FU];
                matrixState[i] = (center * 1664525UL) +
                                 (left ^ (right >> 3U)) +
                                 1013904223UL;
            }
        }
    }
};

#endif
