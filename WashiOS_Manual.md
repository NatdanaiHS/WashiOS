# WashiOS Documentation Manual
## The Comprehensive Guide to the KNACKSAT-4 Satellite Core OS & HAL Framework

This manual provides a detailed architectural guide, development workflow, and safety handbook for WashiOS. It is written to onboard complete beginners as well as future On-Board Data Handling (OBDH) engineers.

---

## Section 1: What is WashiOS? (The Absolute Beginner Guide)

### What is WashiOS?
**WashiOS** is a specialized, ultra-reliable core operating system and Hardware Abstraction Layer (HAL) framework designed for the **KNACKSAT-4** satellite. 

Unlike a typical computer operating system (like Windows or macOS) or a simple microcontroller loop (like Arduino), WashiOS is engineered specifically for space environments. A satellite in orbit cannot be manually turned off and on if it freezes. It is subjected to extreme solar radiation, high-energy cosmic rays, and severe thermal cycles. The purpose of WashiOS is to provide an indestructible foundation that manages the satellite's tasks, monitors system health, and automatically recovers from faults without human intervention.

### The Modular Layer Architecture (The Smartphone Analogy)
To understand WashiOS, think of a smartphone. Android (the operating system) does not care if your phone uses a camera made by Sony, Samsung, or OmniVision. Android interacts with a generic camera "interface" (the **HAL**). The phone manufacturer writes a specific driver (the **BSP**) that connects the physical camera hardware to that interface.

WashiOS separates its software into four distinct layers to ensure that the core flight logic is independent of the physical processor:

```text
+-------------------------------------------------------------+
| Layer 4: Flight Application (Satellite Mission Logic)       |
|          e.g., Camera control, ADCS, battery management     |
+-------------------------------------------------------------+
| Layer 3: Core OS Services (FreeRTOS & Safety Services)      |
|          e.g., Task scheduling, FaultLog, TMR, Watchdog      |
+-------------------------------------------------------------+
| Layer 2: Hardware Abstraction Layer (HAL C++ Interfaces)    | <--- Pure C++ contracts (No chip-specific code)
+-------------------------------------------------------------+
| Layer 1: Board Support Package (BSP / Target Drivers)      | <--- STM32Cube HAL, DWT registers, USART2
+-------------------------------------------------------------+
| Layer 0: Hardware Target (STM32F411RE Microcontroller)      |
+-------------------------------------------------------------+
```

1. **Flight Application (Layer 4):** The high-level logic of the satellite (e.g., "capture a photo when passing over Thailand").
2. **Core OS Services (Layer 3):** Standard RTOS scheduling combined with custom space-grade safety routines (TMR voting, fault logging, liveness monitoring).
3. **HAL C++ Interfaces (Layer 2):** Pure C++ abstract classes containing virtual methods. They define *what* the hardware can do (e.g., "write bytes to UART") but contain zero vendor-specific code or register definitions.
4. **BSP / Target Drivers (Layer 1):** The concrete C++ implementations of the HAL contracts. This layer contains the real chip-specific code (e.g., STM32Cube HAL library calls) that tells the processor *how* to perform the action.

*Why do this?* If the hardware team decides to replace the STM32 microcontroller with a radiation-hardened chip or a different brand, we only have to rewrite the BSP drivers (Layer 1). The Flight Application (Layer 4) and Core OS (Layer 3) remain untouched, saving years of software redevelopment and testing.

### The Non-Negotiable Rules of Space-Grade C++

#### 1. Static Memory Allocation Only (No Heap)
On a standard PC, programmers use `malloc`, `free`, `new`, and `delete` to dynamically request RAM from the operating system. Over long runtimes, this creates **Heap Fragmentation**—small gaps of unusable memory. Eventually, a critical request for memory will fail because a large enough contiguous block of RAM does not exist, causing a catastrophic software crash. 
In space, WashiOS enforces **Static Allocation**. Every task, queue, stack, and variable must have its memory pre-allocated at compile-time. We know exactly how much RAM the system will use before the rocket leaves the launchpad, guaranteeing that the satellite will never run out of memory in orbit.

#### 2. Zero Exceptions (`-fno-exceptions`)
C++ exceptions (`try`, `catch`, `throw`) introduce unpredictable, non-deterministic execution timing and require substantial compiler runtime overhead. If an exception is thrown but not caught, the C++ runtime calls `std::terminate()`, halting the CPU immediately. In space, WashiOS requires all errors to be handled locally and deterministically using error status returns.

#### 3. Zero RTTI (`-fno-rtti`)
Run-Time Type Information (RTTI) enables features like `dynamic_cast` and `typeid` to verify variable types at runtime. This adds metadata bloating the binary size and slows down CPU execution. WashiOS compiles with RTTI disabled, ensuring a highly compact and fast binary.

---

## Section 2: Architecture Layout & Core Features Explained

Every core file in `include/core/` serves as a defensive shield to keep the satellite operating.

### 2.1. FaultLog (`FaultLog.hpp`)
* **Purpose:** A crash-safe diagnostic recorder.
* **Mechanism:** The `FaultLog` is a fixed-capacity circular ring buffer stored in RAM. When the satellite detects an anomaly (such as a task check-in failure, a TMR vote correction, or a stack overflow), it records a `FaultEvent` containing the type, timestamp, task ID, and detail codes. If the log reaches capacity, it overwrites the oldest entry. This prevents heap overflows while guaranteeing that ground stations can always read the latest diagnostic history after reboot.

### 2.2. TMR: Triple Modular Redundancy (`TMR.hpp`)
* **Purpose:** Protects critical variables from radiation-induced **Single Event Upsets (SEUs)** or bit-flips.
* **Mechanism:** When high-energy cosmic rays strike a microcontroller's RAM, they can flip a binary `0` to a `1`. To prevent this from corrupting vital satellite parameters (like the current orbit phase or deployer status), `TMR<T>` stores three identical copies of the variable in separate memory locations:
  
  ```text
    Cosmic Radiation Bit-Flip!
              │
              ▼
    [ Copy 0 ] [ Copy 1 ] [ Copy 2 ]
     (Val: 42)  (Val: 17)  (Val: 42)
        │          │          │
        └────┬─────┴──────────┘
             ▼
      [ Majority Vote ]
             │
             ├──► Return Correct Value: 42
             │
             └──► Memory Scrubbing: Write "42" back to Copy 1
  ```

  When the variable is read, WashiOS pulls all three copies and performs a majority vote:
  * If all three match, the value is returned.
  * If one copy has been corrupted (e.g., `[42, 17, 42]`), the system returns the correct value (`42`) and automatically **scrubs** (overwrites) the corrupted copy with the correct value.
  * If all three copies diverge (an unrecoverable split, e.g. `[12, 42, 99]`), the system logs a `TmrUnrecoverable` fault and immediately triggers a hardware reset to prevent propagating corrupted data to flight controls.

### 2.3. TaskHealthRegistry & Watchdog (`TaskHealth.hpp`, `Watchdog.hpp`)
* **Purpose:** Liveness monitoring and thread protection.
* **Mechanism:** Under a Real-Time Operating System (RTOS), the software is divided into concurrent threads called "tasks" (e.g., a Telemetry Task, a Sensor Read Task). If a task freezes (e.g., waiting forever on a locked sensor bus), the satellite could become unresponsive.
  * **Registry:** Every critical task must "check in" to the `TaskHealthRegistry` at a regular frequency, updating its `lastCheckInMs`.
  * **Watchdog:** A separate, high-priority watchdog thread runs periodically to check these deadlines. If a task fails to check in before its specified deadline, the watchdog marks it as unhealthy.
  * **Safe-Fail Recovery:** If the unhealthy task is marked as "critical," the watchdog calls `targetSafeFail()`, which disables all interrupts to freeze scheduling and invokes CMSIS `NVIC_SystemReset()`. This triggers a clean hardware reboot of the microcontroller to clear the software fault.

### 2.4. Telemetry Pipeline (`Telemetry.hpp`)
* **Purpose:** Packs system health data for transmission to Earth.
* **Mechanism:** Bandwidth in space communication is extremely expensive. WashiOS serializes the satellite's sequence, uptime, task health masks, and latest fault codes into a compact, packed **28-byte wire frame** (`TelemetryFrame`).
  * **Endian Safety:** All values are written in a deterministic, byte-by-byte little-endian format, preventing data corruption when read by different ground computers.
  * **Fast CRC-32:** To detect data corruption during radio transmission through Earth's atmosphere, the pipeline appends a CRC-32 checksum. To conserve processing cycles and satellite battery power, the calculation is computed via a fast nibble-based (4-bit) 16-entry static lookup table, rather than a slow bit-by-bit calculation loop.

---

## Section 3: The Two Environments (SITL vs Target Board)

WashiOS is designed to run in two distinct environments: on the developer's local computer (Software-in-the-Loop) and on the real satellite chip.

### 3.1. Software-in-the-Loop (SITL)
* **What is it?** The "native" host compiler environment.
* **Why use it?** Satellite hardware is expensive and delicate. With SITL, developers can compile and run WashiOS directly on their personal laptops (Windows, macOS, or Linux).
* **How it works:** WashiOS compiles using the host computer's native compiler (e.g., GCC or Clang). The hardware interfaces (like UART or GPIO) are bound to mock software buffers inside `test/mocks/`. This allows developers to run 100% of the core operating system logic, inject faults (like simulating a frozen telemetry task), and run automated tests locally without any physical hardware.

### 3.2. Target Board Environment
* **What is it?** The real microcontroller target environment (`genericSTM32F411RE`).
* **Why use it?** This compiles the final binary that will run on the satellite's STM32F411RE chip.
* **How it works:** PlatformIO uses a cross-compiler (`arm-none-eabi-gcc`) to translate the C++ code into ARM Cortex-M4 machine code. It links the FreeRTOS kernel and binds the HAL contracts to concrete STM32 Cube HAL drivers.

### 3.3. Compilation and Testing Commands
WashiOS utilizes **PlatformIO** for build and test automation.

#### 1. Compile the target STM32 firmware:
```powershell
# Using global PlatformIO CLI
pio run -e genericSTM32F411RE

# Using Windows-specific default PlatformIO installation path
C:\Users\wachi\.platformio\penv\Scripts\pio.exe run -e genericSTM32F411RE
```
*Outputs: The compiled binary (`firmware.elf` and `firmware.bin`) is generated in `.pio/build/genericSTM32F411RE/`.*

#### 2. Run the native host SITL tests:
```powershell
# Using global PlatformIO CLI
pio test -e native

# Using Windows-specific default PlatformIO installation path
C:\Users\wachi\.platformio\penv\Scripts\pio.exe test -e native
```
*Outputs: Executes the Unity test suite locally on your laptop, returning a report of passed/failed assertions.*

---

## Section 4: Step-by-Step Developer Guide (How to implement new features)

To add a new hardware feature (e.g., a new sensor or communication device), you must follow the strict **3-Step Boundary Process**. This keeps the application isolated from physical hardware and fully testable on host computers.

```text
                   DEVELOPER WORKFLOW FOR NEW DEVICES
                   
    Step 1: Define Interface        Step 2: Implement Mock         Step 3: Implement Driver
     (include/hal/ISensor.hpp)      (test/mocks/MockSensor.hpp)     (src/bsp/Stm32Sensor.cpp)
     ┌───────────────────────┐      ┌─────────────────────────┐    ┌─────────────────────────┐
     │  class ISensor {      │      │  class MockSensor :     │    │  class Stm32Sensor :    │
     │  public:              │      │    public ISensor {     │    │    public ISensor {     │
     │    virtual bool       │      │  public:                │    │  public:                │
     │      readVal() = 0;   │      │    bool readVal() {     │    │    bool readVal() {     │
     │  };                   │───►  │      return mockVal;    │───►│      return HAL_I2C_...     │
     │                       │      │    }                    │    │    }                    │
     │  No hardware-specific │      │  };                     │    │  };                     │
     │  includes allowed!    │      │  (Allows SITL Testing)  │    │  (STM32-Specific Code)  │
     └───────────────────────┘      └─────────────────────────┘    └─────────────────────────┘
```

### Step 1: Define the Hardware-Neutral HAL Contract
Create a new abstract C++ class under `include/hal/`. This class dictates *what* the component must do. It must not include any hardware-specific files.

Example (`include/hal/ISensor.hpp`):
```cpp
#pragma once
#include <cstdint>

namespace hal
{

class ISensor
{
public:
    virtual ~ISensor() = default;

    // Initializes the sensor
    virtual bool initialize() = 0;

    // Reads the raw value from the sensor. Returns false on timeout or bus failure.
    virtual bool readData(uint32_t& outValue, uint32_t timeoutMs) = 0;
};

} // namespace hal
```

### Step 2: Implement the Mock Driver for SITL testing
Create a mock implementation under `test/mocks/`. This allows you to test your flight application logic without physical hardware.

Example (`test/mocks/MockSensor.hpp`):
```cpp
#pragma once
#include "ISensor.hpp"

namespace test_mocks
{

class MockSensor final : public hal::ISensor
{
public:
    bool initialize() override
    {
        return !forcedFailure;
    }

    bool readData(uint32_t& outValue, uint32_t timeoutMs) override
    {
        (void)timeoutMs;
        if (forcedFailure || forcedTimeout)
        {
            return false;
        }
        outValue = mockValue;
        return true;
    }

    // Helper methods for unit tests to inject values/failures
    void setMockValue(uint32_t value) { mockValue = value; }
    void setForcedFailure(bool enable) { forcedFailure = enable; }
    void setForcedTimeout(bool enable) { forcedTimeout = enable; }

private:
    uint32_t mockValue = 100U;
    bool forcedFailure = false;
    bool forcedTimeout = false;
};

} // namespace test_mocks
```

### Step 3: Implement the Production Driver
Create the concrete implementation files under `include/bsp/` and `src/bsp/`. This layer contains the real hardware calls that will run on the satellite.

Example (`include/bsp/Stm32Sensor.hpp`):
```cpp
#pragma once
#include "ISensor.hpp"
#include "stm32f4xx_hal.h" // Target specific STM32 HAL is allowed here

namespace bsp
{

class Stm32Sensor final : public hal::ISensor
{
public:
    explicit Stm32Sensor(I2C_HandleTypeDef* hi2c, uint16_t address);
    bool initialize() override;
    bool readData(uint32_t& outValue, uint32_t timeoutMs) override;

private:
    I2C_HandleTypeDef* m_hi2c;
    uint16_t m_address;
};

} // namespace bsp
```

Example (`src/bsp/Stm32Sensor.cpp`):
```cpp
#include "bsp/Stm32Sensor.hpp"

namespace bsp
{

Stm32Sensor::Stm32Sensor(I2C_HandleTypeDef* hi2c, uint16_t address)
    : m_hi2c(hi2c), m_address(address) {}

bool Stm32Sensor::initialize()
{
    // Real STM32 hardware verification sequence...
    return (m_hi2c != nullptr);
}

bool Stm32Sensor::readData(uint32_t& outValue, uint32_t timeoutMs)
{
    if (m_hi2c == nullptr) return false;
    
    uint8_t buffer[4] = {};
    HAL_StatusTypeDef status = HAL_I2C_Master_Receive(m_hi2c, m_address, buffer, 4U, timeoutMs);
    if (status != HAL_OK)
    {
        return false;
    }
    
    // Pack bytes
    outValue = (static_cast<uint32_t>(buffer[0]) << 24U) |
               (static_cast<uint32_t>(buffer[1]) << 16U) |
               (static_cast<uint32_t>(buffer[2]) << 8U)  |
               static_cast<uint32_t>(buffer[3]);
    return true;
}

} // namespace bsp
```

---

## Section 5: Maintenance, MISRA C++, and Safety Rules

To maintain WashiOS's flight certification, all developers must adhere to strict coding guidelines and standards.

### 5.1. Core Working Rules of the Repository
* **No Dynamic Memory:** Under no circumstances should you call `malloc()`, `calloc()`, `free()`, `new`, `delete`, or instantiate standard library containers (`std::vector`, `std::string`, `std::map`). Use static variables or local stack-based storage.
* **Mandatory Bus Timeouts:** Any interface operation involving an external bus (I2C, SPI, UART) must take an explicit `timeout_ms` parameter. Infinite blocking loops (waiting for registers to change state) are banned.
* **Pre-Reset Diagnostic Logging:** If an unrecoverable failure occurs, the driver must attempt to write details to the `FaultLog` before executing `NVIC_SystemReset()`.

### 5.2. Space-Grade Standards Alignment

#### 1. MISRA C++:2023 Concurrency Protection (Rule 18.3.1)
Because WashiOS runs on a preemptive RTOS, tasks can interrupt each other at any line. Operations on variables wider than 32 bits (such as 64-bit timestamps) require multiple assembly instructions on the Cortex-M4 CPU. 
If task A is interrupted mid-write, and task B reads the variable, it will retrieve corrupted data.
* **Solution:** Always wrap shared read/write segments in FreeRTOS critical sections:
```cpp
taskENTER_CRITICAL();
sharedVariable = new64BitValue;
taskEXIT_CRITICAL();
```

#### 2. NASA/JPL C++ Coding Standard Rule 17 (Check Return Values)
Every function return value representing an execution status must be checked and handled. 
* Do not cast critical initialization calls blindly to `(void)`.
* For example, check task startup:
```cpp
BaseType_t status = heartbeatTask.Start("Heartbeat", 1);
if (status != pdPASS)
{
    // Handle initialization failure
    taskDISABLE_INTERRUPTS();
    NVIC_SystemReset(); // Restart the board
}
```

#### 3. Bounded Execution Loops
All software loops (especially `for` and `while` loops in drivers) must have an absolute upper bound of iterations to prevent infinite loops if physical hardware fails.
* **Bad:** `while (HAL_GPIO_ReadPin(GPIOA, GPIO_PIN_0) == GPIO_PIN_RESET);`
* **Good:**
```cpp
uint32_t timeoutTicks = 10000U;
while (HAL_GPIO_ReadPin(GPIOA, GPIO_PIN_0) == GPIO_PIN_RESET)
{
    if (--timeoutTicks == 0U)
    {
        // Handle timeout
        break;
    }
}
```

#### 4. ECSS-E-ST-40C (Space Engineering: Software) Compliance
ECSS requires that a software system is deterministic, fail-safe, and self-recovering. 
* Never place the CPU in an infinite lockup loop (`for(;;);`) during a fault. 
* A locked-up CPU will drain batteries, lose solar alignment, and cease radio command monitoring. 
* The only acceptable action for an unrecoverable crash is to log the fault and trigger a full hardware reset (`NVIC_SystemReset()`) to recover the spacecraft's main loop.
