#pragma once

namespace hal
{

/**
 * @brief Abstract interface for watchdog refresh control.
 *
 * The IWatchdog interface defines the minimal platform-independent contract
 * for servicing a target-specific watchdog timer. Implementations shall write
 * directly to the required hardware registers while preserving the absolute
 * no-allocation and no-exception contract required by the hardware abstraction
 * layer.
 */
class IWatchdog
{
public:
    /**
     * @brief Default virtual destructor for safe destruction through interface pointers.
     */
    virtual ~IWatchdog() noexcept = default;

    /**
     * @brief Refresh the watchdog down-counter.
     *
     * Implementations shall perform the target-specific register write sequence
     * required to pet the watchdog without allocating memory or throwing
     * exceptions.
     */
    virtual void kick() noexcept = 0;
};

} /* namespace hal */
