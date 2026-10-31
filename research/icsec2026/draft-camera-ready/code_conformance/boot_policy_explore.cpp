// Explicit-state exploration of the REAL boot policy (DRAFT-CAMERA-READY, 2026-10-18).
//
// Runs boot::BootPolicy::run() (bootloader/include/boot/BootPolicy.hpp, BootMetadata.hpp, with the real
// core::FaultLog<> and CRC-32) on every retained-memory state reachable from the provisioned state under the
// environment actions of the UPPAAL boot model (formal/models/boot_policy.xml, templates App and Flash):
//
//   App   (while the application runs): clean warm reset; critical stall -> FaultLog WatchdogTimeout + reset;
//         confirm boot (design variant only; the shipped application never writes boot metadata, F1).
//   Flash (while running or in the safe loop): corrupt image A; corrupt image B; stage a Pending image in B;
//         activate B (active = B, boot_count = 0); corrupt the metadata record; cold start (retained SRAM lost).
//
// Abstraction (the only one): a pre-boot boot_count above 5 is clamped to 5. The policy only compares
// boot_count with MaxUnconfirmedBootAttempts = 3 and increments it, so every value above 3 behaves alike;
// without the clamp a Confirmed slot that warm-resets forever makes the state space infinite.
//
// Checked on every boot (property names as in the paper): B1 never launch an image whose bytes do not match
// what was provisioned; B2 never launch a slot whose state is not bootable; B3 at most 4 consecutive launches
// of a Pending slot; B4 no intact image -> safe loop; B6 retained critical fault -> no launch; B8 a Pending
// slot is never launched with boot_count already above the limit (B8b: on which path); B9 every boot ends in
// exactly one of launch / safe loop; F1 whether slot B ever becomes Confirmed.
//
// Compile once against the working tree (F4 fix) and once against the pre-fix headers (see run_all.sh).

#include <cstdint>
#include <cstdio>
#include <cstring>
#include <deque>
#include <set>
#include <string>
#include <vector>

#include "boot/BootMetadata.hpp"
#include "boot/BootPolicy.hpp"
#include "hal/IBootPlatform.hpp"
#include "hal/IBeacon.hpp"
#include "hal/IFlashMap.hpp"

namespace
{

constexpr std::size_t SlotLength = 64U;
uint8_t flashA[SlotLength], flashB[SlotLength];
uint8_t imageA[SlotLength], imageB[SlotLength];

struct FlashMap final : public hal::IFlashMap
{
    bool vecA = true, vecB = true;
    uintptr_t slotBase(hal::FirmwareSlot s) const override { return reinterpret_cast<uintptr_t>(s == hal::FirmwareSlot::SlotB ? flashB : flashA); }
    std::size_t slotLength(hal::FirmwareSlot) const override { return SlotLength; }
    bool isSlotVectorValid(hal::FirmwareSlot s) const override { return s == hal::FirmwareSlot::SlotB ? vecB : vecA; }
    uintptr_t applicationBase() const override { return slotBase(hal::FirmwareSlot::SlotA); }
    std::size_t applicationLength() const override { return SlotLength; }
    uintptr_t ramBase() const override { return 0x20000000UL; }
    std::size_t ramLength() const override { return 32UL * 1024UL; }
    bool isApplicationVectorValid() const override { return vecA; }
};

struct Platform final : public hal::IBootPlatform
{
    uintptr_t jumped = 0U;
    void prepareForApplicationJump() override {}
    void jumpToApplication(uintptr_t v) override { jumped = v; }
};

struct Beacon final : public hal::IBeacon
{
    uint32_t loops = 0U;
    void enterSafeLoop() override { ++loops; }
};

// Pre-boot state: retained RAM + flash contents + one history counter for B3.
struct State
{
    boot::BootMetadata md;
    core::FaultLog<> log;
    bool intactA, intactB, bWritten;
    uint8_t pendingRun;   // consecutive launches of a Pending slot
    bool coldStarted;     // retained memory lost (metadata and fault log are garbage)
};

uint32_t defaultCrc() { return boot::crc32(imageA, SlotLength); }

std::string key(State& s)
{
    std::string k;
    auto put = [&k](const void* p, std::size_t n) { k.append(static_cast<const char*>(p), n); };
    put(&s.md, sizeof(s.md));
    const uint32_t n = static_cast<uint32_t>(s.log.size());
    put(&n, sizeof(n));
    for (std::size_t i = 0; i < s.log.size(); ++i)
    {
        core::FaultEvent e = {};
        s.log.read(i, e);
        put(&e.type, sizeof(e.type));
    }
    const uint8_t flags[] = {s.intactA, s.intactB, s.bWritten, s.pendingRun, s.coldStarted};
    put(flags, sizeof(flags));
    return k;
}

bool hasCriticalFault(State& s)
{
    for (std::size_t i = 0; i < s.log.size(); ++i)
    {
        core::FaultEvent e = {};
        if (!s.log.read(i, e)) return true;
        if (e.type == core::FaultEventType::TaskCheckinFailure || e.type == core::FaultEventType::WatchdogTimeout) return true;
    }
    return false;
}

struct Report
{
    long states = 0, boots = 0, launches = 0, safeLoops = 0;
    long b1 = 0, b2 = 0, b3 = 0, b4 = 0, b6 = 0, b8 = 0, b8Fallback = 0, b8Primary = 0, b9 = 0;
    bool slotBConfirmedReachable = false;
    long maxPendingRun = 0;
};

void loadFlash(const State& s)
{
    std::memcpy(flashA, imageA, SlotLength);
    if (!s.intactA) flashA[0] ^= 0xFFU;
    std::memset(flashB, 0xFF, SlotLength);
    if (s.bWritten)
    {
        std::memcpy(flashB, imageB, SlotLength);
        if (!s.intactB) flashB[0] ^= 0xFFU;
    }
}

}  // namespace

int main(int argc, char** argv)
{
    const bool appConfirms = argc > 1 && std::strcmp(argv[1], "design") == 0;
    for (std::size_t i = 0; i < SlotLength; ++i) { imageA[i] = static_cast<uint8_t>(1 + i); imageB[i] = static_cast<uint8_t>(101 + 3 * i); }

    // First power-up: retained SRAM modelled as all-zero bytes (as in the cold-start action below), so the
    // real FaultLog classifies it as a cold start. A default-constructed FaultLog would instead classify
    // as Corrupt and every boot would safe-fail -- the vacuity guard at the end catches that case.
    State init{};
    std::memset(static_cast<void*>(&init.md), 0, sizeof(init.md));
    std::memset(static_cast<void*>(&init.log), 0, sizeof(init.log));
    init.intactA = true;
    init.coldStarted = true;   // first power-up: retained RAM holds no valid record
    std::deque<State> queue{init};
    std::set<std::string> seen;
    Report r;

    while (!queue.empty())
    {
        State s = queue.front();
        queue.pop_front();
        if (s.md.boot_count > 5U && boot::hasValidBootMetadata(s.md)) { s.md.boot_count = 5U; boot::commitBootMetadata(s.md); }
        if (!seen.insert(key(s)).second) continue;
        ++r.states;

        // ---- one boot of the real policy ----
        State post = s;
        loadFlash(post);
        FlashMap flash;
        flash.vecA = post.intactA;
        flash.vecB = post.bWritten && post.intactB;
        Platform platform;
        Beacon beacon;
        const bool priorCritical = !s.coldStarted && hasCriticalFault(s);
        const uint32_t activeBefore = boot::hasValidBootMetadata(s.md) ? s.md.active_slot : 0U;
        boot::BootPolicy policy(flash, platform, beacon, post.md, post.log, defaultCrc(), SlotLength);
        policy.run();
        post.coldStarted = false;
        ++r.boots;

        const bool launched = platform.jumped != 0U;
        const bool safe = beacon.loops > 0U;
        if (launched == safe) ++r.b9;
        if (!s.intactA && !(s.bWritten && s.intactB) && !safe) ++r.b4;
        if (post.md.slot_b_state == static_cast<uint32_t>(boot::FirmwareSlotState::Confirmed)) r.slotBConfirmedReachable = true;

        std::vector<State> next;
        if (launched)
        {
            ++r.launches;
            const bool isB = platform.jumped == reinterpret_cast<uintptr_t>(flashB);
            const uint32_t st = isB ? post.md.slot_b_state : post.md.slot_a_state;
            if (!(isB ? (post.bWritten && post.intactB) : post.intactA)) ++r.b1;
            if (!boot::isBootableFirmwareSlotState(st)) ++r.b2;
            if (priorCritical) ++r.b6;
            const bool pending = st == static_cast<uint32_t>(boot::FirmwareSlotState::Pending);
            post.pendingRun = pending ? static_cast<uint8_t>(post.pendingRun + 1U) : 0U;
            if (post.pendingRun > r.maxPendingRun) r.maxPendingRun = post.pendingRun;
            if (post.pendingRun > 4U) ++r.b3;
            if (pending && post.md.boot_count > boot::MaxUnconfirmedBootAttempts + 1U)
            {
                ++r.b8;
                const bool viaFallback = (isB ? 1U : 0U) != activeBefore;
                if (viaFallback) ++r.b8Fallback; else ++r.b8Primary;
            }

            // App actions (then a warm reset)
            next.push_back(post);                                          // clean reset
            State stall = post;
            stall.log.record(core::FaultEventType::WatchdogTimeout, 0U, 2U, 0U, 0U);
            next.push_back(stall);                                         // critical stall -> IWDG reset
            if (appConfirms)
            {
                State conf = post;
                conf.md.confirmed_flag = boot::BootMetadataConfirmed;
                boot::commitBootMetadata(conf.md);
                conf.pendingRun = 0U;
                next.push_back(conf);
            }
            // Flash actions while running (then a warm reset)
            State a = post; a.intactA = false; next.push_back(a);
            if (post.bWritten) { State b = post; b.intactB = false; next.push_back(b); }
            State stage = post;
            stage.bWritten = true; stage.intactB = true;
            stage.md.slot_b_crc32 = boot::crc32(imageB, SlotLength);
            stage.md.slot_b_state = static_cast<uint32_t>(boot::FirmwareSlotState::Pending);
            boot::commitBootMetadata(stage.md);
            stage.pendingRun = 0U;
            next.push_back(stage);
            if (post.md.slot_b_state == static_cast<uint32_t>(boot::FirmwareSlotState::Pending))
            {
                State act = post;
                act.md.active_slot = static_cast<uint32_t>(boot::BootSlot::SlotB);
                act.md.boot_count = 0U;
                boot::commitBootMetadata(act.md);
                act.pendingRun = 0U;
                next.push_back(act);
            }
            State corrupt = post; corrupt.md.checksum ^= 0x1U; next.push_back(corrupt);
        }
        else
        {
            ++r.safeLoops;   // the safe loop only leaves through a cold start (below)
        }
        // Cold start from either outcome: retained SRAM lost, flash kept.
        State cold = post;
        std::memset(&cold.md, 0, sizeof(cold.md));
        std::memset(static_cast<void*>(&cold.log), 0, sizeof(cold.log));
        cold.pendingRun = 0U;
        cold.coldStarted = true;
        next.push_back(cold);
        if (!launched)
        {
            State coldA = cold; coldA.intactA = false; next.push_back(coldA);
            if (cold.bWritten) { State coldB = cold; coldB.intactB = false; next.push_back(coldB); }
        }
        for (State& n : next) queue.push_back(n);
    }

    std::printf("variant=%s states=%ld boots=%ld launches=%ld safeLoops=%ld\n", appConfirms ? "design" : "shipped", r.states, r.boots, r.launches, r.safeLoops);
    std::printf("B1 unvalidated launch: %ld\nB2 non-bootable launch: %ld\nB3 >4 consecutive Pending launches: %ld (max run %ld)\n", r.b1, r.b2, r.b3, r.maxPendingRun);
    std::printf("B4 no intact image but not safe loop: %ld\nB6 launch despite retained critical fault: %ld\n", r.b4, r.b6);
    std::printf("B8 Pending launched over the limit: %ld (fallback path %ld, primary path %ld)\nB9 not exactly one outcome: %ld\n", r.b8, r.b8Fallback, r.b8Primary, r.b9);
    std::printf("F1 slot B Confirmed reachable: %s\n", r.slotBConfirmedReachable ? "yes" : "no");
    // Vacuity guard: the properties mean nothing unless the exploration launched applications, launched a
    // Pending slot and reached both safe loops and fallbacks.
    const bool vacuous = r.launches == 0 || r.maxPendingRun == 0 || r.safeLoops == 0 || r.states < 100;
    if (vacuous) std::printf("VACUOUS exploration: states=%ld launches=%ld maxPendingRun=%ld\n", r.states, r.launches, r.maxPendingRun);
    const bool safetyOk = !vacuous && r.b1 == 0 && r.b2 == 0 && r.b4 == 0 && r.b6 == 0 && r.b9 == 0;
    std::printf("SAFETY(B1,B2,B4,B6,B9)=%s LIMIT(B3,B8)=%s\n", safetyOk ? "HOLD" : "VIOLATED", (r.b3 == 0 && r.b8 == 0) ? "HOLD" : "VIOLATED");
    return safetyOk ? 0 : 1;
}
