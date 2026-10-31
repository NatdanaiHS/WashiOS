#pragma once

#include <cstddef>
#include <cstdint>

#include "PayloadProtocol.hpp"

class HostModeCommandParser
{
public:
    enum class Event : uint8_t
    {
        None,
        ModeSelected,
        InvalidCommand
    };

    Event consume(uint8_t byte, comms::PayloadMode& selectedMode)
    {
        if (byte == static_cast<uint8_t>('\r'))
        {
            return Event::None;
        }
        if (byte == static_cast<uint8_t>('\n'))
        {
            return finishLine(selectedMode);
        }
        if (used >= Capacity - 1U)
        {
            overflowed = true;
            return Event::None;
        }

        line[used++] = static_cast<char>(byte);
        return Event::None;
    }

private:
    static constexpr std::size_t Capacity = 24U;
    char line[Capacity] = {};
    std::size_t used = 0U;
    bool overflowed = false;

    Event finishLine(comms::PayloadMode& selectedMode)
    {
        if (used == 0U && !overflowed)
        {
            return Event::None;
        }

        line[used] = '\0';
        Event event = Event::InvalidCommand;
        if (!overflowed && equals("MODE NORMAL"))
        {
            selectedMode = comms::PayloadMode::Normal;
            event = Event::ModeSelected;
        }
        else if (!overflowed && equals("MODE SILENT"))
        {
            selectedMode = comms::PayloadMode::Silent;
            event = Event::ModeSelected;
        }
        else if (!overflowed && equals("MODE BAD_CRC"))
        {
            selectedMode = comms::PayloadMode::BadCrc;
            event = Event::ModeSelected;
        }
        else if (!overflowed && equals("MODE DELAYED"))
        {
            selectedMode = comms::PayloadMode::Delayed;
            event = Event::ModeSelected;
        }

        used = 0U;
        overflowed = false;
        return event;
    }

    bool equals(const char* expected) const
    {
        std::size_t index = 0U;
        while (expected[index] != '\0' && index < used)
        {
            if (line[index] != expected[index])
            {
                return false;
            }
            ++index;
        }
        return index == used && expected[index] == '\0';
    }
};
