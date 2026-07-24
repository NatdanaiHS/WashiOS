#pragma once

#include <cstddef>
#include <cstdint>

namespace boot
{

inline uint32_t crc32UpdateByte(uint32_t crc, uint8_t value)
{
    static constexpr uint32_t Crc32NibbleTable[16] = {
        0x00000000UL, 0x1DB71064UL, 0x3B6E20C8UL, 0x26D930ACUL,
        0x76DC4190UL, 0x6B6B51F4UL, 0x4DB26158UL, 0x5005713CUL,
        0xEDB88320UL, 0xF00F9344UL, 0xD6D6A3E8UL, 0xCB61B38CUL,
        0x9B64C2B0UL, 0x86D3D2D4UL, 0xA00AE278UL, 0xBDBDF21CUL
    };

    crc ^= static_cast<uint32_t>(value);
    crc = (crc >> 4U) ^ Crc32NibbleTable[crc & 0x0FUL];
    crc = (crc >> 4U) ^ Crc32NibbleTable[crc & 0x0FUL];
    return crc;
}

inline uint32_t crc32(const volatile uint8_t* data, std::size_t length)
{
    uint32_t crc = 0xFFFFFFFFUL;

    for (std::size_t i = 0U; i < length; ++i)
    {
        crc = crc32UpdateByte(crc, data[i]);
    }

    return ~crc;
}

inline uint32_t crc32UpdateU32(uint32_t crc, uint32_t value)
{
    for (std::size_t i = 0U; i < sizeof(value); ++i)
    {
        crc = crc32UpdateByte(crc,
                              static_cast<uint8_t>((value >> (i * 8U)) & 0xFFU));
    }

    return crc;
}

} /* namespace boot */
