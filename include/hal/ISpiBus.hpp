#pragma once

#include <cstddef>
#include <cstdint>

namespace hal
{

/**
 * @brief Abstract interface for a Serial Peripheral Interface bus.
 *
 * The ISpiBus interface defines deterministic, timeout-bounded transactions
 * for communicating with devices on an SPI bus. Implementations shall provide
 * platform-specific bus access while preserving the no-allocation and
 * no-exception contract required by the hardware abstraction layer.
 */
class ISpiBus
{
public:
    /**
     * @brief Default virtual destructor for safe destruction through interface pointers.
     */
    virtual ~ISpiBus() = default;

    /**
     * @brief Perform a full-duplex SPI data transaction.
     *
     * The transaction shall transmit and receive data simultaneously for the
     * specified number of bytes. The transmit pointer may be null when only
     * receiving data is required. The receive pointer may be null when only
     * transmitting data is required.
     *
     * @param txData Pointer to the bytes to transmit, or null for receive-only transfers.
     * @param rxData Pointer to the receive buffer, or null for transmit-only transfers.
     * @param length Number of bytes to transfer.
     * @param timeout_ms Maximum transaction duration in milliseconds.
     *
     * @return true if the transfer completed successfully; false otherwise.
     */
    virtual bool transfer(const uint8_t* txData,
                          uint8_t* rxData,
                          std::size_t length,
                          uint32_t timeout_ms) = 0;

    /**
     * @brief Configure the SPI bus clock frequency.
     *
     * Implementations shall configure the nearest supported clock frequency
     * that does not violate the target hardware limits.
     *
     * @param hz Requested SPI clock frequency in hertz.
     */
    virtual void setFrequency(uint32_t hz) = 0;

    /**
     * @brief Activate the chip select signal for a device on the SPI bus.
     *
     * @param csPinId Platform-defined chip select identifier.
     */
    virtual void selectChip(uint8_t csPinId) = 0;

    /**
     * @brief Deactivate the chip select signal for a device on the SPI bus.
     *
     * @param csPinId Platform-defined chip select identifier.
     */
    virtual void deselectChip(uint8_t csPinId) = 0;
};

} /* namespace hal */
