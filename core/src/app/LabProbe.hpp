#pragma once

#include <cstdint>

#if defined(WASHIOS_LAB_GPIO) || defined(WASHIOS_STALL_INJECT)
#include "FreeRTOS.h"
#include "task.h"
#include "stm32g4xx_hal.h"
#endif

/*
 * Logic-analyzer probe points for the camera-ready hardware tests (Part B).
 * Compiled to no-ops unless WASHIOS_LAB_GPIO is defined, so the frozen
 * payload-demo and scope builds are unchanged.
 *
 * Event probes TOGGLE (every edge is one event) so that no event is lost when
 * the pulse would be shorter than the analyzer sample period. Span probes are
 * HIGH for the duration of the instrumented call.
 *
 *   Probe           NUCLEO pin   Kind    Meaning
 *   Poll            D2  / PA10   toggle  poll frame handed to the payload UART
 *   Loop            D4  / PB5    toggle  top of each PayloadLinkTask loop
 *   Status          D5  / PB4    span    reportStatus() that emits a line
 *   Write           D6  / PB10   span    every console writeLine()
 *   Accept          D8  / PA9    toggle  response frame accepted (Ok)
 *   Recovery        D9  / PC7    toggle  Offline -> Online recovery
 *   Stall           D10 / PB6    level   injected stall began (stays high)
 *   WatchdogRecord  D11 / PA7    level   WATCHDOG_TIMEOUT recorded (stays high)
 */
namespace lab
{

enum class Probe : uint8_t
{
    Poll,
    Loop,
    Status,
    Write,
    Accept,
    Recovery,
    Stall,
    WatchdogRecord
};

#if defined(WASHIOS_LAB_GPIO)

struct ProbePin
{
    GPIO_TypeDef* port;
    uint16_t pin;
};

inline ProbePin pinFor(Probe probe)
{
    switch (probe)
    {
    case Probe::Poll: return {GPIOA, GPIO_PIN_10};
    case Probe::Loop: return {GPIOB, GPIO_PIN_5};
    case Probe::Status: return {GPIOB, GPIO_PIN_4};
    case Probe::Write: return {GPIOB, GPIO_PIN_10};
    case Probe::Accept: return {GPIOA, GPIO_PIN_9};
    case Probe::Recovery: return {GPIOC, GPIO_PIN_7};
    case Probe::Stall: return {GPIOB, GPIO_PIN_6};
    case Probe::WatchdogRecord:
    default: return {GPIOA, GPIO_PIN_7};
    }
}

inline void initialize()
{
    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();
    __HAL_RCC_GPIOC_CLK_ENABLE();

    for (uint8_t index = 0U; index <= static_cast<uint8_t>(Probe::WatchdogRecord); ++index)
    {
        const ProbePin probePin = pinFor(static_cast<Probe>(index));
        GPIO_InitTypeDef gpio = {};
        gpio.Pin = probePin.pin;
        gpio.Mode = GPIO_MODE_OUTPUT_PP;
        gpio.Pull = GPIO_NOPULL;
        gpio.Speed = GPIO_SPEED_FREQ_HIGH;
        HAL_GPIO_WritePin(probePin.port, probePin.pin, GPIO_PIN_RESET);
        HAL_GPIO_Init(probePin.port, &gpio);
    }
}

inline void high(Probe probe)
{
    const ProbePin probePin = pinFor(probe);
    probePin.port->BSRR = probePin.pin;
}

inline void low(Probe probe)
{
    const ProbePin probePin = pinFor(probe);
    probePin.port->BRR = probePin.pin;
}

/* Each event probe is driven from a single task, so read-modify-write is safe. */
inline void toggle(Probe probe)
{
    const ProbePin probePin = pinFor(probe);
    probePin.port->ODR ^= probePin.pin;
}

#else

inline void initialize() {}
inline void high(Probe) {}
inline void low(Probe) {}
inline void toggle(Probe) {}

#endif

/*
 * Stall injection (B3). WASHIOS_STALL_INJECT selects the task that stops
 * checking in: 1 = PayloadLink, 2 = Heartbeat. The stalled task blocks forever
 * instead of spinning, so it starves no other task and only its own health
 * check-ins stop.
 */
enum class StallTarget : uint8_t
{
    None = 0U,
    PayloadLink = 1U,
    Heartbeat = 2U
};

#if defined(WASHIOS_STALL_INJECT)
#if !defined(WASHIOS_STALL_AFTER_MS)
#define WASHIOS_STALL_AFTER_MS 10000U
#endif

inline void stallIfDue(StallTarget target)
{
    if (static_cast<uint8_t>(target) != static_cast<uint8_t>(WASHIOS_STALL_INJECT))
    {
        return;
    }

    const uint32_t nowMs =
        static_cast<uint32_t>(xTaskGetTickCount()) * static_cast<uint32_t>(portTICK_PERIOD_MS);
    if (nowMs < static_cast<uint32_t>(WASHIOS_STALL_AFTER_MS))
    {
        return;
    }

    high(Probe::Stall);
    for (;;)
    {
        vTaskDelay(portMAX_DELAY);
    }
}
#else
inline void stallIfDue(StallTarget) {}
#endif

} /* namespace lab */
