#pragma once

#include "IGPIO.hpp"

namespace test_mocks
{

class MockGpio final : public hal::IGPIO
{
public:
    void setHigh() override
    {
        const bool previous = state;
        state = true;
        fireOnTransition(previous, state);
    }

    void setLow() override
    {
        const bool previous = state;
        state = false;
        fireOnTransition(previous, state);
    }

    void toggle() override
    {
        const bool previous = state;
        state = !state;
        fireOnTransition(previous, state);
    }

    bool read() const override
    {
        return state;
    }

    bool setInterrupt(hal::GpioInterruptEdge edge,
                      hal::GpioInterruptCallback callback,
                      void* context) override
    {
        if (callback == nullptr)
        {
            return false;
        }

        interruptEdge = edge;
        interruptCallback = callback;
        interruptContext = context;
        interruptEnabled = true;
        return true;
    }

    void clearInterrupt() override
    {
        interruptEnabled = false;
        interruptCallback = nullptr;
        interruptContext = nullptr;
    }

    bool triggerInterrupt(hal::GpioInterruptEdge edge)
    {
        if (!interruptEnabled || interruptCallback == nullptr)
        {
            return false;
        }

        if (!edgeMatches(edge))
        {
            return false;
        }

        interruptCallback(interruptContext);
        return true;
    }

private:
    bool state = false;
    bool interruptEnabled = false;
    hal::GpioInterruptEdge interruptEdge = hal::GpioInterruptEdge::Rising;
    hal::GpioInterruptCallback interruptCallback = nullptr;
    void* interruptContext = nullptr;

    bool edgeMatches(hal::GpioInterruptEdge edge) const
    {
        return interruptEdge == hal::GpioInterruptEdge::Both || interruptEdge == edge;
    }

    void fireOnTransition(bool previous, bool current)
    {
        if (previous == current)
        {
            return;
        }

        const hal::GpioInterruptEdge edge =
            current ? hal::GpioInterruptEdge::Rising : hal::GpioInterruptEdge::Falling;
        (void)triggerInterrupt(edge);
    }
};

} /* namespace test_mocks */
