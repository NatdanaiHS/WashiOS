#include <cstddef>
#include <cstdint>

#include "stm32f4xx_hal.h"
#include "FixedTextWriter.hpp"
#include "HostModeCommandParser.hpp"
#include "PayloadProtocol.hpp"
#include "Stm32F411BoardUart.hpp"
#include "Stm32F411InterruptUart.hpp"

namespace
{

constexpr uint32_t UartTimeoutMs = 10U;
constexpr uint32_t DefaultDelayedResponseMs = 250U;
constexpr uint32_t LinkStatusPeriodMs = 1000U;
constexpr std::size_t MaxDebugBytesPerCycle = 32U;
constexpr std::size_t MaxLinkBytesPerCycle = 64U;

UART_HandleTypeDef debugUart = {};
UART_HandleTypeDef linkUart = {};
bsp::Stm32F411InterruptUart debugTransport(&debugUart);
bsp::Stm32F411InterruptUart linkTransport(&linkUart);
comms::PayloadFrameDecoder requestDecoder;
HostModeCommandParser hostCommandParser;
comms::PayloadMode currentMode = comms::PayloadMode::Normal;
uint32_t delayedResponseMs = DefaultDelayedResponseMs;
uint32_t sampleCounter = 0U;
uint32_t nextLinkStatusMs = LinkStatusPeriodMs;
uint32_t lastLinkOverflow = 0U;
uint32_t lastLinkHardwareError = 0U;
uint32_t lastHostOverflow = 0U;
uint32_t lastHostHardwareError = 0U;
bool linkActiveLogged = false;

[[noreturn]] void safeFail()
{
    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_5, GPIO_PIN_SET);
    for (;;)
    {
    }
}

void initializeClock()
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
    osc.PLL.PLLM = 16U;
    osc.PLL.PLLN = 400U;
    osc.PLL.PLLP = RCC_PLLP_DIV4;
    osc.PLL.PLLQ = 7U;
    if (HAL_RCC_OscConfig(&osc) != HAL_OK)
    {
        safeFail();
    }

    clk.ClockType = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK |
                    RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    clk.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
    clk.AHBCLKDivider = RCC_SYSCLK_DIV1;
    clk.APB1CLKDivider = RCC_HCLK_DIV2;
    clk.APB2CLKDivider = RCC_HCLK_DIV1;
    if (HAL_RCC_ClockConfig(&clk, FLASH_LATENCY_3) != HAL_OK)
    {
        safeFail();
    }
    HAL_SYSTICK_Config(HAL_RCC_GetHCLKFreq() / 1000U);
    HAL_SYSTICK_CLKSourceConfig(SYSTICK_CLKSOURCE_HCLK);
    HAL_NVIC_SetPriority(SysTick_IRQn, 15U, 0U);
}

void initializeGpio()
{
    __HAL_RCC_GPIOA_CLK_ENABLE();
    GPIO_InitTypeDef gpio = {};
    gpio.Pin = GPIO_PIN_5;
    gpio.Mode = GPIO_MODE_OUTPUT_PP;
    gpio.Pull = GPIO_NOPULL;
    gpio.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(GPIOA, &gpio);
    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_5, GPIO_PIN_RESET);
}

template<std::size_t Capacity>
void writeDebug(const core::FixedTextWriter<Capacity>& line)
{
    (void)debugTransport.writeBuffer(line.data(), line.size(), UartTimeoutMs);
}

void logLiteral(const char* text)
{
    core::FixedTextWriter<112U> line;
    (void)line.append(text);
    writeDebug(line);
}

const char* modeName(comms::PayloadMode mode)
{
    switch (mode)
    {
    case comms::PayloadMode::Normal: return "NORMAL";
    case comms::PayloadMode::Silent: return "SILENT";
    case comms::PayloadMode::BadCrc: return "BAD_CRC";
    case comms::PayloadMode::Delayed: return "DELAYED";
    default: return "UNKNOWN";
    }
}

void logMode()
{
    core::FixedTextWriter<64U> line;
    (void)line.append("[PAYLOAD] MODE=");
    (void)line.append(modeName(currentMode));
    if (currentMode == comms::PayloadMode::Delayed)
    {
        (void)line.append(" delay_ms=");
        (void)line.appendU32(delayedResponseMs);
    }
    (void)line.append("\r\n");
    writeDebug(line);
}

void serviceHostCommands()
{
    for (std::size_t count = 0U;
         count < MaxDebugBytesPerCycle && debugTransport.available() > 0U;
         ++count)
    {
        uint8_t byte = 0U;
        if (!debugTransport.readBuffer(&byte, 1U, 0U))
        {
            return;
        }
        comms::PayloadMode selectedMode = currentMode;
        uint32_t selectedDelayMs = delayedResponseMs;
        const HostModeCommandParser::Event event =
            hostCommandParser.consume(byte, selectedMode, selectedDelayMs);
        if (event == HostModeCommandParser::Event::ModeSelected)
        {
            currentMode = selectedMode;
            delayedResponseMs = selectedDelayMs;
            logMode();
        }
        else if (event == HostModeCommandParser::Event::InvalidCommand)
        {
            logLiteral("[PAYLOAD] COMMAND_REJECTED\r\n");
        }
    }
}

int32_t simulatedSensorValue()
{
    return 25000 + ((static_cast<int32_t>(sampleCounter % 21U) - 10) * 25);
}

void handleRequest(const uint8_t* requestData)
{
    comms::PayloadFrame request = {};
    if (comms::decodePayloadFrame(requestData, comms::PayloadWireSize, request) !=
            comms::PayloadValidationResult::Ok ||
        request.type != comms::PayloadMessageType::PollRequest)
    {
        logLiteral("[PAYLOAD] REQUEST_REJECTED\r\n");
        return;
    }
    if (!linkActiveLogged)
    {
        logLiteral("[PAYLOAD] LINK_ACTIVE\r\n");
        linkActiveLogged = true;
    }

    HAL_GPIO_TogglePin(GPIOA, GPIO_PIN_5);
    ++sampleCounter;
    if (currentMode == comms::PayloadMode::Silent)
    {
        return;
    }
    if (currentMode == comms::PayloadMode::Delayed)
    {
        HAL_Delay(delayedResponseMs);
    }

    const comms::PayloadTelemetry telemetry = {
        HAL_GetTick(), sampleCounter, simulatedSensorValue(), currentMode
    };
    uint8_t response[comms::PayloadWireSize] = {};
    if (!comms::encodeTelemetryResponse(request.sequence, telemetry,
                                        response, sizeof(response)))
    {
        safeFail();
    }
    if (currentMode == comms::PayloadMode::BadCrc)
    {
        response[comms::PayloadCrcOffset] ^= 0x01U;
    }
    if (!linkTransport.writeBuffer(response, sizeof(response), UartTimeoutMs))
    {
        logLiteral("[PAYLOAD] LINK_WRITE_FAILED\r\n");
    }
}

void serviceLink()
{
    for (std::size_t count = 0U;
         count < MaxLinkBytesPerCycle && linkTransport.available() > 0U;
         ++count)
    {
        uint8_t byte = 0U;
        if (!linkTransport.readBuffer(&byte, 1U, 0U))
        {
            return;
        }
        const comms::PayloadDecodeEvent event = requestDecoder.consume(byte);
        if (event == comms::PayloadDecodeEvent::FrameReady)
        {
            handleRequest(requestDecoder.frameData());
        }
        else if (event == comms::PayloadDecodeEvent::FrameRejected)
        {
            logLiteral("[PAYLOAD] FRAME_REJECTED\r\n");
        }
    }
}

void logUartCounter(const char* marker, uint32_t linkCount, uint32_t hostCount)
{
    core::FixedTextWriter<112U> line;
    (void)line.append(marker);
    (void)line.append(" link=");
    (void)line.appendU32(linkCount);
    (void)line.append(" host=");
    (void)line.appendU32(hostCount);
    (void)line.append("\r\n");
    writeDebug(line);
}

void serviceUartStatus(uint32_t nowMs)
{
    if (static_cast<int32_t>(nowMs - nextLinkStatusMs) < 0)
    {
        return;
    }
    const uint32_t linkOverflow = linkTransport.overflowCount();
    const uint32_t hostOverflow = debugTransport.overflowCount();
    const uint32_t linkError = linkTransport.hardwareErrorCount();
    const uint32_t hostError = debugTransport.hardwareErrorCount();
    if (linkOverflow != lastLinkOverflow || hostOverflow != lastHostOverflow)
    {
        logUartCounter("[PAYLOAD] UART_RX_OVERFLOW", linkOverflow, hostOverflow);
        lastLinkOverflow = linkOverflow;
        lastHostOverflow = hostOverflow;
    }
    if (linkError != lastLinkHardwareError || hostError != lastHostHardwareError)
    {
        logUartCounter("[PAYLOAD] UART_RX_ERROR", linkError, hostError);
        lastLinkHardwareError = linkError;
        lastHostHardwareError = hostError;
    }
    nextLinkStatusMs = nowMs + LinkStatusPeriodMs;
}

} /* namespace */

extern "C" void USART1_IRQHandler()
{
    linkTransport.handleInterrupt();
}

extern "C" void USART2_IRQHandler()
{
    debugTransport.handleInterrupt();
}

extern "C" void SysTick_Handler()
{
    HAL_IncTick();
}

int main()
{
    HAL_Init();
    initializeClock();
    initializeGpio();
    if (!bsp::initializeF411HostUart(&debugUart) ||
        !bsp::initializeF411LinkUart(&linkUart) ||
        !debugTransport.enableInterruptReceive() ||
        !linkTransport.enableInterruptReceive())
    {
        safeFail();
    }
    HAL_NVIC_SetPriority(USART1_IRQn, 6U, 0U);
    HAL_NVIC_EnableIRQ(USART1_IRQn);
    HAL_NVIC_SetPriority(USART2_IRQn, 6U, 0U);
    HAL_NVIC_EnableIRQ(USART2_IRQn);
    HAL_Delay(100U);
    logLiteral("[PAYLOAD] READY board=NUCLEO-F411RE role=PAYLOAD mode=NORMAL baud=115200\r\n");

    for (;;)
    {
        const uint32_t nowMs = HAL_GetTick();
        serviceHostCommands();
        serviceLink();
        serviceUartStatus(nowMs);
        HAL_Delay(1U);
    }
}
