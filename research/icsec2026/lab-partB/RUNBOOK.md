# Part B — คู่มือวันแล็บ (B1–B6) สำหรับ G431RB + F411RE

**บอร์ดที่ใช้:** NUCLEO-G431RB 1 บอร์ด (controller, เรียกว่า **G431**) และ NUCLEO-F411RE 1 บอร์ด (payload, เรียกว่า **F411**)
F411 บอร์ดที่สองไม่จำเป็น ให้เก็บไว้เป็นอะไหล่ ถ้าบอร์ดแรกมีปัญหาค่อยสลับมาใช้

**เริ่มได้เลยตอนนี้:** Session 1 (B4) และ Session 2 (B3) ใช้แค่ G431 ส่วน Session 3 (B1, B2, B5, B6) ใช้ G431 + F411

ทุกคำสั่งรันใน **Terminal ของ VS Code** ที่โฟลเดอร์ `C:\MyOS\WashiOS-lab`
(VS Code: **File → Open Folder** → พิมพ์ `C:\MyOS\WashiOS-lab` → **Select Folder** จากนั้น **Terminal → New Terminal**
บรรทัดใน Terminal ต้องขึ้นต้นด้วย `PS C:\MyOS\WashiOS-lab>`)

**กฎ evidence:** ทุกการวัดเริ่มด้วย `labtool.py new ...` (สร้างโฟลเดอร์ใหม่ชื่อไม่ซ้ำ) และจบด้วย `labtool.py close ...`
ห้ามใช้ run เดิมซ้ำ ถ้าพลาดกลางทางให้ close พร้อม `--note "ABORTED: เหตุผล"` แล้วสร้าง run ใหม่

> **Deviation ที่ต้องเขียนในเปเปอร์:** งานเดิมใช้ G474 เป็น payload แต่รอบนี้ใช้ **F411** แทน
> ค่าที่วัดฝั่ง controller อย่างเดียว (B1 J, B2, B3, B4) ไม่ขึ้นกับว่า payload เป็นบอร์ดอะไร
> แต่ **B5 (T_tx)** และ **B6 (recovery)** รวมเวลาตอบกลับของ payload ไว้ด้วย จึงต้องระบุว่าเป็นคู่ G431–F411

> **คาดไว้ก่อน (อ่านก่อนเริ่ม):** RAM ที่ bootloader ใช้เก็บ `BootMetadata` (0x20000018) ถูก `.data` ของแอป
> (0x20000000–0x20000088) เขียนทับตอนแอปบูต และ `FaultLog` ของ bootloader (0x20000050) กับของแอป (0x20000088)
> อยู่คนละที่ ผลที่น่าจะเห็นบนบอร์ดจริง:
> - **B3:** หลัง IWDG reset บอร์ด**อาจรันแอปใหม่เอง** แทนที่จะค้างใน beacon (ขัดกับ B6/F2)
> - **B4 โหมด `system`:** boot count ไม่สะสมข้ามรอบ แต่โหมด `policy` ควรตรงกับโมเดล
>
> ถ้าเห็นแบบนี้ **ไม่ใช่ว่าต่อสายผิด** แต่เป็นผลการทดลองจริง ให้เก็บไว้ตามปกติ

---

## 0. เตรียมของ (ทำครั้งเดียว)

### 0.1 ของที่ต้องมี
- G431, F411 และสาย Micro-USB 2 เส้น
- Logic analyzer "24MHz 8CH" (ตัวสีขาวจาก Shopee) พร้อมสาย USB และสายแพสีรุ้ง
- สาย Dupont **ตัวผู้-ตัวผู้** ประมาณ 15 เส้น (หัวสายแพของ analyzer เป็นตัวเมีย และ header สีดำบนบอร์ดก็เป็นตัวเมีย
  จึงต้องเอาสายตัวผู้-ตัวผู้มาต่อตรงกลาง)

**ชื่อช่องบน analyzer:** บนตัวเครื่องเขียน **CH1–CH8, GND, CLK** ซึ่งคู่มือนี้ใช้ชื่อเดียวกับที่เขียนบนตัวเครื่องเลย
สาย **CLK ไม่ใช้** ให้ปล่อยว่างไว้

### 0.2 ตรวจ Python
```powershell
python --version
python -c "import serial; print('pyserial OK')"
```
ถ้าไม่มี pyserial: `python -m pip install pyserial`

### 0.3 ลงโปรแกรม sigrok
1. เข้า https://sigrok.org/wiki/Downloads แล้วเลื่อนลงไปหัวข้อ **Windows**
2. โหลดและติดตั้ง **PulseView** (installer x86_64) กด Next ไปจนถึง Finish
3. โหลดและติดตั้ง **sigrok-cli** (installer x86_64) กด Next ไปจนถึง Finish
   ถ้าขึ้น "Windows protected your PC" ให้กด **More info → Run anyway**

### 0.4 ลงไดรเวอร์ analyzer (Zadig) ทำครั้งเดียว
1. เสียบ analyzer เข้าคอม
2. Start → พิมพ์ Zadig → เลือก **Zadig (sigrok-cli)** (อันที่**ไม่มี**คำว่า Win XP) → กด Yes
3. เมนู **Options** แล้วติ๊ก **List All Devices**
4. ใน dropdown ตรงกลาง เลือกตัวที่ช่อง USB ID ขึ้นว่า **0925 3881** (มักชื่อ `fx2lafw` หรือ `Unknown Device`)
   **ห้ามเลือก** ST-Link, STM32, เมาส์, คีย์บอร์ด, Bluetooth
5. ช่องขวาของลูกศรเขียวต้องเป็น **WinUSB** แล้วกด **Install Driver** (หรือ Replace Driver) รอจนขึ้นว่า successfully
6. ปิด Zadig แล้วถอด analyzer ออกและเสียบใหม่

### 0.5 ทดสอบ analyzer
```powershell
python research\icsec2026\lab-partB\labtool.py check
```
ต้องขึ้น `Analyzer OK.`

### 0.6 ตั้งตัวแปรที่ใช้ทั้งวัน
**ต้องพิมพ์ใหม่ทุกครั้งที่เปิด Terminal ใหม่**
```powershell
$pio = "$env:USERPROFILE\.platformio\penv\Scripts\pio.exe"
$lab = "research\icsec2026\lab-partB\labtool.py"
$bf  = "research\icsec2026\lab-partB\bootfault.py"
```

### 0.7 หา COM port
เสียบ **ทีละบอร์ด** แล้วรันคำสั่งนี้:
```powershell
& $pio device list
```
หาบรรทัดที่เขียนว่า `STMicroelectronics STLink Virtual COM Port` แล้วจดเลขไว้
(COM3/COM4 ที่เขียน Bluetooth ไม่เกี่ยว):

`G431 = COM___`   `F411 = COM___`

ทุกคำสั่งข้างล่างที่เขียน `COM_G431` หรือ `COM_F411` ให้เปลี่ยนเป็นเลขจริง เช่น `COM7`

---

## Session 1 — B4 Boot-policy fault injection (ใช้ G431 อย่างเดียว ไม่ต้องใช้ analyzer)

ประมาณ 30 นาที **เสียบ USB แค่ G431 ตัวเดียว** (F411 ห้ามเสียบตอนนี้ ไม่อย่างนั้น OpenOCD อาจเลือกบอร์ดผิด)

### 1.1 Flash firmware lab และเขียน slot B
```powershell
powershell -ExecutionPolicy Bypass -File .\tools\flash_payload_demo.ps1 -CoreEnv nucleo_g431rb_payload_demo_lab -BootloaderEnv nucleo_g431rb_payload_demo_lab
```
ต้องจบด้วย `Payload demo firmware flashed and started.` และไฟ LED เขียว (LD2) บน G431 กระพริบทุกครึ่งวินาที
```powershell
$run = python $lab new B4 boot-policy-fixed --flashed "G431 lab, fixed bootloader, slot B = lab_slot_b"
python $bf $run prepare-slot-b
python $bf $run read
```
`read` จะแสดง BootMetadata 13 ช่อง ถ้าบรรทัดสุดท้ายขึ้น `valid: False` แปลว่าแอปเขียนทับ metadata ไปแล้ว ซึ่งตรงกับที่คาดไว้

### 1.2 Scenario บน bootloader ที่แก้แล้ว
รันทีละบรรทัด แต่ละคำสั่งทำงานเองทั้งหมด (reset, ทำให้ flash เสีย, อ่านค่าผ่าน SWD แล้วคืน flash) ใช้เวลาคำสั่งละประมาณ 10–30 วินาที
เทียบผลกับบรรทัด `expect:` ที่พิมพ์ออกมา
```powershell
python $bf $run scenario a
python $bf $run scenario b
python $bf $run scenario c --resets 6
python $bf $run scenario d --k 1 --resets 6
python $bf $run scenario d --k 2 --resets 6
python $bf $run scenario d --k 3 --resets 6
python $bf $run scenario c --mode system --resets 6
python $bf $run scenario d --k 2 --mode system --resets 6
python $lab close $run
```
| คำสั่ง | ควรได้ (ตามโมเดล) |
|---|---|
| a | `LAUNCHED_B` |
| b | `SAFE_LOOP` และ fail = NoValidFirmwareSlot |
| c | `LAUNCHED_B` 4 ครั้ง แล้ว `SAFE_LOOP` และ fail = BootLoopLimit |
| d (k=1,2,3) | B launch 4 ครั้งทุกค่า k |
| โหมด system | อาจต่างจากโมเดล (เรื่อง RAM ถูกเขียนทับ) ให้จดผลไว้ |

### 1.3 Bootloader ก่อนแก้ (pre-fix) สำหรับ F4
build ไว้ให้แล้วที่ `C:\MyOS\WashiOS-prefix-bootloader` (commit `c8ab6f6^`)
```powershell
$run = python $lab new B4 boot-policy-prefix --flashed "G431 lab, PRE-FIX bootloader c8ab6f6^"
python $bf $run flash-bootloader prefix
python $bf $run scenario d --k 1 --resets 6 --bootloader prefix
python $bf $run scenario d --k 2 --resets 6 --bootloader prefix
python $bf $run scenario d --k 3 --resets 6 --bootloader prefix
python $bf $run scenario c --resets 6 --bootloader prefix
python $bf $run flash-bootloader fixed
python $lab close $run
```
บน pre-fix ควรได้ B launch **4−k** ครั้ง (k=1 ได้ 3 ครั้ง, k=2 ได้ 2 ครั้ง, k=3 ได้ 1 ครั้ง)
**ห้ามลืมบรรทัด `flash-bootloader fixed`** ซึ่งเป็นการคืน bootloader ตัวที่แก้แล้ว

---

## Session 2 — B3 Watchdog stall (ใช้ G431 + analyzer)

ประมาณ 30 นาที

### 2.1 ต่อสาย Setup B (**ถอด USB ทุกเส้นก่อน**)
ชื่อขา D0…D13 พิมพ์อยู่ข้าง header สีดำบนบอร์ด

| Analyzer (บนตัวเครื่อง) | G431 ขา | สัญญาณ |
|---|---|---|
| **CH1** | **D10** | stall (ขึ้น high ตอนเริ่ม stall) |
| **CH2** | **D11** | wdrec (ขึ้น high ตอนบันทึก WATCHDOG_TIMEOUT) |
| **CH3** | **RESET** | nrst (pulse ลงตอน reset) |
| **CH4** | **D13** | led (heartbeat หรือ beacon) |
| **CH5** | **D4** | loop (เปลี่ยนเฉพาะตอนแอปรันอยู่) |
| **GND** | **GND** | ground |

**รู RESET** อยู่บน header ตัวเมียแถวสั้นฝั่งไฟเลี้ยง ซึ่งเรียงเป็น `NC, IOREF, RESET, 3V3, 5V, GND, GND, VIN`
ให้เสียบที่รูที่เขียนว่า **RESET** **ห้ามเสียบรู 3V3/5V/VIN** ส่วน GND ใช้รู GND ตรงนี้ได้เลย
CH6, CH7, CH8 และ CLK ปล่อยว่าง

### 2.2 Payload-link stall
เสียบ analyzer และ G431 (USB เท่านั้น) แล้ว flash:
```powershell
powershell -ExecutionPolicy Bypass -File .\tools\flash_payload_demo.ps1 -CoreEnv nucleo_g431rb_payload_demo_stall_link -BootloaderEnv nucleo_g431rb_payload_demo_stall_link
```
firmware ตัวนี้ทำให้ task PayloadLink **หยุดเองหลังบูต 10 วินาที**
```powershell
python $lab check
$run = python $lab new B3link stall-payloadlink --flashed "G431 stall_link"
python $lab capture $run --setup B --seconds 300 --serial COM_G431:g431
```
ระหว่างที่อัด 5 นาที **ให้ดูไฟ LD2 บน G431**:
- **กรณี A, แอปกลับมาเอง** (กระพริบช้าทุกครึ่งวินาทีอีก แล้วอีกราว 10 วินาทีก็ reset อีก): ไม่ต้องทำอะไร ระบบจะวน trial เองประมาณ 20 รอบ
- **กรณี B, กระพริบเร็วค้าง (beacon) แอปไม่กลับมา:** ทำทีละ trial ดังนี้
  1. รอ 3 วินาที แล้วกดปุ่ม **RESET สีดำ** บน G431 หนึ่งครั้ง ไฟต้องยังกระพริบเร็วอยู่
  2. ถอดแล้วเสียบ USB ของ G431 ใหม่เพื่อเริ่ม trial ถัดไป
  3. ทำให้ได้ประมาณ 10 trial

พอครบ 5 นาที:
```powershell
python $lab analyze $run --test B3
python $lab close $run --note "observed: กรณี A หรือ B"
```
ค่าที่ดู: `stall_to_record` เทียบกับ W3 952 ms, `record_to_reset` เทียบกับค่าสูงสุดของ IWDG 2170 ms
และ `relaunched_without_power_cycle`

### 2.3 Heartbeat stall
```powershell
powershell -ExecutionPolicy Bypass -File .\tools\flash_payload_demo.ps1 -CoreEnv nucleo_g431rb_payload_demo_stall_heartbeat -BootloaderEnv nucleo_g431rb_payload_demo_stall_heartbeat
$run = python $lab new B3heartbeat stall-heartbeat --flashed "G431 stall_heartbeat"
python $lab capture $run --setup B --seconds 300 --serial COM_G431:g431
python $lab analyze $run --test B3
python $lab close $run --note "observed: กรณี A หรือ B"
```
รอบนี้ไฟ LED จะหยุดกระพริบตอน stall ซึ่งเป็นเรื่องปกติ และ `stall_to_record` ให้เทียบกับ W3 1652 ms

---

## Session 3 — B1 + B2 + B5 + B6 (ใช้ G431 + F411 + analyzer)

ประมาณ 45 นาที

### 3.1 Flash ทีละบอร์ด
**G431** (เสียบเฉพาะ G431) ให้คืน firmware lab ปกติ:
```powershell
powershell -ExecutionPolicy Bypass -File .\tools\flash_payload_demo.ps1 -CoreEnv nucleo_g431rb_payload_demo_lab -BootloaderEnv nucleo_g431rb_payload_demo_lab
```
**F411** (ถอด G431 ออก แล้วเสียบเฉพาะ F411):
```powershell
cd demo-payload; & $pio run -e nucleo_f411re_payload_lab -t upload; cd ..
```
ต้องขึ้น `SUCCESS` (ตอนนี้จด COM ของ F411 ในข้อ 0.7 ได้เลย)

### 3.2 ต่อสาย (**ถอด USB ทุกเส้นก่อน**)
**สาย link ระหว่างบอร์ด** (สองบอร์ดใช้ขาคนละชุด ให้ต่อตามตารางนี้เป๊ะๆ):

| G431 | F411 |
|---|---|
| **D1** (PC4, TX ของ G431) | **D2** (PA10, RX ของ F411) |
| **D0** (PC5, RX ของ G431) | **D8** (PA9, TX ของ F411) |
| **GND** | **GND** |

ห้ามต่อ 3V3/5V ข้ามบอร์ด แต่ละบอร์ดใช้ไฟจาก USB ของตัวเอง

**สาย analyzer Setup A** (ถอดสายของ Setup B ออกให้หมดก่อน):

| Analyzer (บนตัวเครื่อง) | บอร์ด | ขา | สัญญาณ |
|---|---|---|---|
| **CH1** | G431 | **D2** | poll |
| **CH2** | G431 | **D4** | loop |
| **CH3** | G431 | **D5** | status |
| **CH4** | G431 | **D6** | write |
| **CH5** | G431 | **D8** | accept |
| **CH6** | G431 | **D7** | timeout |
| **CH7** | G431 | **D9** | recovery |
| **CH8** | **F411** | **D7** | pl_fault (high ระหว่างอยู่ใน fault mode) |
| **GND** | G431 | **GND** | ground |

ระวังเรื่องขาที่สับสนง่าย:
- บน G431 ขา **D2 และ D8 เป็นสายไป analyzer** ส่วนบน F411 ขา **D2 และ D8 เป็นสาย link**
- สัญญาณ pl_fault บน F411 อยู่ที่ขา **D7** (ไม่ใช่ D8)

### 3.3 เสียบไฟและเช็ค
เสียบ USB ของ G431, F411 และ analyzer ทั้งสามตัว ไฟ LD2 บน F411 ควรกระพริบทุก poll (ทุกครึ่งวินาที)
ถ้า F411 ไม่กระพริบ แปลว่าสาย link สลับกัน ให้เช็คตาราง link อีกครั้ง

### 3.4 Smoke test 30 วินาที
```powershell
$run = python $lab new trial smoke-setupA --flashed "G431 lab + F411 payload lab"
python $lab capture $run --setup A --seconds 30
python $lab analyze $run
python $lab close $run --note "smoke test only"
```
ดูส่วน `"signals"`: poll ประมาณ 60, loop เป็นหลักหมื่น, status 6 ขึ้นไป, write 6 ขึ้นไป, accept ประมาณ 60
**ถ้าช่องไหนได้ 0 หรือ 1 แปลว่าสายช่องนั้นหลุดหรือเสียบผิด** ให้แก้แล้วทำ smoke test ใหม่

### 3.5 B1/B2/B5 — อัด 11 นาที (ห้ามแตะบอร์ด)
```powershell
$run = python $lab new B1B2B5 normal-11min --flashed "G431 lab + F411 payload lab"
python $lab capture $run --setup A --seconds 660 --serial COM_G431:g431 --serial COM_F411:payload
python $lab analyze $run --test B1 --test B2 --test B5
python $lab close $run --note "payload board = F411RE (deviation from G474)"
```
- **B1:** `poll_period_regular` เทียบกับ `poll_period_containing_status_report` ค่า `max_abs_dev_ms` คือ J ที่วัดได้
- **B2:** ถ้า `next_poll_slip_after_status` ใกล้เคียงกับ `status_span` แปลว่าสาเหตุคือ console write แบบ blocking
  ถ้า `writes_at_or_over_10ms_uart_timeout` มากกว่า 0 แปลว่าบรรทัด status ถูกตัดเพราะชน timeout 10 ms
- **B5:** `poll_to_accept` คือ T_tx (ของคู่ G431–F411)

### 3.6 B6 — recovery 15 trial (ใช้ 2 terminal)
**Terminal 1** (ตั้งตัวแปรตามข้อ 0.6 ก่อน, รอบนี้**ห้ามใส่** `--serial`):
```powershell
$run = python $lab new B6 recovery-15trials --flashed "G431 lab + F411 payload lab"
python $lab capture $run --setup A --seconds 420
```
**Terminal 2** (กด `+` บนแถบ Terminal เพื่อเปิดอันใหม่) ให้เริ่มภายใน 10 วินาทีหลังจาก Terminal 1 ขึ้นคำว่า Recording:
```powershell
python research\icsec2026\injector\run_payload_campaign.py --campaign labB6_g431_f411_s20261101 --seed 20261101 --g431-port COM_G431 --g474-port COM_F411 --repetitions 5
```
(ช่อง `--g474-port` เป็นแค่ชื่อพารามิเตอร์ ให้ใส่ COM ของ **F411** ลงไปได้เลย และถ้าทำซ้ำต้องเปลี่ยนชื่อ campaign กับ seed ใหม่)

รอให้ capture ครบ 420 วินาที แล้วใน Terminal 1:
```powershell
python $lab analyze $run --test B6
python $lab close $run --note "campaign: research/icsec2026/runs/labB6_g431_f411_s20261101; payload = F411RE"
```
ค่าที่ดู: `recovery_interval` และ `recoveries_over_500ms` ว่ามีกรณีแบบ R085 (523 ms) หรือไม่

---

## ปิดวัน
1. ทุก run ใน `research\icsec2026\lab-partB\runs\` ต้องมีไฟล์ `INVENTORY.sha256`
2. ส่งรายชื่อโฟลเดอร์ใน `runs\` มาเพื่อสรุปผลเทียบกับ E1/E2/W3/W5/W6/B3/B4/B6/F2/F4

## แก้ปัญหา
| อาการ | ทำอะไร |
|---|---|
| `$run` ว่าง หรือ error ว่า `$lab` ไม่รู้จัก | เปิด Terminal ใหม่แล้วยังไม่ได้ตั้งตัวแปร ให้ทำข้อ 0.6 ใหม่ |
| `labtool check` ไม่เจอ analyzer | ทำ Zadig (0.4) ใหม่, ปิด PulseView, เปลี่ยนช่อง USB |
| ช่องใดนับได้ 0 | สายหลุดหรือเสียบผิดขา |
| OpenOCD `open failed` หรือเลือกบอร์ดผิด | เสียบ ST-Link ไว้ตัวเดียว ปิดโปรแกรมอื่นที่ใช้บอร์ดอยู่ |
| campaign บอกว่า port busy | รอบ B6 ห้ามใส่ `--serial` ใน capture |
| `.ps1 cannot be loaded` | ใช้คำสั่งแบบ `powershell -ExecutionPolicy Bypass -File ...` ตามคู่มือ |
| ไฟ F411 ไม่กระพริบตาม poll | สาย link สลับกัน ให้เช็คตาราง 3.2 |
