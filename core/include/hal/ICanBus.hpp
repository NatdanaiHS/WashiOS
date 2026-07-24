#pragma once

#include <cstdint>

namespace hal
{

/**
 * @brief Fixed-size Controller Area Network frame representation.
 *
 * The CanFrame structure stores the identifier, payload length, and payload
 * bytes for a classical CAN frame without dynamic memory allocation.
 */
struct CanFrame
{
    /**
     * @brief Standard 11-bit or extended 29-bit CAN message identifier.
     */
    uint32_t messageId;

    /**
     * @brief Number of valid bytes in the data payload.
     *
     * Classical CAN frames support payload lengths from 0 to 8 bytes.
     */
    uint8_t dataLength;

    /**
     * @brief Static payload storage for classical CAN data bytes.
     */
    uint8_t data[8];
};

/**
 * @brief Hardware-neutral CAN controller state.
 */
enum class CanBusState
{
    Uninitialized,
    Ready,
    Error,
    BusOff
};

/**
 * @brief Abstract interface for a Controller Area Network bus.
 *
 * The ICanBus interface defines deterministic, timeout-bounded operations for
 * CAN communication. Implementations shall provide platform-specific CAN
 * controller access while preserving the no-allocation and no-exception
 * contract required by the hardware abstraction layer.
 */
class ICanBus
{
public:
    /**
     * @brief Default virtual destructor for safe destruction through interface pointers.
     */
    virtual ~ICanBus() noexcept = default;

    /**
     * @brief Initialize the CAN controller at the specified communication speed.
     *
     * @param baudRate Requested CAN bus baud rate in bits per second.
     *
     * @return true if initialization completed successfully; false otherwise.
     */
    virtual bool begin(uint32_t baudRate) noexcept = 0;

    /**
     * @brief Transmit a CAN frame.
     *
     * The operation shall complete before the specified timeout expires.
     * Implementations shall return false if the frame cannot be transmitted or
     * if the timeout is reached.
     *
     * @param frame CAN frame to transmit.
     * @param timeout_ms Maximum operation duration in milliseconds.
     *
     * @return true if the frame was transmitted successfully; false otherwise.
     */
    virtual bool transmit(const CanFrame& frame, uint32_t timeout_ms) noexcept = 0;

    /**
     * @brief Receive a CAN frame.
     *
     * The operation shall complete before the specified timeout expires.
     * Implementations shall return false if no frame is received or if the
     * timeout is reached.
     *
     * @param frame Destination structure for the received CAN frame.
     * @param timeout_ms Maximum operation duration in milliseconds.
     *
     * @return true if a frame was received successfully; false otherwise.
     */
    virtual bool receive(CanFrame& frame, uint32_t timeout_ms) noexcept = 0;

    /**
     * @brief Configure a CAN hardware acceptance filter.
     *
     * Acceptance filters reduce processor load by allowing only selected CAN
     * identifiers through the controller receive path.
     *
     * @param targetMessageId Target CAN message identifier for the filter.
     * @param mask Identifier mask used by the hardware acceptance filter.
     *
     * @return true if the filter was configured successfully; false otherwise.
     */
    virtual bool setFilter(uint32_t targetMessageId, uint32_t mask) noexcept = 0;

    /**
     * @brief Get the current controller state without allocating memory.
     *
     * @return Current hardware-neutral CAN bus state.
     */
    virtual CanBusState getState() const noexcept = 0;

    /**
     * @brief Trigger CAN bus fault recovery.
     *
     * Implementations shall start the platform-specific recovery sequence when
     * the CAN controller enters a bus-off or equivalent fault state due to a
     * Single Event Upset or electrical interference.
     */
    virtual void recoverBus() noexcept = 0;
};

} /* namespace hal */
