#include "bsp/g4/Stm32G4Uart.hpp"

#include "stm32g4xx_hal.h"

namespace
{

constexpr std::size_t MaxHalTransferLength = 0xFFFFU;

} /* namespace */

namespace bsp
{

Stm32G4Uart::Stm32G4Uart(void* uartHandle)
    : handle(uartHandle)
{
}

uint32_t Stm32G4Uart::boundedTimeout(uint32_t timeoutMs)
{
    return (timeoutMs < MaxOperationTimeoutMs) ? timeoutMs : MaxOperationTimeoutMs;
}

bool Stm32G4Uart::writeBuffer(const uint8_t* data,
                              std::size_t length,
                              uint32_t timeout_ms)
{
    if ((data == nullptr && length > 0U) || handle == nullptr ||
        length > MaxHalTransferLength)
    {
        return false;
    }

    if (length == 0U)
    {
        return true;
    }

    UART_HandleTypeDef* const uart = static_cast<UART_HandleTypeDef*>(handle);
    if (uart->gState != HAL_UART_STATE_READY)
    {
        return false;
    }

    return HAL_UART_Transmit(uart,
                             const_cast<uint8_t*>(data),
                             static_cast<uint16_t>(length),
                             boundedTimeout(timeout_ms)) == HAL_OK;
}

bool Stm32G4Uart::readBuffer(uint8_t* buffer,
                             std::size_t length,
                             uint32_t timeout_ms)
{
    if ((buffer == nullptr && length > 0U) || handle == nullptr ||
        length > MaxHalTransferLength)
    {
        return false;
    }

    if (length == 0U)
    {
        return true;
    }

    (void)buffer;
    (void)timeout_ms;
    return false;
}

std::size_t Stm32G4Uart::available() const
{
    return 0U;
}

void Stm32G4Uart::flush()
{
    if (handle != nullptr)
    {
        UART_HandleTypeDef* const uart = static_cast<UART_HandleTypeDef*>(handle);
        const uint32_t start = HAL_GetTick();
        while (__HAL_UART_GET_FLAG(uart, UART_FLAG_TC) == RESET &&
               (HAL_GetTick() - start) < MaxOperationTimeoutMs)
        {
        }
    }
}

void Stm32G4Uart::setBaudRate(uint32_t baudRate)
{
    if (handle != nullptr)
    {
        UART_HandleTypeDef* const uart = static_cast<UART_HandleTypeDef*>(handle);
        uart->Init.BaudRate = baudRate;
        (void)HAL_UART_Init(uart);
    }
}

} /* namespace bsp */
