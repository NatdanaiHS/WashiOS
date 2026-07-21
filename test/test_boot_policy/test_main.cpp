#include <cstdint>
#include <cstddef>

#include <unity.h>

#include "boot/BootMetadata.hpp"
#include "boot/BootPolicy.hpp"
#include "hal/IBootPlatform.hpp"
#include "hal/IBeacon.hpp"
#include "hal/IFlashMap.hpp"

void setUp()
{
}

void tearDown()
{
}

namespace
{

constexpr std::size_t TestSlotLength = 64U;

uint8_t slotA[TestSlotLength] = {};
uint8_t slotB[TestSlotLength] = {};

struct MockFlashMap final : public hal::IFlashMap
{
    bool slotAVectorValid = true;
    bool slotBVectorValid = true;

    uintptr_t slotBase(hal::FirmwareSlot slot) const override
    {
        return reinterpret_cast<uintptr_t>(
            (slot == hal::FirmwareSlot::SlotB) ? slotB : slotA);
    }

    std::size_t slotLength(hal::FirmwareSlot) const override
    {
        return TestSlotLength;
    }

    bool isSlotVectorValid(hal::FirmwareSlot slot) const override
    {
        return (slot == hal::FirmwareSlot::SlotB) ? slotBVectorValid :
                                                    slotAVectorValid;
    }

    uintptr_t applicationBase() const override
    {
        return slotBase(hal::FirmwareSlot::SlotA);
    }

    std::size_t applicationLength() const override
    {
        return slotLength(hal::FirmwareSlot::SlotA);
    }

    uintptr_t ramBase() const override
    {
        return 0x20000000UL;
    }

    std::size_t ramLength() const override
    {
        return 32UL * 1024UL;
    }

    bool isApplicationVectorValid() const override
    {
        return isSlotVectorValid(hal::FirmwareSlot::SlotA);
    }
};

struct MockBootPlatform final : public hal::IBootPlatform
{
    uint32_t prepareCount = 0U;
    uintptr_t jumpedVector = 0U;

    void prepareForApplicationJump() override
    {
        ++prepareCount;
    }

    void jumpToApplication(uintptr_t vectorTableBase) override
    {
        jumpedVector = vectorTableBase;
    }
};

struct MockBeacon final : public hal::IBeacon
{
    uint32_t safeLoopCount = 0U;

    void enterSafeLoop() override
    {
        ++safeLoopCount;
    }
};

void fillSlot(uint8_t* slot, uint8_t seed)
{
    for (std::size_t i = 0U; i < TestSlotLength; ++i)
    {
        slot[i] = static_cast<uint8_t>(seed + i);
    }
}

uint32_t slotCrc(const uint8_t* slot)
{
    return boot::crc32(slot, TestSlotLength);
}

uint32_t slotCrcLength(const uint8_t* slot, std::size_t length)
{
    return boot::crc32(slot, length);
}

void configureMetadata(boot::BootMetadata& metadata,
                       boot::BootSlot activeSlot,
                       uint32_t slotACrc,
                       uint32_t slotBCrc)
{
    boot::initializeBootMetadata(metadata, slotACrc);
    metadata.active_slot = static_cast<uint32_t>(activeSlot);
    metadata.slot_a_crc32 = slotACrc;
    metadata.slot_b_crc32 = slotBCrc;
    metadata.slot_a_state = static_cast<uint32_t>(boot::FirmwareSlotState::Confirmed);
    metadata.slot_b_state = static_cast<uint32_t>(boot::FirmwareSlotState::Valid);
    boot::commitBootMetadata(metadata);
}

void test_legacy_metadata_migrates_to_current_version()
{
    boot::BootMetadata metadata = {};
    metadata.signature = core::WASHIOS_MAGIC_SIGNATURE;
    metadata.boot_count = 2U;
    metadata.confirmed_flag = 0U;
    metadata.expected_firmware_crc32 = 0x12345678UL;
    metadata.checksum = boot::calculateLegacyBootMetadataChecksum(metadata);

    TEST_ASSERT_TRUE(boot::recoverBootMetadata(metadata, 0xABCDEF01UL));
    TEST_ASSERT_TRUE(boot::hasValidBootMetadata(metadata));
    TEST_ASSERT_EQUAL_UINT32(boot::BootMetadataCurrentVersion,
                             metadata.metadata_version);
    TEST_ASSERT_EQUAL_UINT32(static_cast<uint32_t>(boot::BootSlot::SlotA),
                             metadata.active_slot);
    TEST_ASSERT_EQUAL_UINT32(0x12345678UL, metadata.slot_a_crc32);
    TEST_ASSERT_EQUAL_UINT32(
        static_cast<uint32_t>(boot::FirmwareSlotState::Confirmed),
        metadata.slot_a_state);
}

void test_corrupt_metadata_initializes_safe_default()
{
    boot::BootMetadata metadata = {};
    metadata.signature = core::WASHIOS_MAGIC_SIGNATURE;
    metadata.checksum = 0xBADCAFEUL;

    TEST_ASSERT_FALSE(boot::recoverBootMetadata(metadata, 0x2468ACE0UL));
    TEST_ASSERT_TRUE(boot::hasValidBootMetadata(metadata));
    TEST_ASSERT_EQUAL_UINT32(static_cast<uint32_t>(boot::BootSlot::SlotA),
                             metadata.active_slot);
    TEST_ASSERT_EQUAL_UINT32(0x2468ACE0UL, metadata.slot_a_crc32);
    TEST_ASSERT_EQUAL_UINT32(
        static_cast<uint32_t>(boot::FirmwareSlotState::Confirmed),
        metadata.slot_a_state);
}

void test_valid_empty_metadata_adopts_provisioned_default()
{
    boot::BootMetadata metadata = {};
    boot::initializeBootMetadata(metadata, 0U);

    TEST_ASSERT_TRUE(boot::hasValidBootMetadata(metadata));
    TEST_ASSERT_TRUE(boot::recoverBootMetadata(metadata, 0x13572468UL));

    TEST_ASSERT_EQUAL_UINT32(0x13572468UL, metadata.expected_firmware_crc32);
    TEST_ASSERT_EQUAL_UINT32(0x13572468UL, metadata.slot_a_crc32);
    TEST_ASSERT_EQUAL_UINT32(
        static_cast<uint32_t>(boot::FirmwareSlotState::Confirmed),
        metadata.slot_a_state);
}

void test_slot_a_valid_boots_slot_a()
{
    fillSlot(slotA, 0x10U);
    fillSlot(slotB, 0x80U);
    MockFlashMap flashMap;
    MockBootPlatform platform;
    MockBeacon beacon;
    boot::BootMetadata metadata = {};
    core::FaultLog<> faultLog;
    faultLog.clear();
    configureMetadata(metadata,
                      boot::BootSlot::SlotA,
                      slotCrc(slotA),
                      slotCrc(slotB));

    boot::BootPolicy policy(flashMap, platform, beacon, metadata, faultLog, 0U);
    policy.run();

    TEST_ASSERT_EQUAL_UINT32(1U, platform.prepareCount);
    TEST_ASSERT_EQUAL_UINT64(
        static_cast<uint64_t>(flashMap.slotBase(hal::FirmwareSlot::SlotA)),
        static_cast<uint64_t>(platform.jumpedVector));
    TEST_ASSERT_EQUAL_UINT32(0U, beacon.safeLoopCount);
    TEST_ASSERT_EQUAL_UINT32(static_cast<uint32_t>(boot::BootSlot::SlotA),
                             metadata.last_boot_slot);
}

void test_default_slot_a_crc_uses_provisioned_image_length()
{
    fillSlot(slotA, 0x50U);
    fillSlot(slotB, 0x80U);
    MockFlashMap flashMap;
    MockBootPlatform platform;
    MockBeacon beacon;
    boot::BootMetadata metadata = {};
    core::FaultLog<> faultLog;
    faultLog.clear();
    constexpr std::size_t ProvisionedLength = 16U;
    const uint32_t provisionedCrc = slotCrcLength(slotA, ProvisionedLength);
    boot::initializeBootMetadata(metadata, provisionedCrc);

    boot::BootPolicy policy(flashMap,
                            platform,
                            beacon,
                            metadata,
                            faultLog,
                            provisionedCrc,
                            ProvisionedLength);
    policy.run();

    TEST_ASSERT_EQUAL_UINT32(1U, platform.prepareCount);
    TEST_ASSERT_EQUAL_UINT64(
        static_cast<uint64_t>(flashMap.slotBase(hal::FirmwareSlot::SlotA)),
        static_cast<uint64_t>(platform.jumpedVector));
    TEST_ASSERT_EQUAL_UINT32(0U, beacon.safeLoopCount);
}

void test_confirmed_slot_ignores_unconfirmed_boot_limit()
{
    fillSlot(slotA, 0x60U);
    fillSlot(slotB, 0x90U);
    MockFlashMap flashMap;
    MockBootPlatform platform;
    MockBeacon beacon;
    boot::BootMetadata metadata = {};
    core::FaultLog<> faultLog;
    faultLog.clear();
    configureMetadata(metadata,
                      boot::BootSlot::SlotA,
                      slotCrc(slotA),
                      slotCrc(slotB));
    metadata.boot_count = boot::MaxUnconfirmedBootAttempts + 1U;
    metadata.slot_a_state = static_cast<uint32_t>(boot::FirmwareSlotState::Confirmed);
    boot::commitBootMetadata(metadata);

    boot::BootPolicy policy(flashMap, platform, beacon, metadata, faultLog, 0U);
    policy.run();

    TEST_ASSERT_EQUAL_UINT32(1U, platform.prepareCount);
    TEST_ASSERT_EQUAL_UINT32(0U, beacon.safeLoopCount);
}

void test_pending_slot_over_attempt_limit_enters_safe_loop()
{
    fillSlot(slotA, 0x70U);
    fillSlot(slotB, 0xA0U);
    MockFlashMap flashMap;
    MockBootPlatform platform;
    MockBeacon beacon;
    boot::BootMetadata metadata = {};
    core::FaultLog<> faultLog;
    faultLog.clear();
    configureMetadata(metadata,
                      boot::BootSlot::SlotA,
                      slotCrc(slotA),
                      slotCrc(slotB));
    metadata.boot_count = boot::MaxUnconfirmedBootAttempts + 1U;
    metadata.slot_a_state = static_cast<uint32_t>(boot::FirmwareSlotState::Pending);
    boot::commitBootMetadata(metadata);

    boot::BootPolicy policy(flashMap, platform, beacon, metadata, faultLog, 0U);
    policy.run();

    TEST_ASSERT_EQUAL_UINT32(0U, platform.prepareCount);
    TEST_ASSERT_EQUAL_UINT32(1U, beacon.safeLoopCount);
    TEST_ASSERT_EQUAL_UINT32(boot::DetailBootLoopLimit, metadata.last_fail_reason);
}

void test_stale_slot_a_crc_adopts_matching_default_image()
{
    fillSlot(slotA, 0x78U);
    fillSlot(slotB, 0xA8U);
    MockFlashMap flashMap;
    MockBootPlatform platform;
    MockBeacon beacon;
    boot::BootMetadata metadata = {};
    core::FaultLog<> faultLog;
    faultLog.clear();
    constexpr std::size_t ProvisionedLength = 24U;
    const uint32_t provisionedCrc = slotCrcLength(slotA, ProvisionedLength);
    configureMetadata(metadata,
                      boot::BootSlot::SlotA,
                      slotCrc(slotA) ^ 0x1UL,
                      slotCrc(slotB));

    boot::BootPolicy policy(flashMap,
                            platform,
                            beacon,
                            metadata,
                            faultLog,
                            provisionedCrc,
                            ProvisionedLength);
    policy.run();

    TEST_ASSERT_EQUAL_UINT32(1U, platform.prepareCount);
    TEST_ASSERT_EQUAL_UINT32(0U, beacon.safeLoopCount);
    TEST_ASSERT_EQUAL_UINT32(provisionedCrc, metadata.slot_a_crc32);
}

void test_slot_a_crc_failure_falls_back_to_slot_b()
{
    fillSlot(slotA, 0x20U);
    fillSlot(slotB, 0x90U);
    MockFlashMap flashMap;
    MockBootPlatform platform;
    MockBeacon beacon;
    boot::BootMetadata metadata = {};
    core::FaultLog<> faultLog;
    faultLog.clear();
    configureMetadata(metadata,
                      boot::BootSlot::SlotA,
                      slotCrc(slotA) ^ 0x1UL,
                      slotCrc(slotB));

    boot::BootPolicy policy(flashMap, platform, beacon, metadata, faultLog, 0U);
    policy.run();

    TEST_ASSERT_EQUAL_UINT32(1U, platform.prepareCount);
    TEST_ASSERT_EQUAL_UINT64(
        static_cast<uint64_t>(flashMap.slotBase(hal::FirmwareSlot::SlotB)),
        static_cast<uint64_t>(platform.jumpedVector));
    TEST_ASSERT_EQUAL_UINT32(static_cast<uint32_t>(boot::BootSlot::SlotB),
                             metadata.active_slot);
    TEST_ASSERT_EQUAL_UINT32(static_cast<uint32_t>(boot::BootSlot::SlotB),
                             metadata.last_boot_slot);
}

void test_slot_a_invalid_vector_falls_back_to_slot_b()
{
    fillSlot(slotA, 0x30U);
    fillSlot(slotB, 0xA0U);
    MockFlashMap flashMap;
    flashMap.slotAVectorValid = false;
    MockBootPlatform platform;
    MockBeacon beacon;
    boot::BootMetadata metadata = {};
    core::FaultLog<> faultLog;
    faultLog.clear();
    configureMetadata(metadata,
                      boot::BootSlot::SlotA,
                      slotCrc(slotA),
                      slotCrc(slotB));

    boot::BootPolicy policy(flashMap, platform, beacon, metadata, faultLog, 0U);
    policy.run();

    TEST_ASSERT_EQUAL_UINT64(
        static_cast<uint64_t>(flashMap.slotBase(hal::FirmwareSlot::SlotB)),
        static_cast<uint64_t>(platform.jumpedVector));
    TEST_ASSERT_EQUAL_UINT32(static_cast<uint32_t>(boot::BootSlot::SlotB),
                             metadata.active_slot);
}

void test_both_slots_fail_enter_safe_loop_and_record_fault()
{
    fillSlot(slotA, 0x40U);
    fillSlot(slotB, 0xB0U);
    MockFlashMap flashMap;
    flashMap.slotAVectorValid = false;
    flashMap.slotBVectorValid = false;
    MockBootPlatform platform;
    MockBeacon beacon;
    boot::BootMetadata metadata = {};
    core::FaultLog<> faultLog;
    faultLog.clear();
    core::FaultEvent event = {};
    configureMetadata(metadata,
                      boot::BootSlot::SlotA,
                      slotCrc(slotA),
                      slotCrc(slotB));

    boot::BootPolicy policy(flashMap, platform, beacon, metadata, faultLog, 0U);
    policy.run();

    TEST_ASSERT_EQUAL_UINT32(0U, platform.prepareCount);
    TEST_ASSERT_EQUAL_UINT32(1U, beacon.safeLoopCount);
    TEST_ASSERT_TRUE(faultLog.latest(event));
    TEST_ASSERT_EQUAL_INT(static_cast<int>(core::FaultEventType::SafeFail),
                          static_cast<int>(event.type));
    TEST_ASSERT_EQUAL_UINT32(boot::DetailNoValidFirmwareSlot, event.detailCode);
    TEST_ASSERT_EQUAL_UINT32(boot::DetailNoValidFirmwareSlot,
                             metadata.last_fail_reason);
}

} /* namespace */

int main()
{
    UNITY_BEGIN();
    RUN_TEST(test_legacy_metadata_migrates_to_current_version);
    RUN_TEST(test_corrupt_metadata_initializes_safe_default);
    RUN_TEST(test_valid_empty_metadata_adopts_provisioned_default);
    RUN_TEST(test_slot_a_valid_boots_slot_a);
    RUN_TEST(test_default_slot_a_crc_uses_provisioned_image_length);
    RUN_TEST(test_confirmed_slot_ignores_unconfirmed_boot_limit);
    RUN_TEST(test_pending_slot_over_attempt_limit_enters_safe_loop);
    RUN_TEST(test_stale_slot_a_crc_adopts_matching_default_image);
    RUN_TEST(test_slot_a_crc_failure_falls_back_to_slot_b);
    RUN_TEST(test_slot_a_invalid_vector_falls_back_to_slot_b);
    RUN_TEST(test_both_slots_fail_enter_safe_loop_and_record_fault);
    return UNITY_END();
}
