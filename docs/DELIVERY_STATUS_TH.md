# WashiOS Delivery Status

ตรวจล่าสุด: 31 กรกฎาคม 2026

เอกสารนี้แยกสิ่งที่ตรวจด้วย automation แล้วออกจากสิ่งที่ยังต้องยืนยันบน
hardware เพื่อไม่ให้ผู้ส่งมอบหรือผู้นำเสนอ claim เกินหลักฐาน

## สถานะที่ยืนยันแล้ว

| ขอบเขต | ผลตรวจ |
| --- | --- |
| WashiBoot native tests | 11/11 ผ่าน |
| WashiOS-Core native/SITL tests | 38/38 ผ่าน |
| Core STM32 builds | 6/6 environments ผ่าน |
| WashiBoot builds | 3/3 environments ผ่าน |
| Demo payload responder build | 1/1 environment ผ่าน |
| Dynamic heap ที่ WashiOS ควบคุม | 0 bytes |

Core environments ที่ build ผ่าน:

```text
genericSTM32F411RE
nucleo_g431rb
nucleo_g431rb_slot_b
nucleo_g431rb_stress
nucleo_g431rb_lasercom
nucleo_g431rb_payload_demo
```

WashiBoot environments ที่ build ผ่าน:

```text
nucleo_g431rb
nucleo_g431rb_lasercom
nucleo_g431rb_payload_demo
```

Resource profile ของ `nucleo_g431rb`:

```text
.text                    16,096 bytes
.data + .bss              6,932 bytes
.noinit retained RAM      1,048 bytes
Dynamic heap                  0 bytes
```

คำสั่งที่ใช้ตรวจ:

```powershell
.\tools\test_native.ps1

cd core
pio run -e genericSTM32F411RE `
        -e nucleo_g431rb `
        -e nucleo_g431rb_slot_b `
        -e nucleo_g431rb_stress `
        -e nucleo_g431rb_lasercom `
        -e nucleo_g431rb_payload_demo

cd ..\bootloader
pio run -e nucleo_g431rb `
        -e nucleo_g431rb_lasercom `
        -e nucleo_g431rb_payload_demo

cd ..\demo-payload
pio run -e nucleo_g474re

cd ..
.\core\scripts\profile_resources.ps1
```

## จุดที่เก็บงานแล้ว

- `profile_resources.ps1` ไม่ผูกกับ path ของเครื่องผู้พัฒนา และรันจาก repo
  root ได้
- ตัวเลข test และรายการ build environments ใน `core/README.md` ตรงกับผล
  ล่าสุด
- AI handoff ใช้ `<repo-root>` และระบุ baseline ปัจจุบันแทน path เก่า
- generated `outputs/` ถูก ignore โดยไม่ลบไฟล์ presentation ที่มีอยู่
- เพิ่มคู่มือพูดสำหรับการสรุปงานฝึกงานใน
  `docs/PRESENTATION_GUIDE_TH.md`

## สิ่งที่ยังไม่ควร claim

- ยังไม่มีผล HIL ที่กรอกครบใน
  `demo-payload/docs/experiment-results.md`
- ยังไม่มีหลักฐาน automated test จากการ flash และ power-cycle บอร์ดจริงใน
  รอบตรวจล่าสุด
- CRC-32 ตรวจความเสียหาย แต่ไม่ใช่ secure boot หรือการยืนยันตัวผู้สร้าง
  firmware
- boot metadata ยังอยู่ใน retained RAM และไม่ทนต่อการตัดไฟ
- ยังไม่มี signed firmware, anti-rollback, OTA pipeline และ long-duration
  soak test
- ยังไม่มี license สำหรับการเผยแพร่ต่อสาธารณะ ต้องให้เจ้าของโครงการเลือก
  license ก่อน

## Checklist ก่อนเปิด demo

1. ใช้ commit และ build คู่เดียวกันระหว่าง core กับ bootloader
2. Flash core ก่อนแบบไม่ reset แล้ว flash bootloader ที่ฝัง CRC คู่กัน
3. ต่อ TX/RX แบบไขว้และต่อ GND เท่านั้นเมื่อทั้งสองบอร์ดใช้ USB แยก
4. เปิด serial monitor ที่ 115200 baud และจด COM port ของแต่ละบอร์ด
5. เตรียมผล test/build ข้างบนเป็น fallback หาก hardware demo มีปัญหา
6. ถ้าจะ claim ผล HIL ให้กรอก experiment record พร้อม log หรือภาพหลักฐาน
