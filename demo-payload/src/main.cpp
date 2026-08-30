#include <cstddef>
#include <cstdint>

#include "stm32g4xx_hal.h"
#include "FixedTextWriter.hpp"
#include "HostModeCommandParser.hpp"
#include "PayloadProtocol.hpp"

namespace
{

constexpr uint32_t BaudRate = 115200U;
constexpr uint32_t UartTimeoutMs = 10U;
constexpr uint32_t ButtonDebounceMs = 50U;
constexpr uint32_t DefaultDelayedResponseMs = 250U;
constexpr uint32_t LinkStatusPeriodMs = 1000U;
constexpr std::size_t LinkReceiveBufferCapacity = 128U;
constexpr std::size_t DebugReceiveBufferCapacity = 64U;
constexpr std::size_t MaxDebugBytesPerCycle = 32U;

UART_HandleTypeDef debugUart = {};
UART_HandleTypeDef linkUart = {};
comms::PayloadFrameDecoder requestDecoder;
comms::PayloadMode currentMode = comms::PayloadMode::Normal;
uint32_t delayedResponseMs = DefaultDelayedResponseMs;
uint32_t sampleCounter = 0U;
uint8_t linkReceiveBuffer[LinkReceiveBufferCapacity] = {};
uint8_t debugReceiveBuffer[DebugReceiveBufferCapacity] = {};
volatile std::size_t linkReceiveHead = 0U;
volatile std::size_t linkReceiveTail = 0U;
volatile std::size_t debugReceiveHead = 0U;
volatile std::size_t debugReceiveTail = 0U;
HostModeCommandParser hostCommandParser;
uint32_t linkRxByteCount = 0U;
volatile uint32_t linkUartErrorCount = 0U;
uint32_t lastReportedLinkUartErrorCount = 0U;
uint32_t nextLinkStatusMs = LinkStatusPeriodMs;
bool linkActiveLogged = false;
GPIO_PinState buttonIdleState = GPIO_PIN_RESET;
GPIO_PinState buttonRawState = GPIO_PIN_RESET;
GPIO_PinState buttonStableState = GPIO_PIN_RESET;
uint32_t buttonChangedAtMs = 0U;

[[noreturn]] void safeFail()
{
    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_5, GPIO_PIN_SET);
    for (;;) {}
}

bool finishUartInitialization(UART_HandleTypeDef& uart)
{
    return HAL_UART_Init(&uart) == HAL_OK &&
           HAL_UARTEx_SetTxFifoThreshold(&uart, UART_TXFIFO_THRESHOLD_1_8) == HAL_OK &&
           HAL_UARTEx_SetRxFifoThreshold(&uart, UART_RXFIFO_THRESHOLD_1_8) == HAL_OK &&
           HAL_UARTEx_DisableFifoMode(&uart) == HAL_OK;
}

void setCommonUartConfiguration(UART_HandleTypeDef& uart)
{
    uart.Init.BaudRate = BaudRate;
    uart.Init.WordLength = UART_WORDLENGTH_8B;
    uart.Init.StopBits = UART_STOPBITS_1;
    uart.Init.Parity = UART_PARITY_NONE;
    uart.Init.Mode = UART_MODE_TX_RX;
    uart.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    uart.Init.OverSampling = UART_OVERSAMPLING_16;
    uart.Init.OneBitSampling = UART_ONE_BIT_SAMPLE_DISABLE;
    uart.Init.ClockPrescaler = UART_PRESCALER_DIV1;
    uart.AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_NO_INIT;
}

void initializeClock()
{
    RCC_OscInitTypeDef oscillator = {};
    RCC_ClkInitTypeDef clock = {};
    oscillator.OscillatorType = RCC_OSCILLATORTYPE_HSI;
    oscillator.HSIState = RCC_HSI_ON;
    oscillator.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
    oscillator.PLL.PLLState = RCC_PLL_NONE;
    if (HAL_RCC_OscConfig(&oscillator) != HAL_OK) safeFail();

    clock.ClockType = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK |
                      RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    clock.SYSCLKSource = RCC_SYSCLKSOURCE_HSI;
    clock.AHBCLKDivider = RCC_SYSCLK_DIV1;
    clock.APB1CLKDivider = RCC_HCLK_DIV1;
    clock.APB2CLKDivider = RCC_HCLK_DIV1;
    if (HAL_RCC_ClockConfig(&clock, FLASH_LATENCY_0) != HAL_OK) safeFail();
}

void initializeGpio()
{
    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOC_CLK_ENABLE();
    GPIO_InitTypeDef gpio = {};
    gpio.Pin = GPIO_PIN_5;
    gpio.Mode = GPIO_MODE_OUTPUT_PP;
    gpio.Pull = GPIO_NOPULL;
    gpio.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(GPIOA, &gpio);
    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_5, GPIO_PIN_RESET);

    gpio = {};
    gpio.Pin = GPIO_PIN_13;
    gpio.Mode = GPIO_MODE_INPUT;
    gpio.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(GPIOC, &gpio);
}

void initializeDebugUart()
{
    __HAL_RCC_LPUART1_CLK_ENABLE();
    GPIO_InitTypeDef gpio = {};
    gpio.Pin = GPIO_PIN_2 | GPIO_PIN_3;
    gpio.Mode = GPIO_MODE_AF_PP;
    gpio.Pull = GPIO_PULLUP;
    gpio.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
    gpio.Alternate = GPIO_AF12_LPUART1;
    HAL_GPIO_Init(GPIOA, &gpio);

    debugUart.Instance = LPUART1;
    setCommonUartConfiguration(debugUart);
    if (!finishUartInitialization(debugUart)) safeFail();

    __HAL_UART_CLEAR_OREFLAG(&debugUart);
    __HAL_UART_CLEAR_FEFLAG(&debugUart);
    __HAL_UART_CLEAR_NEFLAG(&debugUart);
    __HAL_UART_ENABLE_IT(&debugUart, UART_IT_RXNE);
    __HAL_UART_ENABLE_IT(&debugUart, UART_IT_ERR);
    HAL_NVIC_SetPriority(LPUART1_IRQn, 6U, 0U);
    HAL_NVIC_EnableIRQ(LPUART1_IRQn);
}

void initializeLinkUart()
{
    __HAL_RCC_USART1_CLK_ENABLE();
    GPIO_InitTypeDef gpio = {};
    gpio.Pin = GPIO_PIN_4 | GPIO_PIN_5;
    gpio.Mode = GPIO_MODE_AF_PP;
    gpio.Pull = GPIO_PULLUP;
    gpio.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
    gpio.Alternate = GPIO_AF7_USART1;
    HAL_GPIO_Init(GPIOC, &gpio);

    linkUart.Instance = USART1;
    setCommonUartConfiguration(linkUart);
    if (!finishUartInitialization(linkUart)) safeFail();

    __HAL_UART_CLEAR_OREFLAG(&linkUart);
    __HAL_UART_CLEAR_FEFLAG(&linkUart);
    __HAL_UART_CLEAR_NEFLAG(&linkUart);
    __HAL_UART_ENABLE_IT(&linkUart, UART_IT_RXNE);
    __HAL_UART_ENABLE_IT(&linkUart, UART_IT_ERR);
    HAL_NVIC_SetPriority(USART1_IRQn, 6U, 0U);
    HAL_NVIC_EnableIRQ(USART1_IRQn);
}

template<std::size_t Capacity>
void writeDebug(const core::FixedTextWriter<Capacity>& line)
{
    (void)HAL_UART_Transmit(&debugUart, const_cast<uint8_t*>(line.data()),
                            static_cast<uint16_t>(line.size()), UartTimeoutMs);
}

void logLiteral(const char* text)
{
    core::FixedTextWriter<96U> line;
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

void cycleMode()
{
    currentMode = static_cast<comms::PayloadMode>(
        (static_cast<uint8_t>(currentMode) + 1U) % 4U);
    logMode();
}

bool readDebugByte(uint8_t& byte)
{
    if (debugReceiveTail == debugReceiveHead)
    {
        return false;
    }

    byte = debugReceiveBuffer[debugReceiveTail];
    debugReceiveTail = (debugReceiveTail + 1U) % DebugReceiveBufferCapacity;
    return true;
}

void serviceHostCommands()
{
    for (std::size_t count = 0U; count < MaxDebugBytesPerCycle; ++count)
    {
        uint8_t byte = 0U;
        if (!readDebugByte(byte))
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

void serviceButton(uint32_t nowMs)
{
    const GPIO_PinState raw = HAL_GPIO_ReadPin(GPIOC, GPIO_PIN_13);
    if (raw != buttonRawState)
    {
        buttonRawState = raw;
        buttonChangedAtMs = nowMs;
    }
    if (raw != buttonStableState &&
        static_cast<uint32_t>(nowMs - buttonChangedAtMs) >= ButtonDebounceMs)
    {
        buttonStableState = raw;
        if (buttonStableState != buttonIdleState) cycleMode();
    }
}

int32_t simulatedSensorValue()
{
    return 25000 + ((static_cast<int32_t>(sampleCounter % 21U) - 10) * 25);
}

void logUartErrors()
{
    core::FixedTextWriter<64U> line;
    (void)line.append("[PAYLOAD] UART_ERRORS=");
    (void)line.appendU32(linkUartErrorCount);
    (void)line.append("\r\n");
    writeDebug(line);
}

bool readLinkByte(uint8_t& byte)
{
    if (linkReceiveTail == linkReceiveHead)
    {
        return false;
    }

    byte = linkReceiveBuffer[linkReceiveTail];
    linkReceiveTail = (linkReceiveTail + 1U) % LinkReceiveBufferCapacity;
    return true;
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
    if (currentMode == comms::PayloadMode::Delayed) HAL_Delay(delayedResponseMs);

    const comms::PayloadTelemetry telemetry = {
        HAL_GetTick(), sampleCounter, simulatedSensorValue(), currentMode
    };
    uint8_t response[comms::PayloadWireSize] = {};
    if (!comms::encodeTelemetryResponse(request.sequence, telemetry,
                                        response, sizeof(response))) safeFail();
    if (currentMode == comms::PayloadMode::BadCrc)
    {
        response[comms::PayloadCrcOffset] ^= 0x01U;
    }

    (void)HAL_UART_Transmit(&linkUart, response,
                            static_cast<uint16_t>(sizeof(response)), UartTimeoutMs);
}

void serviceLink()
{
    uint8_t byte = 0U;
    while (readLinkByte(byte))
    {
        ++linkRxByteCount;
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

void serviceLinkStatus(uint32_t nowMs)
{
    if (static_cast<int32_t>(nowMs - nextLinkStatusMs) >= 0)
    {
        if (linkUartErrorCount != lastReportedLinkUartErrorCount)
        {
            logUartErrors();
            lastReportedLinkUartErrorCount = linkUartErrorCount;
        }
        nextLinkStatusMs = nowMs + LinkStatusPeriodMs;
    }
}

} /* namespace */

extern "C" void LPUART1_IRQHandler()
{
    uint32_t status = debugUart.Instance->ISR;
    while ((status & USART_ISR_RXNE_RXFNE) != 0U)
    {
        const uint8_t byte = static_cast<uint8_t>(debugUart.Instance->RDR);
        const std::size_t next = (debugReceiveHead + 1U) % DebugReceiveBufferCapacity;
        if (next != debugReceiveTail)
        {
            debugReceiveBuffer[debugReceiveHead] = byte;
            debugReceiveHead = next;
        }
        status = debugUart.Instance->ISR;
    }

    if ((status & (USART_ISR_ORE | USART_ISR_FE | USART_ISR_NE)) != 0U)
    {
        debugUart.Instance->ICR = USART_ICR_ORECF | USART_ICR_FECF | USART_ICR_NECF;
    }
}

extern "C" void USART1_IRQHandler()
{
    uint32_t status = linkUart.Instance->ISR;
    while ((status & USART_ISR_RXNE_RXFNE) != 0U)
    {
        const uint8_t byte = static_cast<uint8_t>(linkUart.Instance->RDR);
        const std::size_t next = (linkReceiveHead + 1U) % LinkReceiveBufferCapacity;
        if (next != linkReceiveTail)
        {
            linkReceiveBuffer[linkReceiveHead] = byte;
            linkReceiveHead = next;
        }
        else
        {
            ++linkUartErrorCount;
        }
        status = linkUart.Instance->ISR;
    }

    if ((status & (USART_ISR_ORE | USART_ISR_FE | USART_ISR_NE)) != 0U)
    {
        linkUart.Instance->ICR = USART_ICR_ORECF | USART_ICR_FECF | USART_ICR_NECF;
        ++linkUartErrorCount;
    }
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
    initializeDebugUart();
    initializeLinkUart();
    HAL_Delay(100U);
    buttonIdleState = HAL_GPIO_ReadPin(GPIOC, GPIO_PIN_13);
    buttonRawState = buttonIdleState;
    buttonStableState = buttonIdleState;
    logLiteral("[PAYLOAD] READY board=NUCLEO-G474RE mode=NORMAL baud=115200\r\n");

    for (;;)
    {
        const uint32_t nowMs = HAL_GetTick();
        serviceButton(nowMs);
        serviceHostCommands();
        serviceLink();
        serviceLinkStatus(nowMs);
        HAL_Delay(1U);
    }
}
