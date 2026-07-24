#pragma once

#include <cstddef>
#include <cstdint>

#include "IUart.hpp"

namespace bsp
{

class Stm32G4Uart final : public hal::IUart
{
public:
    explicit Stm32G4Uart(void* uartHandle);

    bool writeBuffer(const uint8_t* data,
                     std::size_t length,
                     uint32_t timeout_ms) noexcept override;
    bool readBuffer(uint8_t* buffer,
                    std::size_t length,
                    uint32_t timeout_ms) noexcept override;
    std::size_t available() const noexcept override;
    void flush() noexcept override;
    void setBaudRate(uint32_t baudRate) noexcept override;

    bool enableInterruptReceive() noexcept;
    void handleInterrupt() noexcept;

private:
    static constexpr uint32_t MaxOperationTimeoutMs = 10U;
    static constexpr std::size_t ReceiveBufferCapacity = 128U;

    static uint32_t boundedTimeout(uint32_t timeoutMs);

    bool readBuffered(uint8_t* buffer,
                      std::size_t length,
                      uint32_t timeoutMs) noexcept;

    void* handle;
    uint8_t receiveBuffer[ReceiveBufferCapacity] = {};
    volatile std::size_t receiveHead = 0U;
    volatile std::size_t receiveTail = 0U;
    bool interruptReceiveEnabled = false;
};

} /* namespace bsp */
