#pragma once

#include <cstddef>
#include <cstdint>

namespace hal
{

/**
 * @brief Operational state reported by an I2C bus implementation.
 *
 * The state value shall be derived from statically owned driver state and shall
 * not require dynamic memory allocation, exceptions, or blocking bus activity
 * to evaluate.
 */
enum class I2cBusState
{
    /** @brief The bus driver has not completed platform initialization. */
    Uninitialized,

    /** @brief The bus is initialized and available for transactions. */
    Ready,

    /** @brief The bus driver detected a recoverable or unrecoverable error. */
    Error,

    /** @brief The bus is locked, held busy, or requires recovery before use. */
    BusLocked
};

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
    virtual ~II2cBus() noexcept = default;

    /**
     * @brief Return the current operational state of the I2C bus.
     *
     * Implementations shall report the state without allocating memory,
     * throwing exceptions, or initiating a bus transaction. The returned value
     * is intended for diagnostics, health monitoring, and recovery decisions.
     *
     * @return Current I2C bus state.
     */
    virtual I2cBusState getState() const noexcept = 0;

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
                       uint32_t timeout_ms) noexcept = 0;

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
                      uint32_t timeout_ms) noexcept = 0;

    /**
     * @brief Perform an atomic write followed by a read using a repeated start.
     *
     * Implementations shall execute the write phase and read phase as one
     * indivisible bus transaction where supported by the platform driver. The
     * transaction shall preserve bus ownership between phases, issue a repeated
     * start condition instead of releasing the bus, and prevent interference
     * from other FreeRTOS tasks until the read phase has completed or failed.
     *
     * @param address I2C device address. Both 7-bit and 10-bit addresses are supported.
     * @param txData Pointer to the byte sequence to transmit before the repeated start.
     * @param txLength Number of bytes to transmit before the repeated start.
     * @param rxBuffer Pointer to the destination buffer for received bytes.
     * @param rxLength Number of bytes to receive after the repeated start.
     * @param timeout_ms Maximum total transaction duration in milliseconds.
     *
     * @return true if the combined transaction completed successfully; false otherwise.
     */
    virtual bool writeRead(uint16_t address,
                           const uint8_t* txData,
                           std::size_t txLength,
                           uint8_t* rxBuffer,
                           std::size_t rxLength,
                           uint32_t timeout_ms) noexcept = 0;

    /**
     * @brief Attempt to recover a faulted I2C bus.
     *
     * Implementations shall provide the platform-specific recovery sequence,
     * such as manually toggling the SCL line to release a slave device that is
     * holding SDA low after a fault or Single Event Upset.
     */
    virtual void resetBus() noexcept = 0;
};

} /* namespace hal */
