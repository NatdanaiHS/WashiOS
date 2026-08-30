#include <cstdint>

#include <unity.h>

#include "HostModeCommandParser.hpp"

void setUp() {}
void tearDown() {}

namespace
{

HostModeCommandParser::Event feed(HostModeCommandParser& parser,
                                  const char* text,
                                  comms::PayloadMode& mode)
{
    HostModeCommandParser::Event event = HostModeCommandParser::Event::None;
    for (std::size_t index = 0U; text[index] != '\0'; ++index)
    {
        const HostModeCommandParser::Event next =
            parser.consume(static_cast<uint8_t>(text[index]), mode);
        if (next != HostModeCommandParser::Event::None)
        {
            event = next;
        }
    }
    return event;
}

void test_accepts_all_supported_modes()
{
    HostModeCommandParser parser;
    comms::PayloadMode mode = comms::PayloadMode::Normal;

    TEST_ASSERT_EQUAL_INT(static_cast<int>(HostModeCommandParser::Event::ModeSelected),
                          static_cast<int>(feed(parser, "MODE SILENT\r\n", mode)));
    TEST_ASSERT_EQUAL_INT(static_cast<int>(comms::PayloadMode::Silent),
                          static_cast<int>(mode));
    TEST_ASSERT_EQUAL_INT(static_cast<int>(HostModeCommandParser::Event::ModeSelected),
                          static_cast<int>(feed(parser, "MODE BAD_CRC\n", mode)));
    TEST_ASSERT_EQUAL_INT(static_cast<int>(comms::PayloadMode::BadCrc),
                          static_cast<int>(mode));
    TEST_ASSERT_EQUAL_INT(static_cast<int>(HostModeCommandParser::Event::ModeSelected),
                          static_cast<int>(feed(parser, "MODE DELAYED\n", mode)));
    TEST_ASSERT_EQUAL_INT(static_cast<int>(comms::PayloadMode::Delayed),
                          static_cast<int>(mode));
    TEST_ASSERT_EQUAL_INT(static_cast<int>(HostModeCommandParser::Event::ModeSelected),
                          static_cast<int>(feed(parser, "MODE NORMAL\n", mode)));
    TEST_ASSERT_EQUAL_INT(static_cast<int>(comms::PayloadMode::Normal),
                          static_cast<int>(mode));
}

void test_rejects_unknown_case_partial_and_overlong_commands()
{
    HostModeCommandParser parser;
    comms::PayloadMode mode = comms::PayloadMode::Normal;

    TEST_ASSERT_EQUAL_INT(static_cast<int>(HostModeCommandParser::Event::InvalidCommand),
                          static_cast<int>(feed(parser, "mode silent\n", mode)));
    TEST_ASSERT_EQUAL_INT(static_cast<int>(HostModeCommandParser::Event::InvalidCommand),
                          static_cast<int>(feed(parser, "MODE\n", mode)));
    TEST_ASSERT_EQUAL_INT(static_cast<int>(HostModeCommandParser::Event::InvalidCommand),
                          static_cast<int>(feed(parser,
                              "MODE NORMAL WITH TRAILING JUNK\n", mode)));
    TEST_ASSERT_EQUAL_INT(static_cast<int>(comms::PayloadMode::Normal),
                          static_cast<int>(mode));
}

void test_fragmented_command_waits_for_newline_and_parser_recovers()
{
    HostModeCommandParser parser;
    comms::PayloadMode mode = comms::PayloadMode::Normal;

    TEST_ASSERT_EQUAL_INT(static_cast<int>(HostModeCommandParser::Event::None),
                          static_cast<int>(feed(parser, "MODE SIL", mode)));
    TEST_ASSERT_EQUAL_INT(static_cast<int>(HostModeCommandParser::Event::ModeSelected),
                          static_cast<int>(feed(parser, "ENT\n", mode)));
    TEST_ASSERT_EQUAL_INT(static_cast<int>(HostModeCommandParser::Event::InvalidCommand),
                          static_cast<int>(feed(parser, "BAD\n", mode)));
    TEST_ASSERT_EQUAL_INT(static_cast<int>(HostModeCommandParser::Event::ModeSelected),
                          static_cast<int>(feed(parser, "MODE NORMAL\n", mode)));
}

} /* namespace */

int main()
{
    UNITY_BEGIN();
    RUN_TEST(test_accepts_all_supported_modes);
    RUN_TEST(test_rejects_unknown_case_partial_and_overlong_commands);
    RUN_TEST(test_fragmented_command_waits_for_newline_and_parser_recovers);
    return UNITY_END();
}
