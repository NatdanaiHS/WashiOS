#pragma once

#include <cstdint>

namespace hal
{

/**
 * @brief ADC conversion status for diagnostics and mock simulation.
 */
enum class AdcStatus
{
    Ready,
    Busy,
    Error
};

/**
 * @brief Abstract interface for an Analog-to-Digital Converter.
 *
 * The IAdc interface defines deterministic, timeout-bounded conversion
 * operations for reading analog input channels. Implementations shall provide
 * platform-specific ADC access while preserving the no-allocation and
 * no-exception contract required by the hardware abstraction layer.
 */
class IAdc
{
public:
    /**
     * @brief Default virtual destructor for safe destruction through interface pointers.
     */
    virtual ~IAdc() noexcept = default;

    /**
     * @brief Read a raw digital conversion value from an ADC channel.
     *
     * The operation shall initiate a conversion and complete before the
     * specified timeout expires. Implementations shall return false if the
     * conversion cannot be completed or if the timeout is reached.
     *
     * @param channelId Platform-defined ADC channel identifier.
     * @param outRawValue Destination for the raw digital conversion value.
     * @param timeout_ms Maximum conversion duration in milliseconds.
     *
     * @return true if the conversion completed successfully; false otherwise.
     */
    virtual bool readRaw(uint8_t channelId,
                         uint16_t& outRawValue,
                         uint32_t timeout_ms) noexcept = 0;

    /**
     * @brief Read a scaled voltage value from an ADC channel.
     *
     * The operation shall initiate a conversion and complete before the
     * specified timeout expires. Implementations shall return false if the
     * conversion cannot be completed or if the timeout is reached.
     *
     * @param channelId Platform-defined ADC channel identifier.
     * @param outVoltage Destination for the scaled voltage value.
     * @param timeout_ms Maximum conversion duration in milliseconds.
     *
     * @return true if the conversion completed successfully; false otherwise.
     */
    virtual bool readVoltage(uint8_t channelId,
                             float& outVoltage,
                             uint32_t timeout_ms) noexcept = 0;

    /**
     * @brief Configure the ADC conversion resolution.
     *
     * Implementations shall configure the requested resolution when supported
     * by the target hardware.
     *
     * @param bits Requested ADC resolution in bits.
     *
     * @return true if the resolution was accepted; false otherwise.
     */
    virtual bool setResolution(uint8_t bits) noexcept = 0;

    /**
     * @brief Get the current ADC status without allocating memory.
     *
     * @return Current hardware-neutral ADC status.
     */
    virtual AdcStatus getStatus() const noexcept = 0;
};

} /* namespace hal */
