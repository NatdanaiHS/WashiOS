#pragma once

#include <cstddef>
#include <cstdint>

namespace hal
{

class IFlashMap
{
public:
    ~IFlashMap() = default;

    virtual uintptr_t applicationBase() const = 0;
    virtual std::size_t applicationLength() const = 0;
    virtual uintptr_t ramBase() const = 0;
    virtual std::size_t ramLength() const = 0;
    virtual bool isApplicationVectorValid() const = 0;
};

} /* namespace hal */
