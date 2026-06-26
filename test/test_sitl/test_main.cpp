#include <cstdint>

#include <unity.h>

#include "MockAdc.hpp"
#include "MockCanBus.hpp"
#include "MockGpio.hpp"
#include "MockI2cBus.hpp"
#include "MockPwm.hpp"
#include "MockSpiBus.hpp"
#include "MockTiming.hpp"
#include "MockUart.hpp"
#include "SitlRuntime.hpp"
#include "BootFailSafe.hpp"
#include "FaultLog.hpp"
#include "TMR.hpp"
#include "TaskHealth.hpp"
#include "Telemetry.hpp"
#include "Watchdog.hpp"

void setUp()
{
}

void tearDown()
{
}

namespace
{

struct CriticalSectionProbe
{
    uint32_t enterCount;
    uint32_t exitCount;
    uint32_t maxDepth;
    uint32_t depth;
    bool underflow;
};

CriticalSectionProbe criticalProbe = {};

struct InterruptCounter
{
    uint32_t count;
};

struct SafeFailCounter
{
    uint32_t count;
};

struct HardwareRefreshCounter
{
    uint32_t count;
};

struct BootRecoveryCounter
{
    uint32_t count;
};

void resetCriticalProbe()
{
    criticalProbe = {};
}

void countInterrupt(void* context) noexcept
{
    InterruptCounter* const counter = static_cast<InterruptCounter*>(context);
    if (counter != nullptr)
    {
        ++counter->count;
    }
}

void countSafeFail(void* context)
{
    SafeFailCounter* const counter = static_cast<SafeFailCounter*>(context);
    if (counter != nullptr)
    {
        ++counter->count;
    }
}

void countHardwareRefresh(void* context)
{
    HardwareRefreshCounter* const counter =
        static_cast<HardwareRefreshCounter*>(context);
    if (counter != nullptr)
    {
        ++counter->count;
    }
}

void countBootRecovery(void* context)
{
    BootRecoveryCounter* const counter =
        static_cast<BootRecoveryCounter*>(context);
    if (counter != nullptr)
    {
        ++counter->count;
    }
}

bool sendHeartbeatFrame(hal::IGPIO& led, hal::IUart& uart, hal::ITiming& timing)
{
    led.toggle();
    const uint8_t frame[3] = {
        static_cast<uint8_t>(0xA5U),
        static_cast<uint8_t>(led.read() ? 1U : 0U),
        static_cast<uint8_t>(timing.getSystemTick() & 0xFFU)
    };
    return uart.writeBuffer(frame, sizeof(frame), 10U);
}

void test_gpio_interrupt_and_app_logic()
{
    test_mocks::MockGpio gpio;
    test_mocks::MockUart<> uart;
    test_mocks::MockTiming timing;
    InterruptCounter counter = {0};

    TEST_ASSERT_TRUE(gpio.setInterrupt(hal::GpioInterruptEdge::Rising,
                                       countInterrupt,
                                       &counter));
    gpio.setHigh();
    gpio.setLow();
    TEST_ASSERT_EQUAL_UINT32(1U, counter.count);

    timing.setTickMs(42U);
    TEST_ASSERT_TRUE(sendHeartbeatFrame(gpio, uart, timing));
    TEST_ASSERT_TRUE(gpio.read());
    TEST_ASSERT_EQUAL_size_t(3U, uart.txAvailable());

    uint8_t tx[3] = {};
    TEST_ASSERT_TRUE(uart.readTx(tx, sizeof(tx)));
    TEST_ASSERT_EQUAL_UINT8(0xA5U, tx[0]);
    TEST_ASSERT_EQUAL_UINT8(1U, tx[1]);
    TEST_ASSERT_EQUAL_UINT8(42U, tx[2]);
}

void test_uart_rx_tx_and_timeout()
{
    test_mocks::MockUart<8, 8> uart;
    const uint8_t rxData[2] = {0x11U, 0x22U};
    uint8_t buffer[2] = {};

    TEST_ASSERT_TRUE(uart.injectRx(rxData, sizeof(rxData)));
    TEST_ASSERT_EQUAL_size_t(2U, uart.available());
    TEST_ASSERT_TRUE(uart.readBuffer(buffer, sizeof(buffer), 5U));
    TEST_ASSERT_EQUAL_UINT8(0x11U, buffer[0]);
    TEST_ASSERT_EQUAL_UINT8(0x22U, buffer[1]);

    uart.setForcedTimeout(true);
    TEST_ASSERT_FALSE(uart.writeBuffer(rxData, sizeof(rxData), 5U));
}

void test_i2c_timeout_and_nominal_read_write()
{
    test_mocks::MockI2cBus<> i2c;
    const uint8_t writeData[2] = {0xAAU, 0x55U};
    const uint8_t readData[2] = {0x10U, 0x20U};
    uint8_t buffer[2] = {};

    TEST_ASSERT_TRUE(i2c.write(0x42U, writeData, sizeof(writeData), 10U));
    TEST_ASSERT_EQUAL_UINT16(0x42U, i2c.getLastAddress());
    TEST_ASSERT_EQUAL_INT(static_cast<int>(hal::I2cBusState::Ready),
                          static_cast<int>(i2c.getState()));

    TEST_ASSERT_TRUE(i2c.setReadData(readData, sizeof(readData)));
    TEST_ASSERT_TRUE(i2c.read(0x42U, buffer, sizeof(buffer), 10U));
    TEST_ASSERT_EQUAL_UINT8(0x10U, buffer[0]);
    TEST_ASSERT_EQUAL_UINT8(0x20U, buffer[1]);

    buffer[0] = 0U;
    buffer[1] = 0U;
    TEST_ASSERT_TRUE(i2c.writeRead(0x42U,
                                   writeData,
                                   sizeof(writeData),
                                   buffer,
                                   sizeof(buffer),
                                   10U));
    TEST_ASSERT_EQUAL_UINT32(1U, i2c.getWriteReadCount());
    TEST_ASSERT_EQUAL_UINT8(0x10U, buffer[0]);
    TEST_ASSERT_EQUAL_UINT8(0x20U, buffer[1]);

    i2c.setForcedTimeout(true);
    TEST_ASSERT_EQUAL_INT(static_cast<int>(hal::I2cBusState::BusLocked),
                          static_cast<int>(i2c.getState()));
    TEST_ASSERT_FALSE(i2c.read(0x42U, buffer, sizeof(buffer), 10U));
}

void test_spi_transfer_and_timeout()
{
    test_mocks::MockSpiBus<> spi;
    const uint8_t tx[3] = {1U, 2U, 3U};
    const uint8_t response[3] = {4U, 5U, 6U};
    uint8_t rx[3] = {};

    spi.setFrequency(1000000U);
    spi.selectChip(2U);
    TEST_ASSERT_TRUE(spi.isSelected(2U));
    TEST_ASSERT_EQUAL_INT(static_cast<int>(hal::SpiBusState::Ready),
                          static_cast<int>(spi.getState()));
    TEST_ASSERT_TRUE(spi.setResponse(response, sizeof(response)));
    TEST_ASSERT_TRUE(spi.transfer(tx, rx, sizeof(rx), 10U));
    TEST_ASSERT_EQUAL_UINT8(4U, rx[0]);
    TEST_ASSERT_EQUAL_UINT8(5U, rx[1]);
    TEST_ASSERT_EQUAL_UINT8(6U, rx[2]);

    spi.setForcedTimeout(true);
    TEST_ASSERT_EQUAL_INT(static_cast<int>(hal::SpiBusState::Error),
                          static_cast<int>(spi.getState()));
    TEST_ASSERT_FALSE(spi.transfer(tx, rx, sizeof(rx), 10U));
    spi.resetBus();
    TEST_ASSERT_EQUAL_UINT32(1U, spi.getResetCount());
    TEST_ASSERT_FALSE(spi.isSelected(2U));
    TEST_ASSERT_EQUAL_INT(static_cast<int>(hal::SpiBusState::Ready),
                          static_cast<int>(spi.getState()));
}

void test_can_loopback_and_error_state()
{
    test_mocks::MockCanBus<> can;
    hal::CanFrame frame = {};
    frame.messageId = 0x123U;
    frame.dataLength = 2U;
    frame.data[0] = 0xCAU;
    frame.data[1] = 0xFEU;

    TEST_ASSERT_TRUE(can.begin(500000U));
    can.setLoopback(true);
    TEST_ASSERT_TRUE(can.transmit(frame, 10U));

    hal::CanFrame received = {};
    TEST_ASSERT_TRUE(can.receive(received, 10U));
    TEST_ASSERT_EQUAL_UINT32(0x123U, received.messageId);
    TEST_ASSERT_EQUAL_UINT8(2U, received.dataLength);
    TEST_ASSERT_EQUAL_UINT8(0xCAU, received.data[0]);

    can.setState(hal::CanBusState::BusOff);
    TEST_ASSERT_FALSE(can.transmit(frame, 10U));
    can.recoverBus();
    TEST_ASSERT_EQUAL_INT(static_cast<int>(hal::CanBusState::Ready),
                          static_cast<int>(can.getState()));
}

void test_adc_raw_voltage_and_timeout()
{
    test_mocks::MockAdc<> adc;
    uint16_t raw = 0;
    float voltage = 0.0F;

    TEST_ASSERT_TRUE(adc.setResolution(12U));
    TEST_ASSERT_TRUE(adc.setRawValue(1U, 2048U));
    TEST_ASSERT_TRUE(adc.readRaw(1U, raw, 10U));
    TEST_ASSERT_EQUAL_UINT16(2048U, raw);
    TEST_ASSERT_TRUE(adc.readVoltage(1U, voltage, 10U));
    TEST_ASSERT_FLOAT_WITHIN(0.01F, 1.65F, voltage);

    adc.setForcedTimeout(true);
    TEST_ASSERT_FALSE(adc.readRaw(1U, raw, 10U));
}

void test_pwm_channel_state()
{
    test_mocks::MockPwm<> pwm;
    hal::PwmChannelState state = {};

    TEST_ASSERT_TRUE(pwm.setFrequency(0U, 1000U));
    TEST_ASSERT_TRUE(pwm.setDutyCycle(0U, 25.0F));
    pwm.start(0U);
    TEST_ASSERT_TRUE(pwm.getChannelState(0U, state));
    TEST_ASSERT_EQUAL_UINT32(1000U, state.frequencyHz);
    TEST_ASSERT_FLOAT_WITHIN(0.001F, 25.0F, state.dutyCyclePercentage);
    TEST_ASSERT_TRUE(state.enabled);

    pwm.stop(0U);
    TEST_ASSERT_TRUE(pwm.getChannelState(0U, state));
    TEST_ASSERT_FALSE(state.enabled);
    TEST_ASSERT_FLOAT_WITHIN(0.001F, 0.0F, state.dutyCyclePercentage);
}

void test_tmr_clean_read_logs_no_fault()
{
    core::FaultLog<> log;
    core::TMR<uint32_t> value(1234U);

    TEST_ASSERT_EQUAL_UINT32(1234U, value.get(log, 10U, 1U, 0U));
    TEST_ASSERT_EQUAL_UINT32(0U, value.corrections());
    TEST_ASSERT_EQUAL_size_t(0U, log.size());
}

void test_tmr_repairs_corrupted_copies()
{
    core::FaultLog<> log;
    core::TMR<uint32_t> value(77U);
    uint32_t copy = 0;
    core::FaultEvent event = {};

    TEST_ASSERT_TRUE(value.corruptCopy(0U, 88U));
    TEST_ASSERT_EQUAL_UINT32(77U, value.get(log, 20U, 2U, 10U));
    TEST_ASSERT_TRUE(value.readCopy(0U, copy));
    TEST_ASSERT_EQUAL_UINT32(77U, copy);

    TEST_ASSERT_TRUE(value.corruptCopy(1U, 99U));
    TEST_ASSERT_EQUAL_UINT32(77U, value.get(log, 21U, 2U, 11U));
    TEST_ASSERT_TRUE(value.readCopy(1U, copy));
    TEST_ASSERT_EQUAL_UINT32(77U, copy);

    TEST_ASSERT_TRUE(value.corruptCopy(2U, 100U));
    TEST_ASSERT_EQUAL_UINT32(77U, value.get(log, 22U, 2U, 12U));
    TEST_ASSERT_TRUE(value.readCopy(2U, copy));
    TEST_ASSERT_EQUAL_UINT32(77U, copy);

    TEST_ASSERT_EQUAL_UINT32(3U, value.corrections());
    TEST_ASSERT_EQUAL_size_t(3U, log.size());
    TEST_ASSERT_TRUE(log.latest(event));
    TEST_ASSERT_EQUAL_INT(static_cast<int>(core::FaultEventType::TmrCorrection),
                          static_cast<int>(event.type));
    TEST_ASSERT_EQUAL_UINT32(3U, event.correctionCount);
}

void test_tmr_unrecoverable_uses_deterministic_fallback()
{
    core::FaultLog<> log;
    core::TMR<uint32_t> value(1U);
    core::FaultEvent event = {};

    core::TMR<uint32_t>::clearUnrecoverablePanic();
    TEST_ASSERT_TRUE(value.corruptCopy(0U, 10U));
    TEST_ASSERT_TRUE(value.corruptCopy(1U, 20U));
    TEST_ASSERT_TRUE(value.corruptCopy(2U, 30U));

    TEST_ASSERT_EQUAL_UINT32(0U, value.get(log, 30U, 3U, 99U));
    TEST_ASSERT_TRUE(core::TMR<uint32_t>::didTriggerUnrecoverablePanic());
    TEST_ASSERT_EQUAL_size_t(1U, log.size());
    TEST_ASSERT_TRUE(log.latest(event));
    TEST_ASSERT_EQUAL_INT(static_cast<int>(core::FaultEventType::TmrUnrecoverable),
                          static_cast<int>(event.type));
    TEST_ASSERT_EQUAL_UINT8(3U, event.taskId);
    TEST_ASSERT_EQUAL_UINT32(99U, event.detailCode);
}

void test_watchdog_allows_healthy_task()
{
    test_mocks::MockTiming timing;
    core::FaultLog<> log;
    core::TaskHealthRegistry<> registry;
    SafeFailCounter counter = {0};
    core::Watchdog<> watchdog(timing, registry, log, countSafeFail, &counter);

    TEST_ASSERT_TRUE(registry.registerTask(1U, 100U, true, timing.getSystemTick()));
    timing.delayMs(50U);
    TEST_ASSERT_TRUE(registry.checkIn(1U, timing.getSystemTick()));
    timing.delayMs(80U);

    const core::TaskHealthEvaluation result = watchdog.poll();
    TEST_ASSERT_EQUAL_INT(static_cast<int>(core::TaskHealthStatus::Healthy),
                          static_cast<int>(result.status));
    TEST_ASSERT_EQUAL_UINT32(0U, counter.count);
    TEST_ASSERT_EQUAL_size_t(0U, log.size());
}

void test_watchdog_critical_timeout_safe_fails_once()
{
    test_mocks::MockTiming timing;
    core::FaultLog<> log;
    core::TaskHealthRegistry<> registry;
    SafeFailCounter counter = {0};
    core::Watchdog<> watchdog(timing, registry, log, countSafeFail, &counter);
    core::FaultEvent event = {};

    TEST_ASSERT_TRUE(registry.registerTask(2U, 100U, true, timing.getSystemTick()));
    timing.delayMs(101U);

    const core::TaskHealthEvaluation firstResult = watchdog.poll();
    TEST_ASSERT_EQUAL_INT(static_cast<int>(core::TaskHealthStatus::CriticalFailure),
                          static_cast<int>(firstResult.status));
    TEST_ASSERT_EQUAL_UINT32(1U, counter.count);
    TEST_ASSERT_EQUAL_size_t(3U, log.size());
    TEST_ASSERT_TRUE(log.latest(event));
    TEST_ASSERT_EQUAL_INT(static_cast<int>(core::FaultEventType::SafeFail),
                          static_cast<int>(event.type));
    TEST_ASSERT_EQUAL_UINT8(2U, event.taskId);

    const core::TaskHealthEvaluation secondResult = watchdog.poll();
    TEST_ASSERT_EQUAL_INT(static_cast<int>(core::TaskHealthStatus::CriticalFailure),
                          static_cast<int>(secondResult.status));
    TEST_ASSERT_EQUAL_UINT32(1U, counter.count);
    TEST_ASSERT_EQUAL_size_t(3U, log.size());
}

void test_watchdog_noncritical_timeout_logs_without_safe_fail()
{
    test_mocks::MockTiming timing;
    core::FaultLog<> log;
    core::TaskHealthRegistry<> registry;
    SafeFailCounter counter = {0};
    core::Watchdog<> watchdog(timing, registry, log, countSafeFail, &counter);
    core::FaultEvent event = {};

    TEST_ASSERT_TRUE(registry.registerTask(3U, 100U, false, timing.getSystemTick()));
    timing.delayMs(101U);

    const core::TaskHealthEvaluation result = watchdog.poll();
    TEST_ASSERT_EQUAL_INT(static_cast<int>(core::TaskHealthStatus::NonCriticalFailure),
                          static_cast<int>(result.status));
    TEST_ASSERT_EQUAL_UINT32(0U, counter.count);
    TEST_ASSERT_EQUAL_size_t(1U, log.size());
    TEST_ASSERT_TRUE(log.latest(event));
    TEST_ASSERT_EQUAL_INT(static_cast<int>(core::FaultEventType::TaskCheckinFailure),
                          static_cast<int>(event.type));
    TEST_ASSERT_EQUAL_UINT8(3U, event.taskId);
}

void test_fault_log_wraps_deterministically()
{
    core::FaultLog<3> log;
    core::FaultEvent event = {};

    for (uint32_t i = 0; i < 5U; ++i)
    {
        TEST_ASSERT_TRUE(log.record(core::FaultEventType::AssertFailure,
                                    i,
                                    static_cast<uint8_t>(i),
                                    i,
                                    0U));
    }

    TEST_ASSERT_EQUAL_size_t(3U, log.size());
    TEST_ASSERT_EQUAL_UINT32(5U, log.totalEvents());

    TEST_ASSERT_TRUE(log.read(0U, event));
    TEST_ASSERT_EQUAL_UINT32(2U, event.detailCode);
    TEST_ASSERT_TRUE(log.read(1U, event));
    TEST_ASSERT_EQUAL_UINT32(3U, event.detailCode);
    TEST_ASSERT_TRUE(log.read(2U, event));
    TEST_ASSERT_EQUAL_UINT32(4U, event.detailCode);
    TEST_ASSERT_TRUE(log.recoverRetainedState());

    log.corruptRetainedStateForTest();

    TEST_ASSERT_FALSE(log.recoverRetainedState());
    TEST_ASSERT_EQUAL_size_t(0U, log.size());
    TEST_ASSERT_EQUAL_UINT32(0U, log.totalEvents());
}

void test_fault_log_rejects_garbage_and_bit_flip_retained_state()
{
    core::FaultLog<4> log;
    core::FaultEvent event = {};

    log.overwriteRetainedStateWithGarbageForTest(0xC05A1EEDUL);

    TEST_ASSERT_FALSE(log.recoverRetainedState());
    TEST_ASSERT_EQUAL_size_t(0U, log.size());
    TEST_ASSERT_EQUAL_UINT32(0U, log.totalEvents());
    TEST_ASSERT_FALSE(log.latest(event));

    TEST_ASSERT_TRUE(log.record(core::FaultEventType::WatchdogTimeout,
                                500U,
                                7U,
                                0xCAFEU,
                                0U));
    TEST_ASSERT_TRUE(log.recoverRetainedState());

    log.corruptRetainedStateForTest();

    TEST_ASSERT_FALSE(log.recoverRetainedState());
    TEST_ASSERT_EQUAL_size_t(0U, log.size());
    TEST_ASSERT_EQUAL_UINT32(0U, log.totalEvents());
    TEST_ASSERT_FALSE(log.read(0U, event));
}

void test_watchdog_blocks_refresh_for_single_starved_critical_task()
{
    test_mocks::MockTiming timing;
    core::FaultLog<> log;
    core::TaskHealthRegistry<4> registry;
    SafeFailCounter safeFailCounter = {0U};
    HardwareRefreshCounter refreshCounter = {0U};
    core::Watchdog<4> watchdog(timing,
                               registry,
                               log,
                               countSafeFail,
                               &safeFailCounter,
                               countHardwareRefresh,
                               &refreshCounter);
    core::FaultEvent event = {};

    TEST_ASSERT_TRUE(registry.registerTask(1U, 100U, true, timing.getSystemTick()));
    TEST_ASSERT_TRUE(registry.registerTask(2U, 100U, true, timing.getSystemTick()));
    TEST_ASSERT_TRUE(registry.registerTask(3U, 100U, true, timing.getSystemTick()));
    TEST_ASSERT_TRUE(registry.areAllCriticalTasksHealthy());

    timing.delayMs(50U);
    TEST_ASSERT_TRUE(registry.checkIn(1U, timing.getSystemTick()));
    TEST_ASSERT_TRUE(registry.checkIn(2U, timing.getSystemTick()));
    TEST_ASSERT_TRUE(registry.checkIn(3U, timing.getSystemTick()));
    (void)watchdog.poll();
    TEST_ASSERT_EQUAL_UINT32(1U, refreshCounter.count);

    timing.delayMs(101U);
    TEST_ASSERT_TRUE(registry.checkIn(1U, timing.getSystemTick()));
    TEST_ASSERT_TRUE(registry.checkIn(3U, timing.getSystemTick()));

    const core::TaskHealthEvaluation result = watchdog.poll();

    TEST_ASSERT_EQUAL_INT(static_cast<int>(core::TaskHealthStatus::CriticalFailure),
                          static_cast<int>(result.status));
    TEST_ASSERT_EQUAL_UINT8(2U, result.firstFailedTaskId);
    TEST_ASSERT_FALSE(registry.areAllCriticalTasksHealthy());
    TEST_ASSERT_EQUAL_UINT32(1U, refreshCounter.count);
    TEST_ASSERT_EQUAL_UINT32(1U, safeFailCounter.count);
    TEST_ASSERT_EQUAL_size_t(3U, log.size());
    TEST_ASSERT_TRUE(log.latest(event));
    TEST_ASSERT_EQUAL_INT(static_cast<int>(core::FaultEventType::SafeFail),
                          static_cast<int>(event.type));
}

void test_health_summary_mask_critical_sections_under_interleaving()
{
    core::TaskHealthRegistry<4> registry;
    core::FaultLog<4> log;
    constexpr uint32_t ExpectedHealthyMask = (1UL << 1U) | (1UL << 2U);

    resetCriticalProbe();
    TEST_ASSERT_TRUE(registry.registerTask(1U, 1000U, true, 0U));
    TEST_ASSERT_TRUE(registry.registerTask(2U, 1000U, true, 0U));
    TEST_ASSERT_TRUE(registry.registerTask(3U, 10U, false, 0U));

    for (uint32_t i = 0U; i < 512U; ++i)
    {
        const uint64_t nowMs = static_cast<uint64_t>(i + 1U);
        TEST_ASSERT_TRUE(registry.checkIn(1U, nowMs));
        TEST_ASSERT_TRUE(registry.checkIn(2U, nowMs));

        if ((i & 1U) == 0U)
        {
            (void)registry.evaluate(nowMs + 20U, log);
        }
        else
        {
            TEST_ASSERT_TRUE(registry.checkIn(3U, nowMs));
        }

        const uint32_t mask = registry.healthSummaryMask();
        TEST_ASSERT_EQUAL_UINT32(ExpectedHealthyMask, mask & ExpectedHealthyMask);
        TEST_ASSERT_EQUAL_UINT32(0U, mask & ~(ExpectedHealthyMask | (1UL << 3U)));
        TEST_ASSERT_FALSE(criticalProbe.underflow);
        TEST_ASSERT_EQUAL_UINT32(criticalProbe.enterCount, criticalProbe.exitCount);
        TEST_ASSERT_EQUAL_UINT32(0U, criticalProbe.depth);
    }

    TEST_ASSERT_TRUE(criticalProbe.enterCount >= (512U * 3U));
    TEST_ASSERT_TRUE(criticalProbe.maxDepth >= 1U);
}

void test_boot_task_start_failure_records_safefail_and_recovery()
{
    core::FaultLog<4> log;
    BootRecoveryCounter recoveryCounter = {0U};
    core::FaultEvent event = {};

    TEST_ASSERT_FALSE(core::handleBootTaskStartFailure(false,
                                                       log,
                                                       42U,
                                                       countBootRecovery,
                                                       &recoveryCounter));
    TEST_ASSERT_EQUAL_UINT32(1U, recoveryCounter.count);
    TEST_ASSERT_EQUAL_size_t(1U, log.size());
    TEST_ASSERT_EQUAL_UINT32(1U, log.totalEvents());
    TEST_ASSERT_TRUE(log.latest(event));
    TEST_ASSERT_EQUAL_INT(static_cast<int>(core::FaultEventType::SafeFail),
                          static_cast<int>(event.type));
    TEST_ASSERT_EQUAL_UINT64(42U, event.timestampMs);

    TEST_ASSERT_TRUE(core::handleBootTaskStartFailure(true,
                                                      log,
                                                      100U,
                                                      countBootRecovery,
                                                      &recoveryCounter));
    TEST_ASSERT_EQUAL_UINT32(1U, recoveryCounter.count);
    TEST_ASSERT_EQUAL_size_t(1U, log.size());
}

void test_sitl_runtime_nominal_tasks_check_in_without_watchdog_intervention()
{
    test_mocks::SitlRuntime runtime;

    TEST_ASSERT_TRUE(runtime.initialize());

    for (uint32_t i = 0; i < 20U; ++i)
    {
        runtime.runNominalCycle(500U);
        TEST_ASSERT_TRUE(runtime.registry.isHealthy(test_mocks::SitlHeartbeatTaskId));
        TEST_ASSERT_TRUE(runtime.registry.isHealthy(test_mocks::SitlTelemetryTaskId));
        TEST_ASSERT_FALSE(runtime.safeFailState.fatalPanic);
        TEST_ASSERT_EQUAL_UINT32(0U, runtime.safeFailState.resetCount);
    }

    TEST_ASSERT_EQUAL_UINT32(20U, runtime.heartbeatTask.count());
    TEST_ASSERT_EQUAL_UINT32(20U, runtime.telemetryTask.count());
    TEST_ASSERT_EQUAL_size_t(0U, runtime.faultLog.size());
}

void test_sitl_runtime_stalled_telemetry_triggers_safe_fail()
{
    test_mocks::SitlRuntime runtime;
    core::FaultEvent event = {};

    TEST_ASSERT_TRUE(runtime.initialize());
    runtime.runNominalCycle(500U);
    runtime.runCycleWithTelemetryStalled(800U);

    TEST_ASSERT_TRUE(runtime.registry.isHealthy(test_mocks::SitlHeartbeatTaskId));
    TEST_ASSERT_FALSE(runtime.registry.isHealthy(test_mocks::SitlTelemetryTaskId));
    TEST_ASSERT_TRUE(runtime.safeFailState.fatalPanic);
    TEST_ASSERT_EQUAL_UINT32(1U, runtime.safeFailState.resetCount);
    TEST_ASSERT_EQUAL_size_t(3U, runtime.faultLog.size());
    TEST_ASSERT_TRUE(runtime.faultLog.latest(event));
    TEST_ASSERT_EQUAL_INT(static_cast<int>(core::FaultEventType::SafeFail),
                          static_cast<int>(event.type));
    TEST_ASSERT_EQUAL_UINT8(test_mocks::SitlTelemetryTaskId, event.taskId);

    runtime.runCycleWithTelemetryStalled(800U);
    TEST_ASSERT_EQUAL_UINT32(1U, runtime.safeFailState.resetCount);
    TEST_ASSERT_EQUAL_size_t(3U, runtime.faultLog.size());
}

void test_telemetry_frame_nominal_packing_and_crc()
{
    core::TaskHealthRegistry<> registry;
    core::FaultLog<> faultLog;
    core::TelemetryFrame frame = {};
    uint8_t buffer[core::TelemetryFrameWireSize] = {};
    std::size_t length = 0U;

    TEST_ASSERT_TRUE(registry.registerTask(test_mocks::SitlHeartbeatTaskId, 1200U, true, 0U));
    TEST_ASSERT_TRUE(registry.registerTask(test_mocks::SitlTelemetryTaskId, 700U, true, 0U));
    TEST_ASSERT_TRUE(faultLog.record(core::FaultEventType::AssertFailure,
                                     99U,
                                     test_mocks::SitlTelemetryTaskId,
                                     0x55AAU,
                                     0U));

    TEST_ASSERT_TRUE(core::buildTelemetryFrame(42U, 1234U, registry, faultLog, frame));
    TEST_ASSERT_TRUE(core::serializeTelemetryFrame(frame, buffer, sizeof(buffer), length));

    TEST_ASSERT_EQUAL_size_t(core::TelemetryFrameWireSize, sizeof(core::TelemetryFrame));
    TEST_ASSERT_EQUAL_size_t(core::TelemetryFrameWireSize, length);
    TEST_ASSERT_EQUAL_UINT8(core::TelemetrySync0, buffer[0]);
    TEST_ASSERT_EQUAL_UINT8(core::TelemetrySync1, buffer[1]);
    TEST_ASSERT_EQUAL_UINT8(core::TelemetryVersion, buffer[2]);
    TEST_ASSERT_EQUAL_UINT8(core::TelemetryFrameWireSize, buffer[3]);
    TEST_ASSERT_EQUAL_UINT32(42U, core::readU32Le(buffer, 4U));
    TEST_ASSERT_EQUAL_UINT32(1234U, core::readU32Le(buffer, 8U));
    TEST_ASSERT_EQUAL_UINT32((1UL << test_mocks::SitlHeartbeatTaskId) |
                             (1UL << test_mocks::SitlTelemetryTaskId),
                             core::readU32Le(buffer, 12U));
    TEST_ASSERT_EQUAL_UINT32(1U, core::readU32Le(buffer, 16U));
    TEST_ASSERT_EQUAL_UINT8(static_cast<uint8_t>(core::FaultEventType::AssertFailure),
                            buffer[20]);
    TEST_ASSERT_EQUAL_UINT8(test_mocks::SitlTelemetryTaskId, buffer[21]);
    TEST_ASSERT_TRUE(core::validateTelemetryBuffer(buffer, length));
    TEST_ASSERT_EQUAL_UINT32(core::crc32(buffer, core::TelemetryFrameWireSize - sizeof(uint32_t)),
                             core::readU32Le(buffer, 24U));
}

void test_telemetry_crc_detects_corruption()
{
    core::TaskHealthRegistry<> registry;
    core::FaultLog<> faultLog;
    core::TelemetryFrame frame = {};
    uint8_t buffer[core::TelemetryFrameWireSize] = {};
    std::size_t length = 0U;

    TEST_ASSERT_TRUE(registry.registerTask(test_mocks::SitlHeartbeatTaskId, 1200U, true, 0U));
    TEST_ASSERT_TRUE(core::buildTelemetryFrame(7U, 800U, registry, faultLog, frame));
    TEST_ASSERT_TRUE(core::serializeTelemetryFrame(frame, buffer, sizeof(buffer), length));
    TEST_ASSERT_TRUE(core::validateTelemetryBuffer(buffer, length));

    buffer[6] ^= 0x01U;
    TEST_ASSERT_FALSE(core::validateTelemetryBuffer(buffer, length));
}

void test_sitl_runtime_telemetry_task_emits_real_frames()
{
    test_mocks::SitlRuntime runtime;
    uint8_t firstFrame[core::TelemetryFrameWireSize] = {};
    uint8_t secondFrame[core::TelemetryFrameWireSize] = {};

    TEST_ASSERT_TRUE(runtime.initialize());
    runtime.runNominalCycle(500U);
    runtime.runNominalCycle(500U);

    TEST_ASSERT_EQUAL_size_t(core::TelemetryFrameWireSize * 2U,
                             runtime.telemetryTransport.txAvailable());
    TEST_ASSERT_TRUE(runtime.telemetryTransport.readTx(firstFrame, sizeof(firstFrame)));
    TEST_ASSERT_TRUE(runtime.telemetryTransport.readTx(secondFrame, sizeof(secondFrame)));
    TEST_ASSERT_TRUE(core::validateTelemetryBuffer(firstFrame, sizeof(firstFrame)));
    TEST_ASSERT_TRUE(core::validateTelemetryBuffer(secondFrame, sizeof(secondFrame)));
    TEST_ASSERT_EQUAL_UINT32(0U, core::readU32Le(firstFrame, 4U));
    TEST_ASSERT_EQUAL_UINT32(1U, core::readU32Le(secondFrame, 4U));
    TEST_ASSERT_EQUAL_UINT32(500U, core::readU32Le(firstFrame, 8U));
    TEST_ASSERT_EQUAL_UINT32(1000U, core::readU32Le(secondFrame, 8U));
}

} /* namespace */

namespace core
{

void testEnterCriticalSection()
{
    ++criticalProbe.enterCount;
    ++criticalProbe.depth;
    if (criticalProbe.depth > criticalProbe.maxDepth)
    {
        criticalProbe.maxDepth = criticalProbe.depth;
    }
}

void testExitCriticalSection()
{
    if (criticalProbe.depth == 0U)
    {
        criticalProbe.underflow = true;
        return;
    }

    --criticalProbe.depth;
    ++criticalProbe.exitCount;
}

} /* namespace core */

int main()
{
    UNITY_BEGIN();
    RUN_TEST(test_gpio_interrupt_and_app_logic);
    RUN_TEST(test_uart_rx_tx_and_timeout);
    RUN_TEST(test_i2c_timeout_and_nominal_read_write);
    RUN_TEST(test_spi_transfer_and_timeout);
    RUN_TEST(test_can_loopback_and_error_state);
    RUN_TEST(test_adc_raw_voltage_and_timeout);
    RUN_TEST(test_pwm_channel_state);
    RUN_TEST(test_tmr_clean_read_logs_no_fault);
    RUN_TEST(test_tmr_repairs_corrupted_copies);
    RUN_TEST(test_tmr_unrecoverable_uses_deterministic_fallback);
    RUN_TEST(test_watchdog_allows_healthy_task);
    RUN_TEST(test_watchdog_critical_timeout_safe_fails_once);
    RUN_TEST(test_watchdog_noncritical_timeout_logs_without_safe_fail);
    RUN_TEST(test_fault_log_wraps_deterministically);
    RUN_TEST(test_fault_log_rejects_garbage_and_bit_flip_retained_state);
    RUN_TEST(test_watchdog_blocks_refresh_for_single_starved_critical_task);
    RUN_TEST(test_health_summary_mask_critical_sections_under_interleaving);
    RUN_TEST(test_boot_task_start_failure_records_safefail_and_recovery);
    RUN_TEST(test_sitl_runtime_nominal_tasks_check_in_without_watchdog_intervention);
    RUN_TEST(test_sitl_runtime_stalled_telemetry_triggers_safe_fail);
    RUN_TEST(test_telemetry_frame_nominal_packing_and_crc);
    RUN_TEST(test_telemetry_crc_detects_corruption);
    RUN_TEST(test_sitl_runtime_telemetry_task_emits_real_frames);
    return UNITY_END();
}
