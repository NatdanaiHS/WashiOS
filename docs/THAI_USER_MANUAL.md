# คู่มือส่งมอบและใช้งาน WashiOS FlightStack

เอกสารนี้เป็นคู่มือภาษาไทยสำหรับคนใน lab ที่ต้องการนำโปรเจกต์นี้ไปใช้เอง โดยตั้งใจให้สามารถอ่านแล้วทำตามได้โดยไม่ต้องให้เจ้าของโปรเจกต์อธิบายทีละขั้น

เอกสารนี้ครอบคลุม 3 ส่วนหลัก:

1. `bootloader/` หรือ WashiBoot
2. `core/` หรือ WashiOS-Core
3. demo mode สำหรับ payload UART และ laser communication

---

## 1. ภาพรวมระบบ

WashiOS FlightStack คือโปรเจกต์ firmware สำหรับบอร์ด STM32 ที่ออกแบบให้เหมาะกับงาน embedded ที่ต้องการความน่าเชื่อถือ เช่น small satellite, avionics experiment หรือระบบใน lab ที่ต้องการทดสอบ fault recovery

ระบบทำงานเป็นลำดับนี้:

```text
Power on / Reset
  -> WashiBoot bootloader
  -> ตรวจ firmware ใน Slot A หรือ Slot B
  -> ถ้า firmware ถูกต้อง จึง jump เข้า WashiOS-Core
  -> WashiOS-Core เริ่ม FreeRTOS
  -> tasks ทำงาน เช่น heartbeat, watchdog, payload link, laser telemetry
```

แนวคิดหลักคือระบบไม่ควรแค่ “รันได้” แต่ควรตรวจตัวเองได้ว่ากำลังจะรัน firmware ที่ถูกต้องหรือไม่ และระหว่างรัน task สำคัญยังทำงานปกติหรือไม่

---

## 2. โครงสร้าง repository ใหม่

ตอนนี้จัดเป็น monorepo แล้ว โครงสร้างหลักคือ:

```text
WashiOS-FlightStack/
  README.md
  bootloader/
    platformio.ini
    bootloader.ld
    include/
    src/
    scripts/
    test/
  core/
    platformio.ini
    include/
    src/
    lib/
    scripts/
    test/
  demo-payload/
    platformio.ini
    src/
    docs/
  docs/
    THAI_USER_MANUAL.md
    AI_RESEARCH_HANDOFF.md
    flight_provisioning.md
  tools/
    build_lasercom.ps1
    flash_lasercom.ps1
    build_payload_demo.ps1
    flash_payload_demo.ps1
    build_payload_responder.ps1
    flash_payload_responder.ps1
    test_native.ps1
```

ในเครื่องปัจจุบัน root ของ repo คือ:

```text
<repo-root>
```

ถึงชื่อ folder ด้านนอกยังชื่อ `Bootloader` แต่ภายในถูกจัดเป็น system repo แล้ว โดยมี `bootloader/` และ `core/` อยู่ข้างใน

ในเอกสารนี้จะเรียก path นี้ว่า:

```text
<repo-root>
```

เช่น ถ้าเครื่องปัจจุบันใช้ path เดิม:

```text
<repo-root> = repository root on the current machine
```

---

## 3. Hardware ที่ต้องใช้

สำหรับการทดสอบหลัก:

```text
ST NUCLEO-G431RB หรือบอร์ด STM32G431RB
สาย USB สำหรับ ST-LINK
คอมพิวเตอร์ที่ติดตั้ง PlatformIO
```

สำหรับ laser communication:

```text
laser module หรือ laser diode พร้อมวงจร driver
transistor, MOSFET, หรือ laser driver module
สาย jumper
oscilloscope หรือ logic analyzer สำหรับ debug
photodiode / optical receiver ถ้าต้องการรับสัญญาณจริง
```

ข้อควรระวัง:

```text
ห้ามต่อ laser diode ตรงกับ GPIO ของ STM32
```

GPIO ใช้เป็นสัญญาณควบคุม logic เท่านั้น ให้ต่อผ่าน driver, transistor, MOSFET หรือ module ที่รับ input 3.3 V ได้

---

## 4. Software ที่ต้องมี

ติดตั้ง:

```text
Git
Python
PlatformIO Core หรือ PlatformIO Extension ใน VS Code
ST-LINK driver
```

ตรวจว่า PlatformIO ใช้ได้:

```powershell
pio --version
```

ถ้า PowerShell หา `pio` ไม่เจอ ให้เปิด terminal จาก PlatformIO IDE หรือเพิ่ม PlatformIO เข้า PATH

---

## 5. Memory Map

สำหรับ STM32G431RB:

```text
Bootloader: 0x08000000, 16 KiB
Slot A:     0x08004000, 56 KiB
Slot B:     0x08012000, 56 KiB
RAM:        0x20000000, 32 KiB
```

ความหมาย:

`bootloader/` ถูก link ให้เริ่มที่ `0x08000000`

`core/` ถูก link ให้เริ่มที่ `0x08004000` สำหรับ Slot A

เมื่อ MCU reset จะเริ่มที่ bootloader ก่อน แล้ว bootloader จะตรวจ application ใน Slot A ก่อน jump เข้า core

---

## 6. Pin Mapping สำคัญ

สำหรับ NUCLEO-G431RB:

| Pin | หน้าที่ |
|---|---|
| PA5 | Heartbeat LED / bootloader safe-loop beacon |
| PA6 | Laser TX GPIO |
| PA2 | USART2_TX debug console |
| PC4 | USART1_TX payload UART |
| PC5 | USART1_RX payload UART |

สำหรับ laser communication:

```text
PA6 -> input ของ laser driver
GND -> ground ร่วมกับวงจร laser
```

ห้ามต่อ:

```text
PA6 -> laser diode โดยตรง
```

---

## 7. วิธี clone และเตรียมโปรเจกต์

ถ้า clone จาก GitHub หลังจากจัดเป็น monorepo แล้ว ควร clone repo เดียว:

```powershell
git clone https://github.com/NatdanaiHS/BootloaderForWashiOS.git WashiOS-FlightStack
cd WashiOS-FlightStack
```

ถ้า repo ถูก rename ใน GitHub ภายหลัง ให้ใช้ URL ใหม่แทน

ตรวจว่าเห็นโครงสร้างนี้:

```powershell
dir
```

ควรเห็น:

```text
bootloader
core
demo-payload
docs
tools
README.md
```

---

## 8. คำสั่งทดสอบแบบเร็ว

รัน native tests ทั้ง bootloader และ core:

```powershell
cd <repo-root>
.\tools\test_native.ps1
```

หรือรันเองทีละส่วน:

```powershell
cd <repo-root>\bootloader
pio test -e native

cd <repo-root>\core
pio test -e native
```

---

## 9. หลักสำคัญก่อน build/upload

ต้องจำข้อนี้:

```text
ต้อง build core ก่อน build bootloader
```

เหตุผลคือ bootloader จะอ่านไฟล์ ELF ของ core แล้วคำนวณ CRC-32 เพื่อฝังลงใน bootloader

ถ้าแก้ code ใน `core/` แล้ว upload core ใหม่ แต่ไม่ได้ build/upload bootloader ใหม่ bootloader อาจ reject core เพราะ CRC ไม่ตรง

ลำดับที่ถูกต้องคือ:

```text
1. build core environment ที่ต้องการ
2. build bootloader environment ที่ตรงกัน
3. upload core application โดยยังไม่ reset
4. upload bootloader ที่มี CRC ตรงกัน
5. reset board หนึ่งครั้งเพื่อเริ่มระบบ
```

---

## 10. ใช้งาน Laser Communication Demo

โหมดนี้ใช้สำหรับเพื่อนใน lab ที่ทำ laser communication ด้วย GPIO-controlled laser

Environment ที่ใช้:

```text
nucleo_g431rb_lasercom
```

ใน mode นี้ `core/` จะเปิด macro:

```text
WASHIOS_LASERCOM_TEST
WASHIOS_LASERCOM_ASCII_TEST
```

หมายความว่า firmware จะส่งข้อความ ASCII test ผ่าน PA6 โดยใช้ pulse-duration modulation

### 10.1 วิธี build แบบเร็ว

จาก root:

```powershell
cd <repo-root>
.\tools\build_lasercom.ps1
```

คำสั่งนี้จะทำ:

```text
1. cd core
2. pio run -e nucleo_g431rb_lasercom
3. cd bootloader
4. pio run -e nucleo_g431rb_lasercom
```

### 10.2 วิธี flash แบบเร็ว

เสียบบอร์ดผ่าน USB แล้วรัน:

```powershell
cd <repo-root>
.\tools\flash_lasercom.ps1
```

สคริปต์นี้จะ:

```text
1. build core lasercom
2. build bootloader lasercom พร้อม CRC ล่าสุด
3. upload core application โดยยังไม่ reset
4. upload bootloader พร้อม CRC ล่าสุด แล้ว reset เพื่อเริ่มระบบ
```

### 10.3 วิธี build เองและ upload อย่างปลอดภัย

ถ้าไม่ใช้ script:

```powershell
cd <repo-root>\core
pio run -e nucleo_g431rb_lasercom

cd <repo-root>\bootloader
pio run -e nucleo_g431rb_lasercom

cd <repo-root>
.\tools\flash_lasercom.cmd
```

ตัว flash helper จะ upload core ก่อนโดยไม่ reset จากนั้น upload bootloader ที่มี CRC ตรงกันและเริ่มระบบ

### 10.4 สิ่งที่ควรเห็น

ถ้า application ทำงาน:

```text
PA5 / LD2 จะกระพริบจาก HeartbeatTask
PA6 จะมี pulse สำหรับควบคุม laser
```

ถ้าวัด PA6 ด้วย oscilloscope หรือ logic analyzer จะเห็น:

```text
sync pulse 100 ms high / 100 ms low จำนวน 3 ครั้ง
ตามด้วย pulse สั้น/ยาวของข้อความ ASCII
```

### 10.5 รูปแบบการส่ง bit

ไฟล์ที่เกี่ยวข้อง:

```text
core\include\comms\LaserPdmTx.hpp
```

ค่าปัจจุบัน:

```cpp
constexpr uint32_t LaserPdmShortPulseUs = 2000U;
constexpr uint32_t LaserPdmLongPulseUs = 4000U;
constexpr uint32_t LaserPdmGapUs = 2000U;
```

การเข้ารหัส:

```text
bit 0 = high 2000 us แล้ว low 2000 us
bit 1 = high 4000 us แล้ว low 2000 us
ส่ง MSB first
```

ฝั่ง receiver สามารถ decode โดยวัดระยะ high:

```text
high ใกล้ 2 ms -> 0
high ใกล้ 4 ms -> 1
```

### 10.6 ข้อความ ASCII ที่ส่ง

ไฟล์:

```text
core\src\app\LaserTelemetryTask.hpp
```

ข้อความปัจจุบัน:

```cpp
static constexpr uint8_t Message[] =
    "SVD is Diamond in Linear Algebra\r\n";
```

ถ้าต้องการเปลี่ยนข้อความ:

```cpp
static constexpr uint8_t Message[] =
    "HELLO FROM WASHIOS\r\n";
```

หลังแก้ ต้อง build/flash ใหม่ตามลำดับ:

```powershell
.\tools\flash_lasercom.ps1
```

### 10.7 การต่อวงจร laser

ตัวอย่างแนวคิด:

```text
PA6 ---- resistor ---- gate/base ของ MOSFET หรือ transistor

external supply ---- laser module/driver ---- MOSFET/transistor ---- GND

GND ของ STM32 ต้องต่อร่วมกับ GND ของวงจร laser
```

ถ้าใช้ laser module ที่มี TTL input:

```text
PA6 -> TTL input
GND -> GND ร่วม
```

ให้ตรวจ datasheet ว่า TTL input รับ 3.3 V ได้หรือไม่

### 10.8 ความปลอดภัยของ laser

1. อย่าชี้ laser เข้าตาคน
2. ระวังพื้นผิวสะท้อนแสง
3. ถ้าใช้ laser กำลังสูงให้ใช้แว่นนิรภัยที่ตรง wavelength
4. ควรมี beam stop
5. เริ่ม test ด้วยกำลังต่ำ
6. ก่อนต่อ laser จริง ให้ดู PA6 ด้วย oscilloscope/logic analyzer ก่อน

---

## 11. ใช้งาน Payload UART Demo

Payload UART demo มี 2 ฝั่ง:

```text
core/          OBC-side payload supervisor บน NUCLEO-G431RB
demo-payload/  payload responder firmware บน NUCLEO-G474RE
```

พูดง่าย ๆ คือ `core/` เป็นบอร์ดหลักที่คอย poll payload ส่วน `demo-payload/` เป็น firmware สำหรับอีกบอร์ดหนึ่งที่ทำตัวเป็น payload แล้วตอบกลับ

### 11.1 Environment ที่ใช้

ฝั่ง OBC:

```text
core env = nucleo_g431rb_payload_demo
bootloader env = nucleo_g431rb_payload_demo
```

ฝั่ง payload responder:

```text
demo-payload env = nucleo_g474re
```

### 11.2 Flash ฝั่ง OBC G431

จาก root:

```powershell
cd <repo-root>
.\tools\flash_payload_demo.ps1
```

สคริปต์นี้จะ build `core/`, build `bootloader/` พร้อม CRC ล่าสุด, upload core โดยไม่ reset แล้ว upload bootloader เป็นขั้นสุดท้ายก่อนเริ่มระบบบนบอร์ด G431

### 11.3 Flash ฝั่ง payload responder G474

เสียบบอร์ด G474RE แล้วรัน:

```powershell
cd <repo-root>
.\tools\build_payload_responder.ps1
.\tools\flash_payload_responder.ps1
```

หรือทำเอง:

```powershell
cd <repo-root>\demo-payload
pio run -e nucleo_g474re
pio run -e nucleo_g474re -t upload
```

ถ้าเสียบ ST-LINK สองบอร์ดพร้อมกัน ให้ระวังเลือกผิดบอร์ด ตอนเริ่มแนะนำให้ flash ทีละบอร์ด

### 11.4 การต่อสายระหว่าง G431 กับ G474

ต่อแบบ cross TX/RX:

```text
G431 OBC D1 / PC4 / USART1_TX  ->  G474 payload D0 / PC5 / USART1_RX
G431 OBC D0 / PC5 / USART1_RX  ->  G474 payload D1 / PC4 / USART1_TX
G431 GND                       ->  G474 GND
```

ให้จ่ายไฟทั้งสองบอร์ดด้วย USB ของตัวเอง และอย่าต่อ 3V3 หรือ 5V ของสองบอร์ดเข้าหากัน

### 11.5 UART และ console

ฝั่ง OBC G431:

```text
USART1 PC4/PC5 = คุยกับ payload
USART2 PA2     = debug console ผ่าน ST-LINK VCP
baud rate      = 115200
```

ฝั่ง payload G474:

```text
USART1 PC4/PC5 = payload link
LPUART1 PA2/PA3 = debug console ผ่าน ST-LINK VCP
baud rate       = 115200
```

เปิด serial monitor:

```powershell
pio device list
pio device monitor -p COM_OBC -b 115200
pio device monitor -p COM_PAYLOAD -b 115200
```

ให้แทน `COM_OBC` และ `COM_PAYLOAD` ด้วย COM port จริงที่เห็นจาก `pio device list`

### 11.6 Fault mode ของ payload responder

บนบอร์ด G474 กด user button เพื่อเปลี่ยนโหมด:

```text
NORMAL -> SILENT -> BAD_CRC -> DELAYED -> NORMAL
```

ความหมาย:

```text
NORMAL  = ตอบ telemetry ถูกต้อง
SILENT  = รับ poll แต่ไม่ตอบ
BAD_CRC = ตอบกลับแต่ทำ CRC ให้ผิด
DELAYED = ตอบช้า 250 ms เกิน deadline 100 ms ของ OBC
```

LED บน G474 จะ toggle ทุกครั้งที่ได้รับ poll request ที่ถูกต้อง

### 11.7 สิ่งที่ควรเห็น

ฝั่ง payload console:

```text
[PAYLOAD] READY board=NUCLEO-G474RE mode=NORMAL baud=115200
[PAYLOAD] LINK_ACTIVE
[PAYLOAD] MODE=SILENT
[PAYLOAD] MODE=BAD_CRC
[PAYLOAD] MODE=DELAYED
```

ฝั่ง OBC console:

```text
[OBC] PAYLOAD_LINK_START baud=115200
[OBC] PAYLOAD_ONLINE ...
[OBC] PAYLOAD_TIMEOUT consecutive=...
[OBC] PAYLOAD_OFFLINE consecutive=...
[OBC] PAYLOAD_RECOVERED ...
[OBC] PAYLOAD_STATUS state=...
```

payload offline ไม่ได้แปลว่า OBC firmware ตาย เพราะ `PayloadLinkTask` ยัง check-in กับ watchdog อยู่

---

## 12. Payload Protocol สำหรับคนทำ payload ฝั่งตอบกลับ

OBC ส่ง `PollRequest` ทุกประมาณ 500 ms

payload ต้องตอบ `TelemetryResponse` กลับมาด้วย sequence เดิม

Frame ขนาด:

```text
32 bytes
```

โครงสร้าง frame:

| Offset | Size | Field |
|---:|---:|---|
| 0 | 1 | sync0 = 0x57 |
| 1 | 1 | sync1 = 0x50 |
| 2 | 1 | version = 1 |
| 3 | 1 | message type |
| 4 | 4 | sequence, little-endian |
| 8 | 2 | payload length, little-endian |
| 10 | 2 | flags, little-endian |
| 12 | 16 | payload |
| 28 | 4 | CRC-32 over bytes 0..27 |

Message type:

```text
PollRequest       = 0x01
TelemetryResponse = 0x81
```

Telemetry payload:

| Offset in payload | Size | Field |
|---:|---:|---|
| 0 | 4 | uptimeMs |
| 4 | 4 | sampleCounter |
| 8 | 4 | simulatedSensorMilliunits |
| 12 | 1 | mode |
| 13 | 3 | reserved / zero |

ถ้า response CRC ผิด OBC จะ reject เป็น CRC

ถ้า sequence ผิด OBC จะ reject เป็น SEQUENCE

ถ้าไม่ตอบ OBC จะ timeout

ถ้า timeout 3 ครั้งติด OBC จะมอง payload เป็น OFFLINE

ถ้ากลับมาตอบถูก OBC จะมองว่า RECOVERED/ONLINE

---

## 13. Bootloader ทำอะไร

bootloader อยู่ใน:

```text
bootloader/
```

หน้าที่:

1. ตรวจ boot metadata
2. ตรวจ retained fault log
3. ตรวจว่า active slot boot ได้หรือไม่
4. ตรวจ vector table ของ application
5. ตรวจ CRC-32 ของ application
6. ถ้าผ่านจึง jump เข้า application
7. ถ้า fail จะลอง fallback slot
8. ถ้าไม่มี slot ที่ใช้ได้ จะเข้า safe loop

safe loop:

```text
PA5 toggle เป็น beacon
ระบบไม่เข้า application
```

ถ้าเห็น PA5 กระพริบแต่ PA6 ไม่มี pulse ใน lasercom mode อาจเป็นไปได้ว่า bootloader ไม่ได้ jump เข้า core เพราะ application ไม่ผ่าน validation

---

## 14. ไฟล์สำคัญ

### Bootloader

```text
bootloader\platformio.ini
bootloader\bootloader.ld
bootloader\src\main.cpp
bootloader\include\boot\BootPolicy.hpp
bootloader\include\boot\BootMetadata.hpp
bootloader\include\boot\Crc32.hpp
bootloader\src\bsp\g4\Stm32G4FlashMap.cpp
bootloader\src\bsp\g4\Stm32G4BootPlatform.cpp
bootloader\src\bsp\g4\Stm32G4Beacon.cpp
bootloader\scripts\provision_slot_crc.py
```

### Core

```text
core\platformio.ini
core\src\main.cpp
core\include\core\FaultLog.hpp
core\include\core\TaskHealth.hpp
core\include\core\Watchdog.hpp
core\include\core\Telemetry.hpp
core\include\rtos_config\WashiTask.hpp
core\src\app\HeartbeatTask.hpp
core\src\app\WatchdogTask.hpp
core\src\app\LaserTelemetryTask.hpp
core\src\app\PayloadLinkTask.hpp
core\include\comms\LaserPdmTx.hpp
core\include\comms\FsoFrame.hpp
core\include\comms\PayloadProtocol.hpp
core\include\comms\PayloadLinkController.hpp
```

---

## 15. Troubleshooting

### 15.1 Build bootloader แล้วหา core ELF ไม่เจอ

สาเหตุ:

```text
ยังไม่ได้ build core environment ที่ตรงกัน
```

วิธีแก้:

```powershell
cd <repo-root>\core
pio run -e nucleo_g431rb_lasercom

cd <repo-root>\bootloader
pio run -e nucleo_g431rb_lasercom
```

หรือใช้:

```powershell
cd <repo-root>
.\tools\build_lasercom.ps1
```

### 15.2 Upload core แล้วไม่รัน

สาเหตุที่พบบ่อย:

1. ยังไม่มี bootloader ที่ `0x08000000`
2. build/upload environment ไม่ตรงกัน
3. core ถูกแก้แล้วแต่ไม่ได้ rebuild bootloader
4. bootloader reject application เพราะ CRC ไม่ตรง

วิธีแก้:

```powershell
cd <repo-root>
.\tools\flash_lasercom.ps1
```

### 15.3 PA6 ไม่มี pulse

เช็ก:

1. ใช้ env `nucleo_g431rb_lasercom` หรือไม่
2. PA5 heartbeat กระพริบหรือไม่
3. bootloader jump เข้า application แล้วหรือยัง
4. ต่อ probe ที่ PA6 จริงหรือไม่
5. ใช้ GND ร่วมกับเครื่องวัดหรือไม่

### 15.4 Laser ไม่ยิง แต่ PA6 มี pulse

ปัญหาน่าจะอยู่ที่ hardware:

1. driver ไม่รับ 3.3 V logic
2. ต่อ GND ไม่ร่วม
3. power supply ของ laser ไม่พอ
4. transistor/MOSFET ต่อผิด
5. laser module ถูกปิดด้วย enable pin อื่น

### 15.5 Serial monitor ไม่เห็นข้อความ

สำหรับ lasercom ASCII test ข้อความถูกส่งทาง PA6 ไม่ใช่ serial console

สำหรับ payload demo ให้ดู USART2 debug console ที่ baud 115200

---

## 16. Checklist สำหรับทดลอง LaserCom

```text
[ ] clone repo แล้วเห็น bootloader/, core/, demo-payload/, docs/, tools/
[ ] ติดตั้ง PlatformIO แล้ว
[ ] ใช้บอร์ด NUCLEO-G431RB
[ ] ต่อ PA6 ไป input ของ laser driver ไม่ใช่ laser diode ตรง ๆ
[ ] ต่อ GND ร่วม
[ ] run .\tools\flash_lasercom.ps1 สำเร็จ
[ ] กด reset
[ ] PA5 heartbeat กระพริบ
[ ] PA6 มี pulse
[ ] oscilloscope เห็น sync pulse 100 ms จำนวน 3 ครั้ง
[ ] receiver decode 2 ms เป็น 0 และ 4 ms เป็น 1
```

---

## 17. ข้อจำกัดของระบบตอนนี้

1. CRC-32 ตรวจ corruption ได้ แต่ไม่ใช่ security
2. ยังไม่มี signed firmware verification
3. ยังไม่มี anti-rollback
4. boot metadata ยังไม่ใช่ persistent flash metadata แบบ production
5. provisioning flow ยังเหมาะกับ development มากกว่า OTA จริง
6. LaserCom ยังเป็น demo transmitter ไม่ใช่ optical communication stack สมบูรณ์
7. payload demo เป็น OBC-side supervisor ไม่ใช่ payload firmware สมบูรณ์

---

## 18. งานที่ควรพัฒนาต่อ

1. เพิ่ม laser receiver และ decoder
2. เพิ่ม checksum/retransmission/error correction สำหรับ laser link
3. เพิ่ม signed firmware ใน bootloader
4. เก็บ boot metadata ลง flash อย่างปลอดภัย
5. เพิ่ม script สำหรับ fault injection
6. เก็บผลวัด เช่น boot time, CRC time, watchdog recovery time, laser frame transmit time
7. ทำเอกสาร PDF ส่งมอบพร้อมรูปวงจรและผล oscilloscope

---

## 19. สรุปสั้นที่สุด

ถ้าจะทดลอง LaserCom:

```powershell
cd <repo-root>
.\tools\flash_lasercom.ps1
```

ดูผล:

```text
PA5 = heartbeat
PA6 = laser TX pulse
```

ถ้าจะแก้ข้อความ:

```text
core\src\app\LaserTelemetryTask.hpp
```

ถ้าจะแก้ pulse timing:

```text
core\include\comms\LaserPdmTx.hpp
```

ถ้าแก้ core แล้ว:

```text
ต้อง rebuild bootloader ด้วย เพราะ CRC ของ application เปลี่ยน
```
