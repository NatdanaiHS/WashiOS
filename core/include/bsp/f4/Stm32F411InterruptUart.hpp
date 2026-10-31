#pragma once

#include <cstddef>
#include <cstdint>

#include "IUart.hpp"
#include "bsp/f4/F411RxRing.hpp"
#include "stm32f4xx_hal.h"

namespace bsp
{

class Stm32F411InterruptUart final : public hal::IUart
{
public:
    explicit Stm32F411InterruptUart(void* uartHandle) noexcept
        : handle(static_cast<UART_HandleTypeDef*>(uartHandle))
    {
    }

    bool writeBuffer(const uint8_t* data,
                     std::size_t length,
                     uint32_t timeoutMs) noexcept override
    {
        if ((data == nullptr && length > 0U) || handle == nullptr ||
            length > 0xFFFFU)
        {
            return false;
        }
        if (length == 0U)
        {
            return true;
        }
        return HAL_UART_Transmit(handle, const_cast<uint8_t*>(data),
                                 static_cast<uint16_t>(length),
                                 boundedTimeout(timeoutMs)) == HAL_OK;
    }

    bool readBuffer(uint8_t* buffer,
                    std::size_t length,
                    uint32_t timeoutMs) noexcept override
    {
        (void)timeoutMs;
        if ((buffer == nullptr && length > 0U) || handle == nullptr)
        {
            return false;
        }
        for (std::size_t index = 0U; index < length; ++index)
        {
            if (!receiveRing.pop(buffer[index]))
            {
                return false;
            }
        }
        return true;
    }

    std::size_t available() const noexcept override
    {
        return receiveRing.available();
    }

    void flush() noexcept override
    {
        if (handle == nullptr)
        {
            return;
        }
        const uint32_t start = HAL_GetTick();
        while (__HAL_UART_GET_FLAG(handle, UART_FLAG_TC) == RESET &&
               static_cast<uint32_t>(HAL_GetTick() - start) < MaxOperationTimeoutMs)
        {
        }
    }

    void setBaudRate(uint32_t baudRate) noexcept override
    {
        if (handle != nullptr)
        {
            handle->Init.BaudRate = baudRate;
            (void)HAL_UART_Init(handle);
        }
    }

    bool enableInterruptReceive() noexcept
    {
        if (handle == nullptr ||
            (handle->Instance != USART1 && handle->Instance != USART2))
        {
            return false;
        }
        receiveRing.clear();
        __HAL_UART_CLEAR_OREFLAG(handle);
        __HAL_UART_CLEAR_FEFLAG(handle);
        __HAL_UART_CLEAR_NEFLAG(handle);
        __HAL_UART_ENABLE_IT(handle, UART_IT_RXNE);
        __HAL_UART_ENABLE_IT(handle, UART_IT_ERR);
        return true;
    }

    void handleInterrupt() noexcept
    {
        if (handle == nullptr)
        {
            return;
        }
        USART_TypeDef* const instance = handle->Instance;
        for (;;)
        {
            const uint32_t status = instance->SR;
            const bool hasData = (status & USART_SR_RXNE) != 0U;
            const bool hasError =
                (status & (USART_SR_ORE | USART_SR_FE | USART_SR_NE)) != 0U;
            if (!hasData && !hasError)
            {
                break;
            }

            /* On STM32F4, reading SR followed by DR clears RXNE and the
               ORE/FE/NE error condition. Preserve the byte when RXNE is set. */
            const uint8_t byte = static_cast<uint8_t>(instance->DR);
            if (hasError)
            {
                receiveRing.noteHardwareError();
            }
            if (hasData)
            {
                (void)receiveRing.pushFromInterrupt(byte);
            }
        }
    }

    uint32_t overflowCount() const noexcept
    {
        return receiveRing.overflowCount();
    }

    uint32_t hardwareErrorCount() const noexcept
    {
        return receiveRing.hardwareErrorCount();
    }

private:
    static constexpr uint32_t MaxOperationTimeoutMs = 10U;
    static constexpr std::size_t ReceiveBufferCapacity = 128U;

    static uint32_t boundedTimeout(uint32_t timeoutMs) noexcept
    {
        return (timeoutMs < MaxOperationTimeoutMs) ? timeoutMs : MaxOperationTimeoutMs;
    }

    UART_HandleTypeDef* handle;
    F411RxRing<ReceiveBufferCapacity> receiveRing;
};

} /* namespace bsp */
