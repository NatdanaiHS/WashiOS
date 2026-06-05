#pragma once

#include <cstddef>
#include <cstdint>

#include "IUart.hpp"

namespace bsp::rp2040
{

class UartDriver final : public hal::IUart
{
public:
    UartDriver();

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
    uint32_t baud;
};

} /* namespace bsp::rp2040 */
