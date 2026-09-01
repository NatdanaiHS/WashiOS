#include <cstddef>
#include <cstdint>

#include <unity.h>

#include "bsp/f4/F411RxRing.hpp"

void setUp()
{
}

void tearDown()
{
}

namespace
{

void test_empty_and_single_byte()
{
    bsp::F411RxRing<8U> ring;
    uint8_t byte = 0U;
    TEST_ASSERT_EQUAL_size_t(0U, ring.available());
    TEST_ASSERT_FALSE(ring.pop(byte));
    TEST_ASSERT_TRUE(ring.pushFromInterrupt(0x5AU));
    TEST_ASSERT_EQUAL_size_t(1U, ring.available());
    TEST_ASSERT_TRUE(ring.pop(byte));
    TEST_ASSERT_EQUAL_HEX8(0x5AU, byte);
    TEST_ASSERT_EQUAL_size_t(0U, ring.available());
}

void test_wrap_preserves_order()
{
    bsp::F411RxRing<5U> ring;
    uint8_t byte = 0U;
    for (uint8_t value = 1U; value <= 3U; ++value)
    {
        TEST_ASSERT_TRUE(ring.pushFromInterrupt(value));
    }
    TEST_ASSERT_TRUE(ring.pop(byte));
    TEST_ASSERT_EQUAL_UINT8(1U, byte);
    TEST_ASSERT_TRUE(ring.pop(byte));
    TEST_ASSERT_EQUAL_UINT8(2U, byte);
    TEST_ASSERT_TRUE(ring.pushFromInterrupt(4U));
    TEST_ASSERT_TRUE(ring.pushFromInterrupt(5U));
    const uint8_t expected[] = {3U, 4U, 5U};
    for (uint8_t value : expected)
    {
        TEST_ASSERT_TRUE(ring.pop(byte));
        TEST_ASSERT_EQUAL_UINT8(value, byte);
    }
    TEST_ASSERT_FALSE(ring.pop(byte));
}

void test_full_counts_overflow_without_overwrite()
{
    bsp::F411RxRing<4U> ring;
    TEST_ASSERT_TRUE(ring.pushFromInterrupt(0x11U));
    TEST_ASSERT_TRUE(ring.pushFromInterrupt(0x22U));
    TEST_ASSERT_TRUE(ring.pushFromInterrupt(0x33U));
    TEST_ASSERT_FALSE(ring.pushFromInterrupt(0x44U));
    TEST_ASSERT_EQUAL_UINT32(1U, ring.overflowCount());
    TEST_ASSERT_EQUAL_size_t(3U, ring.available());
    uint8_t byte = 0U;
    TEST_ASSERT_TRUE(ring.pop(byte)); TEST_ASSERT_EQUAL_HEX8(0x11U, byte);
    TEST_ASSERT_TRUE(ring.pop(byte)); TEST_ASSERT_EQUAL_HEX8(0x22U, byte);
    TEST_ASSERT_TRUE(ring.pop(byte)); TEST_ASSERT_EQUAL_HEX8(0x33U, byte);
}

void test_error_accounting_allows_receive_recovery()
{
    bsp::F411RxRing<8U> ring;
    ring.noteHardwareError();
    ring.noteHardwareError();
    TEST_ASSERT_EQUAL_UINT32(2U, ring.hardwareErrorCount());
    TEST_ASSERT_TRUE(ring.pushFromInterrupt(0xA5U));
    uint8_t byte = 0U;
    TEST_ASSERT_TRUE(ring.pop(byte));
    TEST_ASSERT_EQUAL_HEX8(0xA5U, byte);
}

void test_bounded_cycle_leaves_remaining_bytes()
{
    bsp::F411RxRing<128U> ring;
    for (uint8_t value = 0U; value < 100U; ++value)
    {
        TEST_ASSERT_TRUE(ring.pushFromInterrupt(value));
    }
    constexpr std::size_t MaxBytesPerCycle = 64U;
    uint8_t byte = 0U;
    std::size_t consumed = 0U;
    while (consumed < MaxBytesPerCycle && ring.pop(byte))
    {
        TEST_ASSERT_EQUAL_UINT8(static_cast<uint8_t>(consumed), byte);
        ++consumed;
    }
    TEST_ASSERT_EQUAL_size_t(MaxBytesPerCycle, consumed);
    TEST_ASSERT_EQUAL_size_t(36U, ring.available());
}

} /* namespace */

int main(int argc, char** argv)
{
    (void)argc;
    (void)argv;
    UNITY_BEGIN();
    RUN_TEST(test_empty_and_single_byte);
    RUN_TEST(test_wrap_preserves_order);
    RUN_TEST(test_full_counts_overflow_without_overwrite);
    RUN_TEST(test_error_accounting_allows_receive_recovery);
    RUN_TEST(test_bounded_cycle_leaves_remaining_bytes);
    return UNITY_END();
}
