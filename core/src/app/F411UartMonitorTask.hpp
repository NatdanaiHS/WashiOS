#pragma once

#include <cstdint>

#include "FixedTextWriter.hpp"
#include "IUart.hpp"
#include "WashiTask.hpp"
#include "bsp/f4/Stm32F411InterruptUart.hpp"

class F411UartMonitorTask final : public rtos_config::WashiTask<384>
{
public:
    F411UartMonitorTask(bsp::Stm32F411InterruptUart& monitoredTransport,
                        hal::IUart& consoleTransport)
        : monitored(monitoredTransport), console(consoleTransport)
    {
    }

protected:
    void Run() override
    {
        for (;;)
        {
            reportChanges();
            vTaskDelay(pdMS_TO_TICKS(100U));
        }
    }

private:
    bsp::Stm32F411InterruptUart& monitored;
    hal::IUart& console;
    uint32_t lastOverflowCount = 0U;
    uint32_t lastHardwareErrorCount = 0U;

    void reportChanges()
    {
        const uint32_t overflow = monitored.overflowCount();
        const uint32_t hardware = monitored.hardwareErrorCount();
        if (overflow != lastOverflowCount)
        {
            core::FixedTextWriter<80U> line;
            (void)line.append("[OBC] UART_RX_OVERFLOW count=");
            (void)line.appendU32(overflow);
            (void)line.append("\r\n");
            (void)console.writeBuffer(line.data(), line.size(), 10U);
            lastOverflowCount = overflow;
        }
        if (hardware != lastHardwareErrorCount)
        {
            core::FixedTextWriter<80U> line;
            (void)line.append("[OBC] UART_RX_ERROR count=");
            (void)line.appendU32(hardware);
            (void)line.append("\r\n");
            (void)console.writeBuffer(line.data(), line.size(), 10U);
            lastHardwareErrorCount = hardware;
        }
    }
};
