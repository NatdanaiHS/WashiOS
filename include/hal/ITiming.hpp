#pragma once

#include <cstdint>

namespace hal
{

/**
 * @brief Abstract interface for system timing and deterministic delays.
 *
 * The ITiming interface defines platform-independent access to mission uptime
 * and blocking delay services. Implementations shall provide the underlying
 * hardware or operating environment timing source while preserving the
 * no-allocation and no-exception contract required by the hardware abstraction
 * layer.
 */
class ITiming
{
public:
    /**
     * @brief Default virtual destructor for safe destruction through interface pointers.
     */
    virtual ~ITiming() noexcept = default;

    /**
     * @brief Get the current system uptime in milliseconds.
     *
     * The returned value shall be monotonic for the duration supported by the
     * platform timing implementation.
     *
     * @return Current system uptime in milliseconds.
     */
    virtual uint64_t getSystemTick() const noexcept = 0;

    /**
     * @brief Block execution for a specified number of milliseconds.
     *
     * Implementations shall provide deterministic delay behavior appropriate
     * for the target platform.
     *
     * @param ms Delay duration in milliseconds.
     */
    virtual void delayMs(uint32_t ms) noexcept = 0;

    /**
     * @brief Block execution for a specified number of microseconds.
     *
     * Implementations shall provide deterministic delay behavior appropriate
     * for the target platform.
     *
     * @param us Delay duration in microseconds.
     */
    virtual void delayUs(uint32_t us) noexcept = 0;
};

} /* namespace hal */
