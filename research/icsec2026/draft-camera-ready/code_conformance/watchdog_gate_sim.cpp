// Code-level conformance check of the watchdog gate (DRAFT-CAMERA-READY, 2026-10-18).
//
// Executes the REAL core::TaskHealthRegistry, core::Watchdog, core::WatchdogRunner and core::FaultLog
// (core/include/core/) against a tick-level simulation of the three FreeRTOS tasks of the payload-demo build
// (core/src/main.cpp:66-80, :252-258):
//   HeartbeatTask    checkIn(); vTaskDelay(500)                     (src/app/HeartbeatTask.hpp:37-45)
//   PayloadLinkTask  1 ms loop, checkIn() once nowMs >= nextHealthMs, nextHealthMs = nowMs + 100
//                    (src/app/PayloadLinkTask.hpp:171-178)
//   WatchdogTask     runner.runOnce(); vTaskDelay(50); runner polls when >= 100 ms elapsed
//                    (src/app/WatchdogTask.hpp:24-30, include/core/WatchdogRunner.hpp:25-35); highest priority
// Deadlines 1500 ms (heartbeat) and 800 ms (payload link), both critical. The IWDG resets the board when
// the time since the last refresh reaches its period, swept over the datasheet bracket {1882, 2170} ms.
// Each wake-up is late by a latency in [0, J] (J = 2 ms), the model's assumption A1.
//
// Checked (paper property names): W1 no stall -> never a critical failure and never an IWDG reset;
// W2 no refresh after a critical failure is recorded; W3 stall detected within deadline + 100 + 50 + J
// (952 ms link, 1652 ms heartbeat) from the stall instant; W6 IWDG reset within W3 bound + 2170 ms.

#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <random>

#include "FaultLog.hpp"
#include "TaskHealth.hpp"
#include "Watchdog.hpp"
#include "WatchdogRunner.hpp"

namespace
{

using us_t = int64_t;
constexpr us_t MS = 1000;

struct Clock final : public hal::ITiming
{
    us_t now = 0;
    uint64_t getSystemTick() const noexcept override { return static_cast<uint64_t>(now / MS); }
    void delayMs(uint32_t) noexcept override {}
    void delayUs(uint32_t) noexcept override {}
};

struct Iwdg
{
    us_t lastRefresh = 0;
    us_t refreshesAfterFailure = 0;
    bool failureRecorded = false;
};

void onRefresh(void* ctx)
{
    auto* p = static_cast<std::pair<Iwdg*, Clock*>*>(ctx);
    p->first->lastRefresh = p->second->now;
    if (p->first->failureRecorded) ++p->first->refreshesAfterFailure;
}

void onSafeFail(void* ctx) { static_cast<Iwdg*>(ctx)->failureRecorded = true; }

struct Outcome
{
    double detectMs = -1, resetMs = -1;
    bool failure = false, reset = false;
    long refreshAfterFailure = 0;
};

// stallTask: 0 none, 1 heartbeat, 2 payload link
Outcome run(int stallTask, us_t stallAt, us_t iwdgPeriod, us_t jMax, us_t horizon, std::mt19937_64& rng)
{
    Clock clock;
    core::FaultLog<> log;
    log.recoverRetainedState();
    core::TaskHealthRegistry<> reg;
    Iwdg iwdg;
    std::pair<Iwdg*, Clock*> ctx{&iwdg, &clock};
    reg.registerTask(1U, 1500U, true, 0U);
    reg.registerTask(2U, 800U, true, 0U);
    core::Watchdog<> wd(clock, reg, log, onSafeFail, &iwdg, onRefresh, &ctx);
    core::WatchdogRunner<> runner(clock, wd, 100U);

    auto lat = [&]() -> us_t {
        if (jMax == 0) return 0;
        const int k = std::uniform_int_distribution<int>(0, 3)(rng);
        return k == 0 ? 0 : k == 1 ? jMax : std::uniform_int_distribution<us_t>(0, jMax)(rng);
    };
    // phases of the three tasks relative to the scheduler start
    us_t tHb = std::uniform_int_distribution<us_t>(0, 3)(rng) * MS + lat();
    us_t tPl = std::uniform_int_distribution<us_t>(0, 3)(rng) * MS + lat();
    us_t tWd = std::uniform_int_distribution<us_t>(0, 3)(rng) * MS + lat();
    uint32_t nextHealthMs = 0;
    Outcome o;
    us_t failureAt = -1;
    while (true)
    {
        // highest priority first on ties: watchdog, payload link, heartbeat
        us_t t = std::min({tWd, tPl, tHb});
        if (t > horizon) break;
        clock.now = t;
        if (iwdg.lastRefresh + iwdgPeriod <= t)   // the IWDG counts independently of the tasks
        {
            o.reset = true;
            o.resetMs = (iwdg.lastRefresh + iwdgPeriod - stallAt) / 1000.0;
            break;
        }
        if (t == tWd)
        {
            const bool failedBefore = iwdg.failureRecorded;
            runner.runOnce();
            if (!failedBefore && iwdg.failureRecorded) failureAt = t;
            tWd = ((t + 50 * MS) / MS) * MS + lat();
        }
        else if (t == tPl)
        {
            const uint32_t nowMs = static_cast<uint32_t>(t / MS);
            const bool stalled = stallTask == 2 && t >= stallAt;
            if (!stalled && static_cast<int32_t>(nowMs - nextHealthMs) >= 0)
            {
                reg.checkIn(2U, nowMs);
                nextHealthMs = nowMs + 100U;
            }
            tPl = (t / MS + 1) * MS + lat();
        }
        else
        {
            const bool stalled = stallTask == 1 && t >= stallAt;
            if (!stalled) reg.checkIn(1U, static_cast<uint64_t>(t / MS));
            tHb = ((t + 500 * MS) / MS) * MS + lat();
        }
    }
    o.failure = failureAt >= 0;
    if (o.failure) o.detectMs = (failureAt - stallAt) / 1000.0;
    o.refreshAfterFailure = iwdg.refreshesAfterFailure;
    return o;
}

}  // namespace

int main(int argc, char** argv)
{
    const int scale = argc > 1 ? std::atoi(argv[1]) : 1;
    const us_t J = 2 * MS;
    std::mt19937_64 rng(20261018ULL);
    int failures = 0;

    // W1: no stall, 120 s, both IWDG extremes
    {
        long fail = 0, resets = 0;
        for (int i = 0; i < 200 * scale; ++i)
            for (us_t period : {1882 * MS, 2170 * MS})
            {
                const Outcome o = run(0, 0, period, J, 120000 * MS, rng);
                fail += o.failure; resets += o.reset;
            }
        std::printf("W1 no stall (%d x 2 runs of 120 s): critical failures %ld, IWDG resets %ld -> %s\n",
                    200 * scale, fail, resets, (fail == 0 && resets == 0) ? "HOLD" : "VIOLATED");
        failures += (fail != 0 || resets != 0);
    }
    // W2/W3/W6: stall at every 1 ms phase over 1 s after a 3 s warm-up, per task, per IWDG extreme
    struct Task { int id; const char* name; double w3; };
    for (Task task : {Task{2, "payload-link", 952.0}, Task{1, "heartbeat", 1652.0}})
        for (us_t period : {1882 * MS, 2170 * MS})
        {
            double maxDetect = -1, maxReset = -1;
            long noDetect = 0, noReset = 0, refreshAfter = 0, runs = 0;
            for (int rep = 0; rep < scale; ++rep)
                for (us_t phase = 0; phase < 1000 * MS; phase += 1 * MS / (rep % 2 ? 4 : 1))
                {
                    const us_t stallAt = 3000 * MS + phase;
                    const Outcome o = run(task.id, stallAt, period, J, stallAt + 6000 * MS, rng);
                    ++runs;
                    if (!o.failure) ++noDetect; else maxDetect = std::max(maxDetect, o.detectMs);
                    if (!o.reset) ++noReset; else maxReset = std::max(maxReset, o.resetMs);
                    refreshAfter += o.refreshAfterFailure;
                }
            const bool ok = noDetect == 0 && noReset == 0 && refreshAfter == 0 &&
                            maxDetect <= task.w3 && maxReset <= task.w3 + 2170.0;
            failures += !ok;
            std::printf("%-12s IWDG %4lld ms: runs %ld, max detect %.3f ms (W3 %.0f), max reset %.3f ms (W6 %.0f), "
                        "refresh after failure %ld, undetected %ld, no reset %ld -> %s\n",
                        task.name, static_cast<long long>(period / MS), runs, maxDetect, task.w3, maxReset,
                        task.w3 + 2170.0, refreshAfter, noDetect, noReset, ok ? "HOLD" : "VIOLATED");
        }
    std::printf("failures=%d\n", failures);
    return failures == 0 ? 0 : 1;
}
