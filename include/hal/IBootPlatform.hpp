#pragma once

#include <cstdint>

namespace hal
{

class IBootPlatform
{
public:
    ~IBootPlatform() = default;

    virtual void prepareForApplicationJump() = 0;
    virtual void jumpToApplication(uintptr_t vectorTableBase) = 0;
};

} /* namespace hal */
