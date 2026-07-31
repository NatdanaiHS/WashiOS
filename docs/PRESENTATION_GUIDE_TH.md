# ลำดับการ Present งานฝึกงาน WashiOS

เป้าหมายของการเล่าไม่ใช่ไล่ชื่อไฟล์ แต่ทำให้ผู้ฟังเห็นเส้นทางจาก
“firmware แยกส่วน” ไปเป็น “ระบบที่ตรวจสอบ สาธิต และส่งต่อได้”

## โครงเรื่อง 12–15 นาที

### 1. เปิดเรื่อง: โจทย์ที่รับมา — 1 นาที

พูด:

> ตลอดประมาณ 2 เดือนครึ่ง ผมทำ WashiOS ซึ่งเป็นต้นแบบ flight software
> บน STM32 เป้าหมายไม่ใช่สร้าง operating system ขนาดใหญ่ แต่สร้างฐาน
> firmware ที่เมื่อ application เสีย task ค้าง หรือ payload สื่อสารผิด
> ระบบสามารถตรวจพบ เก็บหลักฐาน และเข้าสู่ทางเลือกที่ปลอดภัยได้

ย้ำขอบเขตว่าเป็น engineering/research prototype ไม่ใช่ flight-qualified
system

### 2. ภาพรวมสถาปัตยกรรม — 1.5 นาที

อธิบายสามส่วน:

1. `bootloader/` ตรวจ vector table และ CRC แล้วเลือก Slot A/B
2. `core/` รัน FreeRTOS พร้อม task health, retained fault log และ watchdog
3. `demo-payload/` เป็นบอร์ด G474 แยกสำหรับทดสอบ UART และ fault injection

ประโยคเชื่อม:

> จุดสำคัญคือผมไม่ได้ทำแต่ละส่วนแยกกัน แต่ทำให้ boot-time, runtime และ
> communication fault handling เชื่อมเป็น flow เดียวกัน

### 3. งานก้อนที่หนึ่ง: Runtime safety core — 2 นาที

พูดตามลำดับ:

- ใช้ static FreeRTOS task allocation และปิด dynamic heap ในส่วนที่ระบบควบคุม
- ให้ critical task check-in ตาม deadline
- refresh watchdog เฉพาะเมื่อ critical task ทั้งหมด healthy
- เก็บ fault log ใน retained `.noinit` พร้อม CRC-32
- ใช้ TMR ป้องกันค่าที่สำคัญและซ่อม single-copy corruption
- ถ้าสร้าง task สำคัญไม่ครบ จะไม่ปล่อย scheduler รันแบบครึ่งระบบ

สรุป:

> จากเดิมที่ firmware อาจค้างเงียบ ระบบนี้เปลี่ยน failure ให้เป็นเหตุการณ์ที่
> ตรวจจับได้และมี recovery path

### 4. งานก้อนที่สอง: WashiBoot A/B bootloader — 2 นาที

พูด:

- แบ่ง flash เป็น bootloader, Slot A และ Slot B
- ตรวจ stack pointer, reset vector และ CRC ก่อน jump
- ถ้า active slot ใช้ไม่ได้จะลอง fallback slot
- pending image มี boot-attempt limit และต้องถูก confirm
- build script อ่าน ELF ของ core แล้วฝัง CRC ที่ตรงกันใน bootloader

อธิบาย flash order:

> ต้อง build core ก่อน จากนั้น build bootloader ที่คำนวณ CRC ของ core ตัวนั้น
> แล้ว flash core โดยไม่ reset ก่อนลง bootloader คู่กันและ reset ครั้งเดียว

### 5. งานก้อนที่สาม: Payload HIL และ LaserCom — 2 นาที

Payload:

- G431 ส่ง poll ทุกประมาณ 500 ms
- G474 ตอบ telemetry frame
- ตรวจ CRC, sequence และ timeout
- fault modes คือ NORMAL, SILENT, BAD_CRC และ DELAYED
- payload เสียไม่ควรทำให้ OBC task health ตายตาม แต่ต้องรายงาน link offline
  และ recover ได้

LaserCom:

- มี GPIO optical telemetry path และกรอบข้อมูล CRC-8
- เป็น demo transmitter ไม่ใช่ complete optical communication stack

### 6. งานก้อนที่สี่: Integration และ handoff — 1.5 นาที

พูด:

- รวม bootloader, core และ payload responder เป็น monorepo
- ทำ build/flash scripts ให้ค้นหา PlatformIO และ OpenOCD ได้ข้ามเครื่อง
- แก้ startup/vector-table path ให้ application ที่ Slot A รันถูกตำแหน่ง
- เพิ่มคู่มือไทย, wiring, troubleshooting และ provisioning notes
- ทำ resource profiler ให้รันจาก repo root โดยไม่ผูก path เครื่องผู้พัฒนา

### 7. หลักฐานว่าระบบไม่พัง — 1.5 นาที

แสดงตัวเลข:

```text
WashiBoot tests          11/11 passed
WashiOS-Core tests       38/38 passed
รวม                      49 tests
Core STM32 builds         6/6 passed
Bootloader builds         3/3 passed
G474 responder build      1/1 passed
Dynamic heap                0 bytes
```

พูด:

> ผมใช้ native tests ตรวจ state machine และ safety logic แล้ว build ทุก target
> แยกอีกชั้น เพื่อจับปัญหาที่ host test ไม่เห็น

### 8. Demo — 2–3 นาที

ถ้ามี hardware:

1. แสดง heartbeat และ NORMAL counter
2. เปลี่ยนเป็น SILENT ให้เห็น timeout/offline แต่ heartbeat ยังอยู่
3. กลับ NORMAL ให้เห็น recovered โดยไม่ reset OBC

ถ้าเวลาเหลือค่อยแสดง BAD_CRC หรือ DELAYED อย่าพยายามสาธิตทุก mode

ถ้า hardware มีปัญหา:

> Demo hardware มี dependency เรื่อง COM port, wiring และคู่ CRC ของ image
> แต่ automated baseline ที่เตรียมไว้ยังยืนยัน 49 tests และทุก target build
> ผ่าน ผมจะเปิด architecture กับ test result แทน แล้วอธิบาย expected
> transition จาก NORMAL ไป OFFLINE และ RECOVERED

### 9. ข้อจำกัดและงานต่อ — 1 นาที

พูดตรง ๆ:

- CRC เป็น integrity check ไม่ใช่ authentication
- metadata ยังไม่อยู่ persistent flash
- ยังไม่มี signature, anti-rollback และ OTA pipeline
- HIL record, power-cycle และ long-run soak test ยังต้องเก็บเพิ่ม
- ต้องเลือก license ก่อน publish ต่อสาธารณะ

ปิด:

> สิ่งที่ผมส่งมอบจึงไม่ใช่ flight-ready product แต่เป็นฐานที่ build ซ้ำได้
> มี safety mechanism ที่ทดสอบได้ มี demo สองบอร์ด และมีเอกสารพอให้คนถัดไป
> รับช่วงต่อโดยไม่ต้องเริ่มแกะระบบใหม่ทั้งหมด

## คำถามที่น่าจะถูกถาม

**ทำไมใช้ CRC ไม่ใช้ digital signature?**

CRC เหมาะกับ milestone การตรวจ accidental corruption และวัด overhead ต่ำ
แต่ไม่ป้องกัน malicious firmware งานถัดไปคือ signature verification และ
anti-rollback

**A/B ทำงานจริงแค่ไหน?**

Policy, vector/CRC validation, fallback และ attempt limit มี native tests
ครอบคลุม ส่วน production update pipeline และ metadata ใน flash ยังไม่ครบ

**ทำไม payload offline แล้วไม่ reset OBC?**

แยก health ของ task ออกจาก health ของ subsystem ตัว task ยังทำงานและยัง
poll เพื่อ recovery ได้ จึงไม่ควรลาก OBC ทั้งระบบให้ reset

**0-byte heap หมายถึง RAM เป็นศูนย์หรือไม่?**

ไม่ใช่ หมายถึงไม่มี dynamic heap ในเส้นทางที่ WashiOS ควบคุม ยังมี static
RAM สำหรับ stack, TCB, buffer และ retained log

**หลักฐานที่แข็งแรงที่สุดคืออะไร?**

49 native tests, firmware build ครบ 10 environments และ resource profile ที่
ทำซ้ำได้ ส่วนหลักฐาน hardware HIL ควรเสริมด้วย log ที่กรอกใน experiment
record

## ก่อนเข้าห้อง 5 นาที

- เปิด deck และหน้าผล test ไว้ล่วงหน้า
- ปิด notification และ serial monitor ที่ไม่ใช้
- เช็กว่า slide แรกใช้คำว่า “Internship Summary” ไม่ใช่ “Weekly Progress”
- จำตัวเลขเพียงชุดเดียว: 49 tests, 10 build environments, 0-byte dynamic heap
- ถ้ามีเวลาไม่พอ ให้ตัด LaserCom และรายละเอียด linker script ก่อน
