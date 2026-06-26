#pragma once

#include <cstddef>
#include <cstdint>

#include "IUart.hpp"

namespace bsp
{

class Stm32Uart final : public hal::IUart
{
public:
    explicit Stm32Uart(void* uartHandle);

    bool writeBuffer(const uint8_t* data,
                     std::size_t length,
                     uint32_t timeout_ms) noexcept override;
    bool readBuffer(uint8_t* buffer,
                    std::size_t length,
                    uint32_t timeout_ms) noexcept override;
    std::size_t available() const noexcept override;
    void flush() noexcept override;
    void setBaudRate(uint32_t baudRate) noexcept override;

private:
    void* handle;
};

} /* namespace bsp */
