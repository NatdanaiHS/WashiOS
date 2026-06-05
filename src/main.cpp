#if defined(STM32G431xx)
#include "stm32g4xx_hal.h"
#else
#include "stm32f4xx_hal.h"
#endif

#include "FreeRTOS.h"
#include "task.h"

#include "BootFailSafe.hpp"
#include "FaultLog.hpp"
#include "CrcProfiler.hpp"
#include "IUart.hpp"
#include "ITiming.hpp"
#include "MemoryConfig.hpp"
#include "SystemReset.hpp"
#include "TaskHealth.hpp"
#include "Watchdog.hpp"
#include "WatchdogRunner.hpp"
#include "app/HeartbeatTask.hpp"
#include "app/TelemetryMockTask.hpp"
#include "app/WatchdogTask.hpp"
#if defined(WASHIOS_STRESS_TEST)
#include "tasks/StressTestTask.hpp"
#endif

#if defined(STM32G431xx)
#include "bsp/g4/Stm32G4Gpio.hpp"
#include "bsp/g4/Stm32G4Timing.hpp"
#include "bsp/g4/Stm32G4Uart.hpp"
#else
#include "bsp/f4/Stm32Gpio.hpp"
#include "bsp/f4/Stm32Timing.hpp"
#include "bsp/f4/Stm32Uart.hpp"
#endif

void SystemClock_Config(void);
static void Board_GPIO_Init(void);
static void Board_USART2_Init(void);
#if defined(STM32G431xx)
static void Board_IWDG_Init(void);
#endif

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

#if !defined(STM32G431xx)
    core::requestSystemReset();
#endif
}

void refreshHardwareWatchdog(void* context)
{
#if defined(STM32G431xx)
    IWDG_HandleTypeDef* const watchdog =
        static_cast<IWDG_HandleTypeDef*>(context);
    if (watchdog != nullptr)
    {
        (void)HAL_IWDG_Refresh(watchdog);
    }
#else
    (void)context;
#endif
}

void requestBootRecovery(void* context)
{
    (void)context;
    core::requestSystemReset();
}

UART_HandleTypeDef huart2 = {};

#if defined(STM32G431xx)
IWDG_HandleTypeDef hiwdg = {};
bsp::Stm32G4Timing targetTiming;
bsp::Stm32G4Uart targetTelemetryUart(&huart2);
bsp::Stm32G4Gpio heartbeatLed(GPIOA, GPIO_PIN_5);
#else
bsp::Stm32Timing targetTiming;
bsp::Stm32Uart targetTelemetryUart(&huart2);
bsp::Stm32Gpio heartbeatLed(GPIOA, GPIO_PIN_5);
#endif

core::TaskHealthRegistry<> systemTaskHealth;
core::FaultLog<> systemFaultLog WASHIOS_RETAINED;
core::Watchdog<> systemWatchdog(targetTiming,
                                systemTaskHealth,
                                systemFaultLog,
                                targetSafeFail,
                                &systemFaultLog,
                                refreshHardwareWatchdog,
#if defined(STM32G431xx)
                                &hiwdg
#else
                                nullptr
#endif
);
core::WatchdogRunner<> systemWatchdogRunner(targetTiming,
                                            systemWatchdog,
                                            WatchdogPollPeriodMs);

} /* namespace */

static HeartbeatTask heartbeatTask;
static TelemetryMockTask telemetryTask;
static WatchdogTask<> watchdogTask(systemWatchdogRunner, WatchdogTaskDelayMs);
#if defined(WASHIOS_STRESS_TEST)
static StressTestTask stressTestTask;

extern "C" void WashiStress_SubmitCommand(uint32_t command)
{
    stressTestTask.SubmitCommand(command);
}
#endif

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    Board_GPIO_Init();
    Board_USART2_Init();
    targetTiming.initialize();
    heartbeatLed.initializeOutput(false);
    (void)systemFaultLog.recoverRetainedState();
#if defined(WASHIOS_PROFILE_CRC)
    core::initializeCrc32Profiler();
#endif

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
#if defined(WASHIOS_STRESS_TEST)
    stressTestTask.Configure(&targetTiming, &heartbeatTask);
#endif

#if defined(STM32G431xx)
    Board_IWDG_Init();
#endif

    bool tasksStarted = heartbeatTask.Start("Heartbeat", tskIDLE_PRIORITY + 1);
    tasksStarted = telemetryTask.Start("Telemetry", tskIDLE_PRIORITY + 2) && tasksStarted;
    tasksStarted = watchdogTask.Start("Watchdog", configMAX_PRIORITIES - 1U) && tasksStarted;
#if defined(WASHIOS_STRESS_TEST)
    tasksStarted = stressTestTask.Start("Stress", WASHIOS_STRESS_PRIORITY) && tasksStarted;
#endif

    if (!core::handleBootTaskStartFailure(tasksStarted,
                                          systemFaultLog,
                                          targetTiming.getSystemTick(),
                                          requestBootRecovery,
                                          nullptr))
    {
        for (;;)
        {
        }
    }

    vTaskStartScheduler();

    /* The scheduler is not expected to return. Reaching this block means
       kernel start-up failed after task creation, so force a deterministic
       recovery path instead of spinning silently. */
    (void)systemFaultLog.record(core::FaultEventType::SafeFail,
                                targetTiming.getSystemTick(),
                                0U,
                                0U,
                                0U);
    core::requestSystemReset();

    for (;;)
    {
    }
}

void SystemClock_Config(void)
{
#if defined(STM32G431xx)
    RCC_OscInitTypeDef osc = {};
    RCC_ClkInitTypeDef clk = {};

    __HAL_RCC_PWR_CLK_ENABLE();
    HAL_PWREx_ControlVoltageScaling(PWR_REGULATOR_VOLTAGE_SCALE1);

    osc.OscillatorType = RCC_OSCILLATORTYPE_HSI | RCC_OSCILLATORTYPE_LSI;
    osc.HSIState = RCC_HSI_ON;
    osc.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
    osc.LSIState = RCC_LSI_ON;
    osc.PLL.PLLState = RCC_PLL_ON;
    osc.PLL.PLLSource = RCC_PLLSOURCE_HSI;
    osc.PLL.PLLM = RCC_PLLM_DIV4;
    osc.PLL.PLLN = 85;
    osc.PLL.PLLP = RCC_PLLP_DIV2;
    osc.PLL.PLLQ = RCC_PLLQ_DIV2;
    osc.PLL.PLLR = RCC_PLLR_DIV2;

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
    clk.APB1CLKDivider = RCC_HCLK_DIV1;
    clk.APB2CLKDivider = RCC_HCLK_DIV1;

    if (HAL_RCC_ClockConfig(&clk, FLASH_LATENCY_4) != HAL_OK)
    {
        core::requestSystemReset();
    }

    HAL_NVIC_SetPriority(SysTick_IRQn, 15U, 0U);
#else
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
#endif
}

#if defined(STM32G431xx)
static void Board_IWDG_Init(void)
{
    hiwdg.Instance = IWDG;
    hiwdg.Init.Prescaler = IWDG_PRESCALER_16;
    hiwdg.Init.Reload = 3999U;
    hiwdg.Init.Window = IWDG_WINDOW_DISABLE;

    if (HAL_IWDG_Init(&hiwdg) != HAL_OK)
    {
        core::requestSystemReset();
    }
}
#endif

static void Board_GPIO_Init(void)
{
    __HAL_RCC_GPIOA_CLK_ENABLE();
}

static void Board_USART2_Init(void)
{
    __HAL_RCC_USART2_CLK_ENABLE();
    __HAL_RCC_GPIOA_CLK_ENABLE();

    GPIO_InitTypeDef gpio = {};
#if defined(STM32G431xx)
    gpio.Pin = GPIO_PIN_2;
#else
    gpio.Pin = GPIO_PIN_2 | GPIO_PIN_3;
#endif
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
#if defined(STM32G431xx)
    huart2.Init.Mode = UART_MODE_TX;
#else
    huart2.Init.Mode = UART_MODE_TX_RX;
#endif
    huart2.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    huart2.Init.OverSampling = UART_OVERSAMPLING_16;
#if defined(STM32G431xx)
    huart2.Init.OneBitSampling = UART_ONE_BIT_SAMPLE_DISABLE;
    huart2.Init.ClockPrescaler = UART_PRESCALER_DIV1;
    huart2.AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_NO_INIT;
#endif

    if (HAL_UART_Init(&huart2) != HAL_OK)
    {
        core::requestSystemReset();
    }

#if defined(STM32G431xx)
    if (HAL_UARTEx_SetTxFifoThreshold(&huart2, UART_TXFIFO_THRESHOLD_1_8) != HAL_OK)
    {
        core::requestSystemReset();
    }

    if (HAL_UARTEx_DisableFifoMode(&huart2) != HAL_OK)
    {
        core::requestSystemReset();
    }
#endif
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
