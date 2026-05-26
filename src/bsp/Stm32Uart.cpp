#include "bsp/Stm32Uart.hpp"

#include "stm32f4xx_hal.h"

namespace bsp
{

Stm32Uart::Stm32Uart(void* uartHandle)
    : handle(uartHandle)
{
}

bool Stm32Uart::writeBuffer(const uint8_t* data,
                            std::size_t length,
                            uint32_t timeout_ms)
{
    if ((data == nullptr && length > 0U) || handle == nullptr)
    {
        return false;
    }

    if (length == 0U)
    {
        return true;
    }

    return HAL_UART_Transmit(static_cast<UART_HandleTypeDef*>(handle),
                             const_cast<uint8_t*>(data),
                             static_cast<uint16_t>(length),
                             timeout_ms) == HAL_OK;
}

bool Stm32Uart::readBuffer(uint8_t* buffer,
                           std::size_t length,
                           uint32_t timeout_ms)
{
    if ((buffer == nullptr && length > 0U) || handle == nullptr)
    {
        return false;
    }

    if (length == 0U)
    {
        return true;
    }

    return HAL_UART_Receive(static_cast<UART_HandleTypeDef*>(handle),
                            buffer,
                            static_cast<uint16_t>(length),
                            timeout_ms) == HAL_OK;
}

std::size_t Stm32Uart::available() const
{
    return 0U;
}

void Stm32Uart::flush()
{
    if (handle != nullptr)
    {
        while (__HAL_UART_GET_FLAG(static_cast<UART_HandleTypeDef*>(handle), UART_FLAG_TC) == RESET)
        {
        }
    }
}

void Stm32Uart::setBaudRate(uint32_t baudRate)
{
    if (handle != nullptr)
    {
        UART_HandleTypeDef* const uart = static_cast<UART_HandleTypeDef*>(handle);
        uart->Init.BaudRate = baudRate;
        (void)HAL_UART_Init(uart);
    }
}

} /* namespace bsp */
