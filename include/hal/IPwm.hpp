#pragma once

#include <cstdint>

namespace hal
{

/**
 * @brief Snapshot of a PWM channel configuration.
 */
struct PwmChannelState
{
    uint32_t frequencyHz;
    float dutyCyclePercentage;
    bool enabled;
};

/**
 * @brief Abstract interface for Pulse Width Modulation output control.
 *
 * The IPwm interface defines deterministic operations for configuring and
 * controlling PWM output channels. Implementations shall provide
 * platform-specific PWM access while preserving the no-allocation and
 * no-exception contract required by the hardware abstraction layer.
 */
class IPwm
{
public:
    /**
     * @brief Default virtual destructor for safe destruction through interface pointers.
     */
    virtual ~IPwm() = default;

    /**
     * @brief Configure the base frequency of a PWM output channel.
     *
     * Implementations shall apply the requested frequency when it is supported
     * by the target hardware.
     *
     * @param channelId Platform-defined PWM channel identifier.
     * @param hz Requested PWM frequency in hertz.
     *
     * @return true if the requested frequency was supported and applied; false otherwise.
     */
    virtual bool setFrequency(uint8_t channelId, uint32_t hz) = 0;

    /**
     * @brief Configure the active duty cycle of a PWM output channel.
     *
     * Implementations shall validate or safely clamp the duty cycle percentage
     * to the supported range of 0.0 to 100.0 before applying it.
     *
     * @param channelId Platform-defined PWM channel identifier.
     * @param percentage Requested active duty cycle percentage.
     *
     * @return true if the duty cycle value was valid and applied; false otherwise.
     */
    virtual bool setDutyCycle(uint8_t channelId, float percentage) = 0;

    /**
     * @brief Enable PWM output on the specified channel.
     *
     * @param channelId Platform-defined PWM channel identifier.
     */
    virtual void start(uint8_t channelId) = 0;

    /**
     * @brief Disable PWM output on the specified channel.
     *
     * Implementations shall drive the associated output to a safe default
     * state, normally logic LOW, when the PWM channel is stopped.
     *
     * @param channelId Platform-defined PWM channel identifier.
     */
    virtual void stop(uint8_t channelId) = 0;

    /**
     * @brief Read back the current state of a PWM output channel.
     *
     * @param channelId Platform-defined PWM channel identifier.
     * @param outState Destination for the channel state snapshot.
     *
     * @return true if the channel exists and state was returned; false otherwise.
     */
    virtual bool getChannelState(uint8_t channelId,
                                 PwmChannelState& outState) const = 0;
};

} /* namespace hal */
