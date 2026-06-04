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
                     uint32_t timeout_ms) override;
    bool readBuffer(uint8_t* buffer,
                    std::size_t length,
                    uint32_t timeout_ms) override;
    std::size_t available() const override;
    void flush() override;
    void setBaudRate(uint32_t baudRate) override;

private:
    void* handle;
};

} /* namespace bsp */
