#pragma once

#include <cstddef>
#include <cstdint>

namespace hal
{

/**
 * @brief Abstract interface for a Universal Asynchronous Receiver-Transmitter.
 *
 * The IUart interface defines deterministic, timeout-bounded operations for
 * serial byte communication. Implementations shall provide platform-specific
 * UART access while preserving the no-allocation and no-exception contract
 * required by the hardware abstraction layer.
 */
class IUart
{
public:
    /**
     * @brief Default virtual destructor for safe destruction through interface pointers.
     */
    virtual ~IUart() = default;

    /**
     * @brief Transmit a sequence of bytes over the UART interface.
     *
     * The operation shall complete before the specified timeout expires.
     * Implementations shall return false if the data cannot be transmitted
     * completely or if the timeout is reached.
     *
     * @param data Pointer to the byte sequence to transmit.
     * @param length Number of bytes to transmit.
     * @param timeout_ms Maximum operation duration in milliseconds.
     *
     * @return true if all bytes were transmitted successfully; false otherwise.
     */
    virtual bool writeBuffer(const uint8_t* data,
                             std::size_t length,
                             uint32_t timeout_ms) = 0;

    /**
     * @brief Receive a specific number of bytes from the UART interface.
     *
     * The operation shall complete before the specified timeout expires.
     * Implementations shall return false if the requested number of bytes
     * cannot be received or if the timeout is reached.
     *
     * @param buffer Pointer to the destination buffer for received bytes.
     * @param length Number of bytes to receive.
     * @param timeout_ms Maximum operation duration in milliseconds.
     *
     * @return true if all requested bytes were received successfully; false otherwise.
     */
    virtual bool readBuffer(uint8_t* buffer,
                            std::size_t length,
                            uint32_t timeout_ms) = 0;

    /**
     * @brief Get the number of bytes currently available for reading.
     *
     * @return Number of received bytes waiting in the hardware or software buffer.
     */
    virtual std::size_t available() const = 0;

    /**
     * @brief Flush the UART interface.
     *
     * Implementations shall discard unread receive data and wait for any
     * ongoing transmission to complete.
     */
    virtual void flush() = 0;

    /**
     * @brief Configure the UART communication speed.
     *
     * @param baudRate Requested baud rate in bits per second.
     */
    virtual void setBaudRate(uint32_t baudRate) = 0;
};

} /* namespace hal */
