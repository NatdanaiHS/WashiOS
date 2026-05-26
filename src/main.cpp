#include "stm32f4xx_hal.h"

#include "FreeRTOS.h"
#include "task.h"

#include "FaultLog.hpp"
#include "IUart.hpp"
#include "ITiming.hpp"
#include "SystemReset.hpp"
#include "TaskHealth.hpp"
#include "Watchdog.hpp"
#include "WatchdogRunner.hpp"
#include "app/HeartbeatTask.hpp"
#include "app/TelemetryMockTask.hpp"
#include "app/WatchdogTask.hpp"
#include "bsp/Stm32Gpio.hpp"
#include "bsp/Stm32Timing.hpp"
#include "bsp/Stm32Uart.hpp"

void SystemClock_Config(void);
static void Board_GPIO_Init(void);
static void Board_USART2_Init(void);

namespace
{

constexpr core::TaskId HeartbeatTaskId = 1U;
constexpr core::TaskId TelemetryTaskId = 2U;
constexpr uint32_t HeartbeatDeadlineMs = 1500U;
constexpr uint32_t TelemetryDeadlineMs = 800U;
constexpr uint32_t WatchdogPollPeriodMs = 100U;
constexpr uint32_t WatchdogTaskDelayMs = 50U;

void targetSafeFail(void* context)
{
    core::FaultLog<>* const faultLog = static_cast<core::FaultLog<>*>(context);
    if (faultLog != nullptr)
    {
        (void)faultLog->record(core::FaultEventType::SafeFail,
                               HAL_GetTick(),
                               0U,
                               0U,
                               0U);
    }

    core::requestSystemReset();
}

UART_HandleTypeDef huart2 = {};
bsp::Stm32Timing targetTiming;
bsp::Stm32Uart targetTelemetryUart(&huart2);
bsp::Stm32Gpio heartbeatLed(GPIOA, GPIO_PIN_5);
core::TaskHealthRegistry<> systemTaskHealth;
core::FaultLog<> systemFaultLog;
core::Watchdog<> systemWatchdog(targetTiming,
                                systemTaskHealth,
                                systemFaultLog,
                                targetSafeFail,
                                &systemFaultLog);
core::WatchdogRunner<> systemWatchdogRunner(targetTiming,
                                            systemWatchdog,
                                            WatchdogPollPeriodMs);

} /* namespace */

static HeartbeatTask heartbeatTask;
static TelemetryMockTask telemetryTask;
static WatchdogTask<> watchdogTask(systemWatchdogRunner, WatchdogTaskDelayMs);

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    Board_GPIO_Init();
    Board_USART2_Init();
    targetTiming.initialize();
    heartbeatLed.initializeOutput(false);

    const uint64_t startupTimeMs = targetTiming.getSystemTick();
    (void)systemTaskHealth.registerTask(HeartbeatTaskId,
                                        HeartbeatDeadlineMs,
                                        true,
                                        startupTimeMs);
    (void)systemTaskHealth.registerTask(TelemetryTaskId,
                                        TelemetryDeadlineMs,
                                        true,
                                        startupTimeMs);

    heartbeatTask.ConfigureHealth(&systemTaskHealth,
                                  &targetTiming,
                                  HeartbeatTaskId);
    heartbeatTask.ConfigureLed(&heartbeatLed);
    telemetryTask.ConfigureHealth(&systemTaskHealth,
                                  &targetTiming,
                                  TelemetryTaskId);
    telemetryTask.ConfigureTelemetry(&systemFaultLog,
                                     &targetTelemetryUart);

    heartbeatTask.Start("Heartbeat", tskIDLE_PRIORITY + 1);
    telemetryTask.Start("Telemetry", tskIDLE_PRIORITY + 2);
    watchdogTask.Start("Watchdog", configMAX_PRIORITIES - 1U);

    vTaskStartScheduler();

    while (1)
    {
    }
}

void SystemClock_Config(void)
{
    RCC_OscInitTypeDef osc = {};
    RCC_ClkInitTypeDef clk = {};

    __HAL_RCC_PWR_CLK_ENABLE();
    __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE1);

    osc.OscillatorType = RCC_OSCILLATORTYPE_HSI;
    osc.HSIState = RCC_HSI_ON;
    osc.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
    osc.PLL.PLLState = RCC_PLL_ON;
    osc.PLL.PLLSource = RCC_PLLSOURCE_HSI;
    osc.PLL.PLLM = 16;
    osc.PLL.PLLN = 400;
    osc.PLL.PLLP = RCC_PLLP_DIV4;
    osc.PLL.PLLQ = 7;

    if (HAL_RCC_OscConfig(&osc) != HAL_OK)
    {
        core::requestSystemReset();
    }

    clk.ClockType = RCC_CLOCKTYPE_HCLK |
                    RCC_CLOCKTYPE_SYSCLK |
                    RCC_CLOCKTYPE_PCLK1 |
                    RCC_CLOCKTYPE_PCLK2;
    clk.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
    clk.AHBCLKDivider = RCC_SYSCLK_DIV1;
    clk.APB1CLKDivider = RCC_HCLK_DIV2;
    clk.APB2CLKDivider = RCC_HCLK_DIV1;

    if (HAL_RCC_ClockConfig(&clk, FLASH_LATENCY_3) != HAL_OK)
    {
        core::requestSystemReset();
    }

    HAL_SYSTICK_Config(HAL_RCC_GetHCLKFreq() / 1000U);
    HAL_SYSTICK_CLKSourceConfig(SYSTICK_CLKSOURCE_HCLK);
    HAL_NVIC_SetPriority(SysTick_IRQn, 15U, 0U);
}

static void Board_GPIO_Init(void)
{
    __HAL_RCC_GPIOA_CLK_ENABLE();
}

static void Board_USART2_Init(void)
{
    __HAL_RCC_USART2_CLK_ENABLE();
    __HAL_RCC_GPIOA_CLK_ENABLE();

    GPIO_InitTypeDef gpio = {};
    gpio.Pin = GPIO_PIN_2 | GPIO_PIN_3;
    gpio.Mode = GPIO_MODE_AF_PP;
    gpio.Pull = GPIO_PULLUP;
    gpio.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
    gpio.Alternate = GPIO_AF7_USART2;
    HAL_GPIO_Init(GPIOA, &gpio);

    huart2.Instance = USART2;
    huart2.Init.BaudRate = 115200;
    huart2.Init.WordLength = UART_WORDLENGTH_8B;
    huart2.Init.StopBits = UART_STOPBITS_1;
    huart2.Init.Parity = UART_PARITY_NONE;
    huart2.Init.Mode = UART_MODE_TX_RX;
    huart2.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    huart2.Init.OverSampling = UART_OVERSAMPLING_16;

    if (HAL_UART_Init(&huart2) != HAL_OK)
    {
        core::requestSystemReset();
    }
}

extern "C" void vApplicationGetIdleTaskMemory(StaticTask_t** ppxIdleTaskTCBBuffer,
                                              StackType_t** ppxIdleTaskStackBuffer,
                                              uint32_t* pulIdleTaskStackSize)
{
    static StaticTask_t idleTaskTCB;
    static StackType_t idleTaskStack[configMINIMAL_STACK_SIZE];

    *ppxIdleTaskTCBBuffer = &idleTaskTCB;
    *ppxIdleTaskStackBuffer = idleTaskStack;
    *pulIdleTaskStackSize = configMINIMAL_STACK_SIZE;
}

extern "C" void vApplicationGetTimerTaskMemory(StaticTask_t** ppxTimerTaskTCBBuffer,
                                               StackType_t** ppxTimerTaskStackBuffer,
                                               uint32_t* pulTimerTaskStackSize)
{
    static StaticTask_t timerTaskTCB;
    static StackType_t timerTaskStack[configTIMER_TASK_STACK_DEPTH];

    *ppxTimerTaskTCBBuffer = &timerTaskTCB;
    *ppxTimerTaskStackBuffer = timerTaskStack;
    *pulTimerTaskStackSize = configTIMER_TASK_STACK_DEPTH;
}

extern "C" void vApplicationStackOverflowHook(TaskHandle_t xTask, char *pcTaskName)
{
    (void)xTask;
    (void)pcTaskName;

    (void)systemFaultLog.record(core::FaultEventType::StackOverflow,
                                0U,
                                0U,
                                0U,
                                0U);

    core::requestSystemReset();
}
