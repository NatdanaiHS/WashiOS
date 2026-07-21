#include "bsp/g4/Stm32G4BoardUart.hpp"

#include "stm32g4xx_hal.h"

namespace
{

bool finishUartInitialization(UART_HandleTypeDef& uart)
{
    return HAL_UART_Init(&uart) == HAL_OK &&
           HAL_UARTEx_SetTxFifoThreshold(&uart, UART_TXFIFO_THRESHOLD_1_8) == HAL_OK &&
           HAL_UARTEx_SetRxFifoThreshold(&uart, UART_RXFIFO_THRESHOLD_1_8) == HAL_OK &&
           HAL_UARTEx_DisableFifoMode(&uart) == HAL_OK;
}

void setCommonUartConfiguration(UART_HandleTypeDef& uart)
{
    uart.Init.BaudRate = 115200U;
    uart.Init.WordLength = UART_WORDLENGTH_8B;
    uart.Init.StopBits = UART_STOPBITS_1;
    uart.Init.Parity = UART_PARITY_NONE;
    uart.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    uart.Init.OverSampling = UART_OVERSAMPLING_16;
    uart.Init.OneBitSampling = UART_ONE_BIT_SAMPLE_DISABLE;
    uart.Init.ClockPrescaler = UART_PRESCALER_DIV1;
    uart.AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_NO_INIT;
}

} /* namespace */

namespace bsp
{

bool initializeG4DebugUart(void* uartHandle) noexcept
{
    if (uartHandle == nullptr)
    {
        return false;
    }

    __HAL_RCC_USART2_CLK_ENABLE();
    __HAL_RCC_GPIOA_CLK_ENABLE();
    GPIO_InitTypeDef gpio = {};
    gpio.Pin = GPIO_PIN_2;
    gpio.Mode = GPIO_MODE_AF_PP;
    gpio.Pull = GPIO_PULLUP;
    gpio.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
    gpio.Alternate = GPIO_AF7_USART2;
    HAL_GPIO_Init(GPIOA, &gpio);

    UART_HandleTypeDef& uart = *static_cast<UART_HandleTypeDef*>(uartHandle);
    uart.Instance = USART2;
    setCommonUartConfiguration(uart);
    uart.Init.Mode = UART_MODE_TX;
    return finishUartInitialization(uart);
}

bool initializeG4PayloadUart(void* uartHandle) noexcept
{
    if (uartHandle == nullptr)
    {
        return false;
    }

    __HAL_RCC_USART1_CLK_ENABLE();
    __HAL_RCC_GPIOC_CLK_ENABLE();
    GPIO_InitTypeDef gpio = {};
    gpio.Pin = GPIO_PIN_4 | GPIO_PIN_5;
    gpio.Mode = GPIO_MODE_AF_PP;
    gpio.Pull = GPIO_PULLUP;
    gpio.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
    gpio.Alternate = GPIO_AF7_USART1;
    HAL_GPIO_Init(GPIOC, &gpio);

    UART_HandleTypeDef& uart = *static_cast<UART_HandleTypeDef*>(uartHandle);
    uart.Instance = USART1;
    setCommonUartConfiguration(uart);
    uart.Init.Mode = UART_MODE_TX_RX;
    return finishUartInitialization(uart);
}

} /* namespace bsp */
