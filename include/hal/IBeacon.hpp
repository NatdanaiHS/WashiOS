#pragma once

namespace hal
{

class IBeacon
{
public:
    ~IBeacon() = default;

    virtual void enterSafeLoop() = 0;
};

} /* namespace hal */
