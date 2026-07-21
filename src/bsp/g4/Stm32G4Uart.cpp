#include "bsp/g4/Stm32G4Uart.hpp"

#include "stm32g4xx_hal.h"

namespace
{

constexpr std::size_t MaxHalTransferLength = 0xFFFFU;
bsp::Stm32G4Uart* usart1Owner = nullptr;

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
                              uint32_t timeout_ms) noexcept
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
                             uint32_t timeout_ms) noexcept
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

    if (interruptReceiveEnabled)
    {
        return readBuffered(buffer, length, timeout_ms);
    }

    UART_HandleTypeDef* const uart = static_cast<UART_HandleTypeDef*>(handle);
    if (uart->RxState != HAL_UART_STATE_READY)
    {
        return false;
    }

    return HAL_UART_Receive(uart,
                            buffer,
                            static_cast<uint16_t>(length),
                            boundedTimeout(timeout_ms)) == HAL_OK;
}

std::size_t Stm32G4Uart::available() const noexcept
{
    if (interruptReceiveEnabled)
    {
        const std::size_t head = receiveHead;
        const std::size_t tail = receiveTail;
        return (head >= tail) ? (head - tail) :
                               (ReceiveBufferCapacity - tail + head);
    }

#if defined(UART_FLAG_RXNE_RXFNE)
    constexpr uint32_t ReceiveDataReadyFlag = UART_FLAG_RXNE_RXFNE;
#elif defined(UART_FLAG_RXNE)
    constexpr uint32_t ReceiveDataReadyFlag = UART_FLAG_RXNE;
#else
    constexpr uint32_t ReceiveDataReadyFlag = 0U;
#endif

    if (handle != nullptr && ReceiveDataReadyFlag != 0U)
    {
        UART_HandleTypeDef* const uart = static_cast<UART_HandleTypeDef*>(handle);
        return (__HAL_UART_GET_FLAG(uart, ReceiveDataReadyFlag) != RESET) ? 1U : 0U;
    }

    return 0U;
}

void Stm32G4Uart::flush() noexcept
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

void Stm32G4Uart::setBaudRate(uint32_t baudRate) noexcept
{
    if (handle != nullptr)
    {
        UART_HandleTypeDef* const uart = static_cast<UART_HandleTypeDef*>(handle);
        uart->Init.BaudRate = baudRate;
        (void)HAL_UART_Init(uart);
    }
}

bool Stm32G4Uart::enableInterruptReceive() noexcept
{
    if (handle == nullptr)
    {
        return false;
    }

    UART_HandleTypeDef* const uart = static_cast<UART_HandleTypeDef*>(handle);
    if (uart->Instance != USART1 || usart1Owner != nullptr)
    {
        return false;
    }

    receiveHead = 0U;
    receiveTail = 0U;
    usart1Owner = this;
    interruptReceiveEnabled = true;

    __HAL_UART_CLEAR_OREFLAG(uart);
    __HAL_UART_CLEAR_FEFLAG(uart);
    __HAL_UART_CLEAR_NEFLAG(uart);
    __HAL_UART_ENABLE_IT(uart, UART_IT_RXNE);
    __HAL_UART_ENABLE_IT(uart, UART_IT_ERR);
    HAL_NVIC_SetPriority(USART1_IRQn, 6U, 0U);
    HAL_NVIC_EnableIRQ(USART1_IRQn);
    return true;
}

void Stm32G4Uart::handleInterrupt() noexcept
{
    UART_HandleTypeDef* const uart = static_cast<UART_HandleTypeDef*>(handle);
    const uint32_t status = uart->Instance->ISR;

    if ((status & USART_ISR_RXNE_RXFNE) != 0U)
    {
        const uint8_t byte = static_cast<uint8_t>(uart->Instance->RDR);
        const std::size_t next = (receiveHead + 1U) % ReceiveBufferCapacity;
        if (next != receiveTail)
        {
            receiveBuffer[receiveHead] = byte;
            receiveHead = next;
        }
    }

    const uint32_t errors = status & (USART_ISR_ORE | USART_ISR_FE | USART_ISR_NE);
    if (errors != 0U)
    {
        uart->Instance->ICR = USART_ICR_ORECF | USART_ICR_FECF | USART_ICR_NECF;
    }
}

bool Stm32G4Uart::readBuffered(uint8_t* buffer,
                               std::size_t length,
                               uint32_t timeoutMs) noexcept
{
    const uint32_t start = HAL_GetTick();
    std::size_t count = 0U;
    while (count < length)
    {
        if (receiveTail != receiveHead)
        {
            buffer[count++] = receiveBuffer[receiveTail];
            receiveTail = (receiveTail + 1U) % ReceiveBufferCapacity;
        }
        else if (static_cast<uint32_t>(HAL_GetTick() - start) >= boundedTimeout(timeoutMs))
        {
            return false;
        }
    }
    return true;
}

} /* namespace bsp */

extern "C" void USART1_IRQHandler()
{
    if (usart1Owner != nullptr)
    {
        usart1Owner->handleInterrupt();
    }
}
