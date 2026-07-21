#pragma once

#include <cstddef>
#include <cstdint>

namespace core
{

template<std::size_t Capacity>
class FixedTextWriter
{
public:
    void clear() { length = 0U; }

    bool append(const char* text)
    {
        if (text == nullptr)
        {
            return false;
        }
        while (*text != '\0')
        {
            if (!appendChar(*text++))
            {
                return false;
            }
        }
        return true;
    }

    bool appendChar(char value)
    {
        if (length >= Capacity)
        {
            return false;
        }
        buffer[length++] = static_cast<uint8_t>(value);
        return true;
    }

    bool appendU32(uint32_t value)
    {
        char digits[10] = {};
        std::size_t count = 0U;
        do
        {
            digits[count++] = static_cast<char>('0' + (value % 10U));
            value /= 10U;
        } while (value != 0U && count < sizeof(digits));

        while (count > 0U)
        {
            if (!appendChar(digits[--count]))
            {
                return false;
            }
        }
        return true;
    }

    bool appendI32(int32_t value)
    {
        if (value < 0)
        {
            if (!appendChar('-'))
            {
                return false;
            }
            const uint32_t magnitude = static_cast<uint32_t>(-(value + 1)) + 1U;
            return appendU32(magnitude);
        }
        return appendU32(static_cast<uint32_t>(value));
    }

    const uint8_t* data() const { return buffer; }
    std::size_t size() const { return length; }

private:
    uint8_t buffer[Capacity == 0U ? 1U : Capacity] = {};
    std::size_t length = 0U;
};

} /* namespace core */
