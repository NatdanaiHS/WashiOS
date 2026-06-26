#pragma once

#include <cstddef>
#include <cstdint>

namespace hal
{

/**
 * @brief Operational state reported by a flash memory implementation.
 *
 * The state value shall be derived from statically owned driver state and shall
 * not require dynamic memory allocation, exceptions, or flash peripheral
 * activity to evaluate.
 */
enum class FlashState
{
    /** @brief The flash driver has not completed platform initialization. */
    Uninitialized,

    /** @brief The flash peripheral is initialized and available for operations. */
    Ready,

    /** @brief The flash driver detected an error or unrecoverable fault. */
    Error,

    /** @brief A flash programming operation is currently in progress. */
    Writing,

    /** @brief A flash erase operation is currently in progress. */
    Erasing
};

/**
 * @brief Abstract interface for deterministic flash memory access.
 *
 * The IFlash interface defines platform-independent read, write, and sector
 * erase operations for non-volatile memory. Implementations shall provide the
 * target-specific register sequences while preserving the absolute
 * no-allocation and no-exception contract required by the hardware abstraction
 * layer.
 */
class IFlash
{
public:
    /**
     * @brief Default virtual destructor for safe destruction through interface pointers.
     */
    virtual ~IFlash() noexcept = default;

    /**
     * @brief Return the current operational state of the flash driver.
     *
     * Implementations shall report the state without allocating memory,
     * throwing exceptions, or initiating a flash memory operation.
     *
     * @return Current flash driver state.
     */
    virtual FlashState getState() const noexcept = 0;

    /**
     * @brief Read bytes from a physical flash memory address.
     *
     * Implementations shall copy up to the requested number of bytes from the
     * specified physical address into the caller-provided destination buffer.
     *
     * @param address Physical flash memory address to read from.
     * @param destination Destination byte buffer provided by the caller.
     * @param length Number of bytes to read.
     *
     * @return true if the read completed successfully; false otherwise.
     */
    virtual bool read(uint32_t address,
                      uint8_t* destination,
                      std::size_t length) noexcept = 0;

    /**
     * @brief Program bytes to a physical flash memory address.
     *
     * Implementations shall perform the target-specific programming sequence
     * for the supplied source data and shall not allocate memory or throw
     * exceptions during the operation.
     *
     * @param address Physical flash memory address to program.
     * @param source Source byte array provided by the caller.
     * @param length Number of bytes to program.
     *
     * @return true if the write completed successfully; false otherwise.
     */
    virtual bool write(uint32_t address,
                       const uint8_t* source,
                       std::size_t length) noexcept = 0;

    /**
     * @brief Erase a flash sector at a sector boundary address.
     *
     * Implementations shall erase the sector identified by the supplied
     * physical sector boundary address using the target-specific erase
     * sequence.
     *
     * @param sectorAddress Physical address aligned to a sector memory boundary.
     *
     * @return true if the sector erase completed successfully; false otherwise.
     */
    virtual bool eraseSector(uint32_t sectorAddress) noexcept = 0;
};

} /* namespace hal */
