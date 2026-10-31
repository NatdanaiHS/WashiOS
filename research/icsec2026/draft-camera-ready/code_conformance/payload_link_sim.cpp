// Code-level conformance check of the payload-link bounds (DRAFT-CAMERA-READY, 2026-10-18).
//
// Executes the REAL controller logic -- comms::PayloadLinkController, comms::PayloadFrameDecoder and the
// frame codec (core/include/comms/), and the responder's HostModeCommandParser (demo-payload/src/) --
// inside a two-process discrete-event simulation with 1 us resolution. The two RTOS/HAL loops are
// re-stated here because they cannot run on the host; each step cites the source line it mirrors:
//
//   controller  core/src/app/PayloadLinkTask.hpp Run() :41-51  receiveFrames -> serviceController ->
//               sendPoll -> reportHealth -> reportStatus -> vTaskDelay(1); every console line and the poll
//               are blocking writes at 115200 8N1 (writeLine, Stm32G4Uart::writeBuffer -> HAL_UART_Transmit).
//   responder   demo-payload/src/main.cpp main() :445-455  serviceHostCommands -> serviceLink ->
//               HAL_Delay(1); handleRequest :298-346 reads currentMode at decode, HAL_Delay(d) in DELAYED,
//               blocking 32-byte transmit; logMode after the mode assignment :245-248.
//
// Assumptions of the simulation (the same ones the UPPAAL model makes): FreeRTOS wake-up latency after a
// tick is at most J (sampled per wake-up); no byte loss; the two boards' tick phases are independent.
// Optional status-report slip (assumption A7): after each PAYLOAD_STATUS line the task stays blocked for an
// extra time drawn from [0, EXTRA] ms, so that the total block (line + extra) stays within SLIP = 60 ms.
//
// Measured, per trial, from the model's clock origins (the payload's mode ASSIGNMENT for fault and
// restoration): first timeout, OFFLINE, recovery; and, for DELAYED, whether any timeout / any delayed
// acceptance occurred in the exposure. Also the host-visible offset: (end of PAYLOAD_RECOVERED line) -
// (end of the [PAYLOAD] MODE=NORMAL line) minus the internal interval.
//
// Build/run: see run_all.sh. Exit status 0 iff no measured value exceeds the model bound of its scenario
// and every delay classification agrees with the model's ACCEPTS / TIMES_OUT predicates.

#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <deque>
#include <random>
#include <string>
#include <vector>

#include "PayloadLinkController.hpp"
#include "PayloadProtocol.hpp"
#include "HostModeCommandParser.hpp"

namespace
{

using us_t = int64_t;
constexpr us_t MS = 1000;
constexpr double BYTE_US = 1e6 * 10.0 / 115200.0;   // 8N1

struct Byte { us_t t; uint8_t v; };

us_t bytesUs(std::size_t n) { return static_cast<us_t>(n * BYTE_US + 0.5); }

struct Config
{
    const char* name;
    comms::PayloadMode fault;
    uint32_t delayMs;
    bool status;          // status reports enabled
    us_t extraMaxUs;      // extra block after each status line (A7)
    us_t jitterMaxUs;     // FreeRTOS wake-up latency bound J
    int trials;
};

struct Result
{
    double firstTimeout = -1, offline = -1, recovery = -1, hostOffset = -1e9;
    int exposureTimeouts = 0, exposureDelayedAccepts = 0;
};

class Sim
{
public:
    Sim(const Config& c, std::mt19937_64& rng) : cfg(c), rng(rng) {}

    Result run()
    {
        payloadPhase = uni(0, MS - 1);
        nextStatusMs = cfg.status ? static_cast<uint32_t>(uni(1, 5000)) : 0xFFFFFFFFu;
        const us_t inject = 1500 * MS + uni(0, 1000 * MS);
        sendCommand(inject, faultCommand());
        us_t end = inject + 10000 * MS;
        tc = 0; tp = payloadPhase;
        while (std::min(tc, tp) < end)
        {
            if (tc <= tp) controllerIteration(); else payloadIteration();
            if (faultAssigned >= 0 && restoreCommandAt < 0)
            {
                restoreCommandAt = faultAssigned + 4000 * MS + uni(0, 50 * MS);
                sendCommand(restoreCommandAt, "MODE NORMAL\n");
            }
            if (restoreAssigned >= 0 && end > restoreAssigned + 3000 * MS) end = restoreAssigned + 3000 * MS;
        }
        Result r;
        if (firstTimeoutAt >= 0) r.firstTimeout = (firstTimeoutAt - faultAssigned) / 1000.0;
        if (offlineAt >= 0) r.offline = (offlineAt - faultAssigned) / 1000.0;
        if (recoveryAt >= 0)
        {
            r.recovery = (recoveryAt - restoreAssigned) / 1000.0;
            r.hostOffset = ((recoveryLineEnd - restoreConfirmEnd) - (recoveryAt - restoreAssigned)) / 1000.0;
        }
        r.exposureTimeouts = exposureTimeouts;
        r.exposureDelayedAccepts = exposureDelayedAccepts;
        return r;
    }

private:
    const Config& cfg;
    std::mt19937_64& rng;
    std::deque<Byte> toPayload, toController, toPayloadDebug;

    // controller (PayloadLinkTask) state
    comms::PayloadLinkController ctl;
    comms::PayloadFrameDecoder ctlDecoder;
    comms::PayloadValidationResult lastRejection = comms::PayloadValidationResult::Ok;
    uint32_t nextStatusMs = 5000;
    us_t tc = 0;

    // responder (demo-payload main) state
    comms::PayloadFrameDecoder reqDecoder;
    HostModeCommandParser parser;
    comms::PayloadMode mode = comms::PayloadMode::Normal;
    uint32_t delayMs = 250;
    uint32_t sampleCounter = 0;
    us_t tp = 0, payloadPhase = 0;

    // observations
    us_t faultAssigned = -1, restoreAssigned = -1, restoreCommandAt = -1, restoreConfirmEnd = -1;
    us_t firstTimeoutAt = -1, offlineAt = -1, recoveryAt = -1, recoveryLineEnd = -1;
    int exposureTimeouts = 0, exposureDelayedAccepts = 0;

    us_t uni(us_t lo, us_t hi) { return std::uniform_int_distribution<us_t>(lo, hi)(rng); }

    std::string faultCommand() const
    {
        switch (cfg.fault)
        {
        case comms::PayloadMode::Silent: return "MODE SILENT\n";
        case comms::PayloadMode::BadCrc: return "MODE BAD_CRC\n";
        default: return "MODE DELAYED " + std::to_string(cfg.delayMs) + "\n";
        }
    }

    void sendCommand(us_t at, const std::string& text)
    {
        for (std::size_t i = 0; i < text.size(); ++i)
            toPayloadDebug.push_back({at + bytesUs(i + 1), static_cast<uint8_t>(text[i])});
    }

    bool inExposure(us_t t) const { return faultAssigned >= 0 && t >= faultAssigned && (restoreAssigned < 0 || t < restoreAssigned); }

    // ---- controller: PayloadLinkTask::Run() one loop pass ----
    void controllerIteration()
    {
        us_t cur = tc;
        const uint32_t nowMs = static_cast<uint32_t>(tc / MS);   // timing.getSystemTick() at :44
        // receiveFrames(nowMs) :82-125
        for (std::size_t count = 0; count < 64 && !toController.empty() && toController.front().t <= cur; ++count)
        {
            const uint8_t b = toController.front().v;
            toController.pop_front();
            const comms::PayloadDecodeEvent ev = ctlDecoder.consume(b);
            if (ev == comms::PayloadDecodeEvent::FrameReady)
            {
                const comms::PayloadLinkState prev = ctl.state();
                const comms::PayloadValidationResult res = ctl.acceptResponse(ctlDecoder.frameData(), comms::PayloadWireSize, nowMs);
                if (res == comms::PayloadValidationResult::Ok)
                {
                    lastRejection = comms::PayloadValidationResult::Ok;
                    if (inExposure(cur) && ctl.latestTelemetry().mode == comms::PayloadMode::Delayed) ++exposureDelayedAccepts;
                    const us_t acceptedAt = cur;
                    cur += line("[OBC] PAYLOAD_ACCEPTED seq=%u mode=%u\r\n", ctl.awaitedSequence(), static_cast<unsigned>(ctl.latestTelemetry().mode));
                    if (prev == comms::PayloadLinkState::Offline)
                    {
                        cur += line("[OBC] PAYLOAD_RECOVERED recoveries=%u\r\n", ctl.stats().recoveries);
                        if (restoreAssigned >= 0 && recoveryAt < 0 && acceptedAt >= restoreAssigned)
                        {
                            recoveryAt = acceptedAt;
                            recoveryLineEnd = cur;
                        }
                    }
                    else if (prev == comms::PayloadLinkState::Starting)
                    {
                        cur += line("[OBC] PAYLOAD_ONLINE seq=%u sample=%u sensor=%d mode=%u\r\n", ctl.awaitedSequence(), 0u, 0, 0u);
                    }
                }
                else
                {
                    cur += logRejection(res);
                }
            }
            else if (ev == comms::PayloadDecodeEvent::FrameRejected)
            {
                cur += logRejection(ctl.acceptResponse(ctlDecoder.frameData(), comms::PayloadWireSize, nowMs));
            }
        }
        // serviceController(nowMs) :127-150
        {
            const uint32_t prevTimeouts = ctl.stats().timeouts;
            const comms::PayloadLinkState prev = ctl.state();
            ctl.service(nowMs);
            if (ctl.stats().timeouts != prevTimeouts)
            {
                if (inExposure(cur))
                {
                    ++exposureTimeouts;
                    if (firstTimeoutAt < 0) firstTimeoutAt = cur;
                }
                if (prev != comms::PayloadLinkState::Offline && ctl.state() == comms::PayloadLinkState::Offline)
                {
                    if (inExposure(cur) && offlineAt < 0) offlineAt = cur;
                    cur += line("[OBC] PAYLOAD_OFFLINE consecutive=%u heartbeat=OK watchdog=OK\r\n", ctl.consecutiveFailures());
                }
                else if (prev != comms::PayloadLinkState::Offline)
                {
                    cur += line("[OBC] PAYLOAD_TIMEOUT consecutive=%u\r\n", ctl.consecutiveFailures());
                }
            }
        }
        // sendPoll(nowMs) :153-168 -- blocking 32-byte write
        {
            uint8_t req[comms::PayloadWireSize] = {};
            if (ctl.preparePoll(nowMs, req, sizeof(req)))
            {
                for (std::size_t i = 0; i < sizeof(req); ++i) toPayload.push_back({cur + bytesUs(i + 1), req[i]});
                cur += bytesUs(sizeof(req));
            }
        }
        // reportStatus(nowMs) :180-204
        if (static_cast<int32_t>(nowMs - nextStatusMs) >= 0)
        {
            const comms::PayloadLinkStats& s = ctl.stats();
            const char* st = ctl.state() == comms::PayloadLinkState::Online ? "ONLINE" : ctl.state() == comms::PayloadLinkState::Offline ? "OFFLINE" : "STARTING";
            char buf[192];
            std::snprintf(buf, sizeof(buf), "[OBC] PAYLOAD_STATUS state=%s polls=%u ok=%u timeout=%u crc=%u seq=%u recovery=%u heartbeat=OK watchdog=OK\r\n",
                          st, s.pollsSent, s.responsesOk, s.timeouts, s.crcRejects, s.sequenceRejects, s.recoveries);
            cur += bytesUs(std::strlen(buf));
            if (cfg.extraMaxUs > 0) cur += uni(0, cfg.extraMaxUs);   // assumption A7, cause unknown
            nextStatusMs = nowMs + 5000U;
        }
        // vTaskDelay(1): wake at the next tick, plus wake-up latency in [0, J]
        tc = (cur / MS + 1) * MS + jitter();
    }

    us_t jitter()
    {
        if (cfg.jitterMaxUs == 0) return 0;
        switch (uni(0, 3))
        {
        case 0: return 0;
        case 1: return cfg.jitterMaxUs;
        default: return uni(0, cfg.jitterMaxUs);
        }
    }

    us_t logRejection(comms::PayloadValidationResult res)
    {
        if (res == lastRejection) return 0;                     // :244-247
        lastRejection = res;
        return line("[OBC] PAYLOAD_REJECT reason=%s\r\n", res == comms::PayloadValidationResult::BadCrc ? "CRC" : "SEQUENCE");
    }

    template <typename... A>
    static us_t line(const char* fmt, A... args)
    {
        char buf[160];
        std::snprintf(buf, sizeof(buf), fmt, args...);
        return bytesUs(std::strlen(buf));
    }

    // ---- responder: demo-payload main() one loop pass ----
    us_t ptick(us_t t) const { return (t - payloadPhase) / MS; }

    void payloadIteration()
    {
        us_t cur = tp;
        // serviceHostCommands() :229-252
        for (std::size_t n = 0; n < 32 && !toPayloadDebug.empty() && toPayloadDebug.front().t <= cur; ++n)
        {
            const uint8_t b = toPayloadDebug.front().v;
            toPayloadDebug.pop_front();
            comms::PayloadMode sel = mode;
            uint32_t selDelay = delayMs;
            if (parser.consume(b, sel, selDelay) == HostModeCommandParser::Event::ModeSelected)
            {
                mode = sel;                                       // assignment precedes logMode()
                delayMs = selDelay;
                if (sel == comms::PayloadMode::Normal) { if (faultAssigned >= 0 && restoreAssigned < 0) restoreAssigned = cur; }
                else if (faultAssigned < 0) faultAssigned = cur;
                char buf[64];
                if (sel == comms::PayloadMode::Delayed) std::snprintf(buf, sizeof(buf), "[PAYLOAD] MODE=DELAYED delay_ms=%u\r\n", selDelay);
                else std::snprintf(buf, sizeof(buf), "[PAYLOAD] MODE=%s\r\n", sel == comms::PayloadMode::Normal ? "NORMAL" : sel == comms::PayloadMode::Silent ? "SILENT" : "BAD_CRC");
                cur += bytesUs(std::strlen(buf));
                if (sel == comms::PayloadMode::Normal && restoreAssigned >= 0 && restoreConfirmEnd < 0) restoreConfirmEnd = cur;
            }
        }
        // serviceLink() :350-364
        while (!toPayload.empty() && toPayload.front().t <= cur)
        {
            const uint8_t b = toPayload.front().v;
            toPayload.pop_front();
            if (reqDecoder.consume(b) != comms::PayloadDecodeEvent::FrameReady) continue;
            comms::PayloadFrame request = {};
            if (comms::decodePayloadFrame(reqDecoder.frameData(), comms::PayloadWireSize, request) != comms::PayloadValidationResult::Ok) continue;
            ++sampleCounter;
            if (mode == comms::PayloadMode::Silent) continue;     // :318-321
            if (mode == comms::PayloadMode::Delayed)              // HAL_Delay(d): (tick - start) < d + 1
                cur = (ptick(cur) + delayMs + 1) * MS + payloadPhase;
            const comms::PayloadTelemetry tel = {static_cast<uint32_t>(ptick(cur)), sampleCounter, 0, mode};
            uint8_t resp[comms::PayloadWireSize] = {};
            comms::encodeTelemetryResponse(request.sequence, tel, resp, sizeof(resp));
            if (mode == comms::PayloadMode::BadCrc) resp[comms::PayloadCrcOffset] ^= 0x01U;
            for (std::size_t i = 0; i < sizeof(resp); ++i) toController.push_back({cur + bytesUs(i + 1), resp[i]});
            cur += bytesUs(sizeof(resp));
        }
        // HAL_Delay(1): (tick - start) < 2
        tp = (ptick(cur) + 2) * MS + payloadPhase;
    }
};

struct Bounds { double firstTimeout, offline, recovery; };

}  // namespace

int main(int argc, char** argv)
{
    const int scale = argc > 1 ? std::atoi(argv[1]) : 1;
    const us_t J = 2 * MS;
    using M = comms::PayloadMode;
    const Bounds slip0{603, 1607, 516}, slip60{663, 1667, 576};
    std::vector<Config> cfgs = {
        {"silent",            M::Silent,  0,   false, 0,        J, 4000},
        {"badcrc",            M::BadCrc,  0,   false, 0,        J, 4000},
        {"silent_status",     M::Silent,  0,   true,  50 * MS,  J, 4000},
        {"badcrc_status",     M::BadCrc,  0,   true,  50 * MS,  J, 4000},
        {"silent_status_code_only", M::Silent, 0, true, 0,      J, 2000},
    };
    for (uint32_t d : {50u, 80u, 85u, 86u, 90u, 95u, 99u, 100u, 101u, 110u, 150u, 250u})
        cfgs.push_back({nullptr, M::Delayed, d, false, 0, J, 1500});
    for (uint32_t d : {110u, 150u, 159u, 160u, 250u})
        cfgs.push_back({nullptr, M::Delayed, d, true, 50 * MS, J, 1500});

    std::vector<std::string> names;
    int failures = 0;
    std::printf("%-26s %7s %9s %9s %9s %10s %9s  %s\n", "scenario", "trials", "maxTO", "maxOFF", "maxREC", "hostOffMax", "toutTrials", "verdict");
    for (std::size_t k = 0; k < cfgs.size(); ++k)
    {
        Config c = cfgs[k];
        std::string nm = c.name ? c.name : ("delayed_" + std::to_string(c.delayMs) + (c.status ? "_status" : ""));
        c.name = nm.c_str();
        c.trials *= scale;
        std::mt19937_64 rng(20261018ULL + k);
        const Bounds b = c.status ? slip60 : slip0;
        const uint32_t slip = c.status ? 60 : 0;
        double mto = -1, moff = -1, mrec = -1, mhost = -1e9;
        int withTimeout = 0, withDelayedAccept = 0, missing = 0;
        for (int i = 0; i < c.trials; ++i)
        {
            Sim sim(c, rng);
            const Result r = sim.run();
            mto = std::max(mto, r.firstTimeout);
            moff = std::max(moff, r.offline);
            mrec = std::max(mrec, r.recovery);
            mhost = std::max(mhost, r.hostOffset);
            if (r.exposureTimeouts > 0) ++withTimeout;
            if (r.exposureDelayedAccepts > 0) ++withDelayedAccept;
            const bool timeoutMode = c.fault != M::Delayed || c.delayMs + 2 + 2 > 100 + 1 + 2 + slip;
            if (timeoutMode && (r.firstTimeout < 0 || r.offline < 0 || r.recovery < 0)) ++missing;
        }
        // Q2/Q3 bound first timeout and OFFLINE only in timeout modes (SILENT, BAD_CRC, DELAYED with
        // TIMES_OUT); in the undetermined band some polls are accepted and no such bound is claimed.
        // Q4 (recovery) is unconditional.
        const bool timeoutModeCfg = c.fault != M::Delayed || c.delayMs + 2 + 2 > 100 + 1 + 2 + slip;
        bool ok = mrec <= b.recovery && missing == 0 &&
                  (!timeoutModeCfg || (mto <= b.firstTimeout && moff <= b.offline));
        std::string verdict = ok ? "OK" : "EXCEEDS";
        if (c.fault == M::Delayed)
        {
            const bool accepts = c.delayMs + 9 + 1 + 4 < 100;
            const bool timesOut = c.delayMs + 2 + 2 > 100 + 1 + 2 + slip;
            if (accepts && withTimeout > 0) { ok = false; verdict = "ACCEPTS violated"; }
            else if (timesOut && withDelayedAccept > 0) { ok = false; verdict = "TIMES_OUT violated"; }
            else if (accepts) verdict += " (accepted in all)";
            else if (timesOut) verdict += " (timed out in all)";
            else verdict += " (band: " + std::to_string(withTimeout) + " with timeout, " + std::to_string(withDelayedAccept) + " with delayed accept)";
        }
        if (missing) verdict += " missing=" + std::to_string(missing);
        if (!ok) ++failures;
        std::printf("%-26s %7d %9.3f %9.3f %9.3f %10.3f %9d  %s\n", c.name, c.trials, mto, moff, mrec, mhost, withTimeout, verdict.c_str());
    }
    std::printf("bounds: SLIP0 %.0f/%.0f/%.0f  SLIP60 %.0f/%.0f/%.0f ms; failures=%d\n",
                slip0.firstTimeout, slip0.offline, slip0.recovery, slip60.firstTimeout, slip60.offline, slip60.recovery, failures);
    return failures == 0 ? 0 : 1;
}
