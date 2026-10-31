#include <cstddef>
#include <cstdint>

#include "stm32g4xx_hal.h"

#include "FaultLog.hpp"
#include "boot/BootMetadata.hpp"
#include "boot/BootPolicy.hpp"
#include "bsp/g4/Stm32G4Beacon.hpp"
#include "bsp/g4/Stm32G4BootPlatform.hpp"
#include "bsp/g4/Stm32G4FlashMap.hpp"

#if !defined(WASHIBOOT_DEFAULT_EXPECTED_CRC32)
#define WASHIBOOT_DEFAULT_EXPECTED_CRC32 0x00000000UL
#endif

#if !defined(WASHIBOOT_DEFAULT_SLOT_A_CRC_LENGTH)
#define WASHIBOOT_DEFAULT_SLOT_A_CRC_LENGTH 0UL
#endif

#if defined(__GNUC__)
/* Shared with the application at fixed addresses; see .retained in bootloader.ld. */
#define WASHIBOOT_RETAINED_METADATA __attribute__((section(".retained.boot_metadata"), aligned(8)))
#define WASHIBOOT_RETAINED_FAULT_LOG __attribute__((section(".retained.fault_log"), aligned(8)))
#else
#define WASHIBOOT_RETAINED_METADATA
#define WASHIBOOT_RETAINED_FAULT_LOG
#endif

namespace
{

boot::BootMetadata bootMetadata WASHIBOOT_RETAINED_METADATA;
core::FaultLog<> systemFaultLog WASHIBOOT_RETAINED_FAULT_LOG;

bsp::Stm32G4FlashMap flashMap;
bsp::Stm32G4BootPlatform bootPlatform;
bsp::Stm32G4Beacon beacon;

} /* namespace */

int main()
{
    HAL_Init();
    beacon.initialize();

    boot::BootPolicy policy(flashMap,
                            bootPlatform,
                            beacon,
                            bootMetadata,
                            systemFaultLog,
                            static_cast<uint32_t>(WASHIBOOT_DEFAULT_EXPECTED_CRC32),
                            static_cast<std::size_t>(WASHIBOOT_DEFAULT_SLOT_A_CRC_LENGTH));
    policy.run();

    for (;;)
    {
    }
}

extern "C" void SysTick_Handler(void)
{
    HAL_IncTick();
}

#if defined(USE_FULL_ASSERT)
extern "C" void assert_failed(uint8_t* file, uint32_t line)
{
    (void)file;
    (void)line;
    beacon.enterSafeLoop();
}
#endif
