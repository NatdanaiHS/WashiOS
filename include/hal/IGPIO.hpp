#pragma once

namespace hal
{

/**
 * @brief Edge selection for hardware-neutral GPIO interrupt registration.
 */
enum class GpioInterruptEdge
{
    Rising,
    Falling,
    Both
};

/**
 * @brief Allocation-free GPIO interrupt callback signature.
 *
 * The callback receives an opaque user context pointer supplied during
 * registration. Implementations shall invoke it from the target-appropriate
 * interrupt or deferred-interrupt context without allocating memory or
 * throwing exceptions.
 */
using GpioInterruptCallback = void (*)(void* context) noexcept;

/**
 * @brief Abstract interface for a General Purpose Input/Output pin.
 *
 * The IGPIO interface defines deterministic operations for controlling and
 * reading a single digital hardware pin. Implementations shall provide the
 * platform-specific register access while preserving the no-allocation and
 * no-exception contract required by the hardware abstraction layer.
 */
class IGPIO
{
public:
    /**
     * @brief Default virtual destructor for safe destruction through interface pointers.
     */
    virtual ~IGPIO() noexcept = default;

    /**
     * @brief Set the physical pin output state to logic HIGH.
     *
     * Implementations shall drive the associated pin to the electrical level
     * defined as logic HIGH for the target hardware.
     */
    virtual void setHigh() noexcept = 0;

    /**
     * @brief Set the physical pin output state to logic LOW.
     *
     * Implementations shall drive the associated pin to the electrical level
     * defined as logic LOW for the target hardware.
     */
    virtual void setLow() noexcept = 0;

    /**
     * @brief Invert the current physical output state of the pin.
     *
     * Implementations shall toggle the output latch or equivalent hardware
     * state associated with the pin.
     */
    virtual void toggle() noexcept = 0;

    /**
     * @brief Read the current physical state of the pin.
     *
     * @return true if the pin is currently at logic HIGH; false if the pin is
     *         currently at logic LOW.
     */
    virtual bool read() const noexcept = 0;

    /**
     * @brief Register an interrupt callback for a selected pin edge.
     *
     * Implementations shall configure the platform-specific interrupt source
     * without exposing chip registers or vendor HAL types through this
     * interface. Passing a null callback shall fail and leave any existing
     * registration unchanged.
     *
     * @param edge Edge transition that shall trigger the callback.
     * @param callback Function pointer invoked when the edge is observed.
     * @param context Opaque user pointer passed back to the callback.
     *
     * @return true if the interrupt registration was accepted; false otherwise.
     */
    virtual bool setInterrupt(GpioInterruptEdge edge,
                              GpioInterruptCallback callback,
                              void* context) noexcept = 0;

    /**
     * @brief Clear the currently registered interrupt callback.
     */
    virtual void clearInterrupt() noexcept = 0;
};

} /* namespace hal */
