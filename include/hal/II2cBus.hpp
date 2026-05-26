#pragma once

#include <cstddef>
#include <cstdint>

namespace hal
{

/**
 * @brief Abstract interface for an Inter-Integrated Circuit bus.
 *
 * The II2cBus interface defines deterministic, timeout-bounded transactions
 * for communicating with devices on an I2C bus. Implementations shall provide
 * platform-specific bus access while preserving the no-allocation and
 * no-exception contract required by the hardware abstraction layer.
 */
class II2cBus
{
public:
    /**
     * @brief Default virtual destructor for safe destruction through interface pointers.
     */
    virtual ~II2cBus() = default;

    /**
     * @brief Write a sequence of bytes to an I2C device address.
     *
     * The transaction shall complete before the specified timeout expires.
     * Implementations shall return false if the transaction cannot be completed,
     * if the addressed device does not acknowledge, or if the timeout is reached.
     *
     * @param address I2C device address. Both 7-bit and 10-bit addresses are supported.
     * @param data Pointer to the byte sequence to transmit.
     * @param length Number of bytes to transmit.
     * @param timeout_ms Maximum transaction duration in milliseconds.
     *
     * @return true if the write transaction completed successfully; false otherwise.
     */
    virtual bool write(uint16_t address,
                       const uint8_t* data,
                       std::size_t length,
                       uint32_t timeout_ms) = 0;

    /**
     * @brief Read a sequence of bytes from an I2C device address.
     *
     * The transaction shall complete before the specified timeout expires.
     * Implementations shall return false if the transaction cannot be completed,
     * if the addressed device does not acknowledge, or if the timeout is reached.
     *
     * @param address I2C device address. Both 7-bit and 10-bit addresses are supported.
     * @param buffer Pointer to the destination buffer for received bytes.
     * @param length Number of bytes to receive.
     * @param timeout_ms Maximum transaction duration in milliseconds.
     *
     * @return true if the read transaction completed successfully; false otherwise.
     */
    virtual bool read(uint16_t address,
                      uint8_t* buffer,
                      std::size_t length,
                      uint32_t timeout_ms) = 0;

    /**
     * @brief Attempt to recover a faulted I2C bus.
     *
     * Implementations shall provide the platform-specific recovery sequence,
     * such as manually toggling the SCL line to release a slave device that is
     * holding SDA low after a fault or Single Event Upset.
     */
    virtual void resetBus() = 0;
};

} /* namespace hal */
