#pragma once

#include "stm32f4xx_hal.h"

namespace bsp
{

inline void setF411UartConfiguration(UART_HandleTypeDef& uart) noexcept
{
    uart.Init.BaudRate = 115200U;
    uart.Init.WordLength = UART_WORDLENGTH_8B;
    uart.Init.StopBits = UART_STOPBITS_1;
    uart.Init.Parity = UART_PARITY_NONE;
    uart.Init.Mode = UART_MODE_TX_RX;
    uart.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    uart.Init.OverSampling = UART_OVERSAMPLING_16;
}

inline bool initializeF411HostUart(void* uartHandle) noexcept
{
    if (uartHandle == nullptr)
    {
        return false;
    }
    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_USART2_CLK_ENABLE();
    GPIO_InitTypeDef gpio = {};
    gpio.Pin = GPIO_PIN_2 | GPIO_PIN_3;
    gpio.Mode = GPIO_MODE_AF_PP;
    gpio.Pull = GPIO_PULLUP;
    gpio.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
    gpio.Alternate = GPIO_AF7_USART2;
    HAL_GPIO_Init(GPIOA, &gpio);

    UART_HandleTypeDef& uart = *static_cast<UART_HandleTypeDef*>(uartHandle);
    uart.Instance = USART2;
    setF411UartConfiguration(uart);
    return HAL_UART_Init(&uart) == HAL_OK;
}

inline bool initializeF411LinkUart(void* uartHandle) noexcept
{
    if (uartHandle == nullptr)
    {
        return false;
    }
    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_USART1_CLK_ENABLE();
    GPIO_InitTypeDef gpio = {};
    gpio.Pin = GPIO_PIN_9 | GPIO_PIN_10;
    gpio.Mode = GPIO_MODE_AF_PP;
    gpio.Pull = GPIO_PULLUP;
    gpio.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
    gpio.Alternate = GPIO_AF7_USART1;
    HAL_GPIO_Init(GPIOA, &gpio);

    UART_HandleTypeDef& uart = *static_cast<UART_HandleTypeDef*>(uartHandle);
    uart.Instance = USART1;
    setF411UartConfiguration(uart);
    return HAL_UART_Init(&uart) == HAL_OK;
}

} /* namespace bsp */
