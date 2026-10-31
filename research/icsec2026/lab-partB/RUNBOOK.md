# Part B — คู่มือวันแล็บ (B1–B6)

ทำตามลำดับจากบนลงล่าง ทุกคำสั่งรันใน **PowerShell ของ VS Code** ที่โฟลเดอร์ `C:\MyOS\WashiOS-lab`
(VS Code: File → Open Folder → `C:\MyOS\WashiOS-lab` แล้วเปิด Terminal → New Terminal)

กฎ evidence: ทุกการวัดเริ่มด้วย `labtool.py new ...` (สร้างโฟลเดอร์ใหม่ชื่อไม่ซ้ำ) และจบด้วย `labtool.py close ...`
(เขียน `INVENTORY.sha256`) ห้ามใช้ run เดิมซ้ำ ถ้าพลาดกลางทาง ให้ close พร้อม `--note "ABORTED: เหตุผล"` แล้วสร้างใหม่

> **คาดไว้ก่อน (อ่านก่อนเริ่ม):** ตอนเตรียมโค้ดพบว่า RAM ที่ bootloader ใช้เก็บ `BootMetadata` (0x20000018)
> ถูก `.data` ของแอป (0x20000000–0x20000088) เขียนทับตอนแอปบูต และ `FaultLog` ของ bootloader (0x20000050)
> กับของแอป (0x20000088) อยู่คนละที่ ผลที่น่าจะเห็นบนบอร์ดจริง:
> - **B3:** หลัง IWDG reset บอร์ด**อาจรันแอปใหม่เอง** แทนที่จะค้างใน beacon (ขัดกับ B6/F2)
> - **B4 โหมด `system`:** จำนวนครั้งที่บูต (boot count) ไม่สะสมข้ามรอบ แต่โหมด `policy` (แอปไม่ได้รัน) ควรตรงกับโมเดล
>
> ถ้าเห็นแบบนี้ **ไม่ใช่ว่าต่อสายผิด** นี่คือผลการทดลองจริง ให้เก็บไว้ตามปกติ ยังไม่ได้แก้โค้ดส่วนนี้ เพราะต้องการวัดของเดิมก่อน

---

## 0. เตรียมของ (ทำครั้งเดียว ~60 นาที)

### 0.1 ของที่ต้องมี
- NUCLEO-G431RB (controller, เรียกว่า **G431**) และ NUCLEO-G474RE (payload, เรียกว่า **G474**)
- สาย Micro-USB 2 เส้น (บอร์ดละเส้น) + สาย USB ของ logic analyzer
- Logic analyzer 8 ช่อง (คู่มือนี้เขียนสำหรับรุ่น "USB Logic Analyzer 24MHz 8CH" ที่ใช้ชิป FX2 ซึ่งเป็นรุ่นที่พบบ่อยที่สุด
  ถ้าบนกล่องเขียนว่า Saleae แท้ หรือรุ่นอื่น ให้ตรวจสอบรุ่นก่อน)
- สาย Dupont ตัวผู้-ตัวผู้ ประมาณ 15 เส้น (หัวสายของ analyzer เป็นตัวเมีย และ header Arduino บนบอร์ดก็เป็นตัวเมีย
  จึงต้องใช้สายตัวผู้-ตัวผู้มาเชื่อมระหว่างกัน)

### 0.2 ตรวจ Python
```powershell
python --version
python -c "import serial; print('pyserial OK')"
```
ถ้าไม่มี pyserial: `python -m pip install pyserial`

### 0.3 ลงโปรแกรม logic analyzer (sigrok)
1. เข้า https://sigrok.org/wiki/Downloads → หัวข้อ Windows
2. ดาวน์โหลดและติดตั้ง **PulseView** (64-bit installer) แล้วกด Next ไปจนจบ
3. ดาวน์โหลดและติดตั้ง **sigrok-cli** (64-bit installer) แล้วกด Next ไปจนจบ
   (ต้องลง sigrok-cli ด้วย เพราะสคริปต์อัดผ่าน sigrok-cli ซึ่งอัดยาว 10 นาทีได้โดยไม่กิน RAM)

### 0.4 ลงไดรเวอร์ให้ analyzer (Zadig)
1. เสียบ analyzer เข้า USB
2. เปิด Start → พิมพ์ **Zadig** (ติดมากับ PulseView, อยู่ที่ `C:\Program Files\sigrok\PulseView\zadig.exe`)
3. เมนู **Options → List All Devices** ให้มีเครื่องหมายถูก
4. ใน dropdown เลือกอุปกรณ์ที่ชื่อ `fx2lafw` หรือ `Unknown Device` (USB ID **0925 3881**). **ห้ามเลือก ST-Link หรือเมาส์/คีย์บอร์ด**
5. ช่องขวาของลูกศรเลือก **WinUSB** แล้วกด **Install Driver** (หรือ Replace Driver) รอจนขึ้น success
6. ถอดแล้วเสียบ analyzer ใหม่

### 0.5 ทดสอบ analyzer
```powershell
python research\icsec2026\lab-partB\labtool.py check
```
ต้องขึ้น `Analyzer OK.` ถ้าไม่ขึ้น ให้ทำข้อ 0.4 ใหม่

ลองดูด้วยตา (ไม่บังคับ): เปิด PulseView → dropdown ซ้ายบนเลือก **fx2lafw** → ตั้ง 1 MHz, 1 M samples → กด **Run**
ต้องเห็นเส้น D0–D7 ปิดโปรแกรม PulseView ก่อนใช้สคริปต์ทุกครั้ง (ใช้ analyzer พร้อมกันสองโปรแกรมไม่ได้)

### 0.6 Build (ทำไว้ให้แล้ว แต่ถ้าแก้โค้ดต้องรันใหม่)
```powershell
$pio = "$env:USERPROFILE\.platformio\penv\Scripts\pio.exe"
cd core; & $pio run -e nucleo_g431rb_payload_demo_lab -e nucleo_g431rb_payload_demo_stall_link -e nucleo_g431rb_payload_demo_stall_heartbeat -e nucleo_g431rb_payload_demo_lab_slot_b; cd ..
cd demo-payload; & $pio run -e nucleo_g474re_lab; cd ..
```

### 0.7 Flash firmware ชุด lab (**เสียบทีละบอร์ด**)
ถ้าเสียบสองบอร์ดพร้อมกัน OpenOCD จะเลือกบอร์ดผิดได้

**G431** (เสียบเฉพาะ G431) จะ build และ flash ทั้ง core + bootloader ที่ provision CRC แล้ว:
```powershell
powershell -ExecutionPolicy Bypass -File .\tools\flash_payload_demo.ps1 -CoreEnv nucleo_g431rb_payload_demo_lab -BootloaderEnv nucleo_g431rb_payload_demo_lab
```
ต้องจบด้วย `Payload demo firmware flashed and started.` และไฟ LED เขียว (LD2) กระพริบทุกครึ่งวินาที

**G474** (ถอด G431 ออกก่อน แล้วเสียบเฉพาะ G474):
```powershell
cd demo-payload; & $pio run -e nucleo_g474re_lab -t upload; cd ..
```

### 0.8 หา COM port
เสียบทีละบอร์ด แล้วดูว่ามี COM ใหม่เพิ่มขึ้นมาตัวไหน:
```powershell
& $pio device list
```
มองหา `STMicroelectronics STLink Virtual COM Port` แล้วจดไว้:
`G431 = COM__` , `G474 = COM__` (COM3/COM4 ที่เป็น Bluetooth ไม่เกี่ยว)

---

## 1. ต่อสาย — Setup A (ใช้กับ B1, B2, B5, B6)

**ถอด USB ทุกเส้นก่อนต่อหรือย้ายสายทุกครั้ง**

### 1.1 สาย link ระหว่างบอร์ด (ของเดิม ตรวจว่ายังต่ออยู่)
| G431 | G474 |
|---|---|
| D1 (PC4, TX) | D0 (PC5, RX) |
| D0 (PC5, RX) | D1 (PC4, TX) |
| GND | GND |

ห้ามต่อ 3V3 หรือ 5V ข้ามบอร์ด แต่ละบอร์ดใช้ไฟจาก USB ของตัวเอง

### 1.2 สาย analyzer
ชื่อขา D0…D13 พิมพ์อยู่ข้าง header สีดำบนบอร์ด ส่วน analyzer มีป้ายที่สาย/ตัวกล่องว่า CH0…CH7 (หรือ D0…D7) และ GND

| Analyzer | บอร์ด | ขาบนบอร์ด | สัญญาณ |
|---|---|---|---|
| CH0 | G431 | **D2** | poll (toggle ทุกครั้งที่ส่ง poll) |
| CH1 | G431 | **D4** | loop (toggle ทุกรอบของ task) |
| CH2 | G431 | **D5** | status (high ระหว่าง reportStatus) |
| CH3 | G431 | **D6** | write (high ระหว่างเขียน console) |
| CH4 | G431 | **D8** | accept (toggle ทุกครั้งที่รับ frame ผ่าน) |
| CH5 | G431 | **D7** | timeout (ขึ้น high เมื่อตรวจเจอ timeout) |
| CH6 | G431 | **D9** | recovery (toggle ทุกครั้งที่ recovered) |
| CH7 | **G474** | **D8** | pl_fault (high ระหว่างอยู่ใน fault mode) |
| GND | G431 | **GND** (รูไหนก็ได้ที่เขียน GND) | ground ร่วม |

ระวัง: บน **G431** ขา **D7** คือ timeout และ **D8** คือ accept อย่าสลับกัน

### 1.3 เสียบไฟ
เสียบ G431, G474 และ analyzer เข้า USB ทั้งสามตัว ไฟ LD2 บน G474 ควรกระพริบตาม poll

---

## 2. Session 1 — B1 + B2 + B5 (NORMAL ยาว 11 นาที) แล้วตามด้วย B6

### 2.1 ทดสอบสั้นก่อน (smoke test 30 วินาที)
```powershell
$lab = "research\icsec2026\lab-partB\labtool.py"
$run = python $lab new trial smoke-setupA --flashed "G431 lab + G474 lab"
python $lab capture $run --setup A --seconds 30
python $lab analyze $run
python $lab close $run --note "smoke test only"
```
ดูบรรทัด `"signals"`: poll ควรมีประมาณ 60, loop เป็นหลักหมื่น, status 6 ขึ้นไป, write 6 ขึ้นไป, accept ประมาณ 60
**ถ้าช่องไหนเป็น 0 หรือ 1 แปลว่าสายช่องนั้นหลุดหรือเสียบผิดขา** ให้แก้แล้วทำ smoke test ใหม่ (run ใหม่)

### 2.2 B1/B2/B5 — อัด 11 นาที (ได้ status report มากกว่า 120 ครั้ง)
ระหว่างนี้ห้ามแตะบอร์ดและห้ามกดปุ่ม payload
```powershell
$run = python $lab new B1B2B5 normal-11min --flashed "G431 lab + G474 lab"
python $lab capture $run --setup A --seconds 660 --serial COM_G431:g431 --serial COM_G474:g474
python $lab analyze $run --test B1 --test B2 --test B5
python $lab close $run
```
(แทน `COM_G431` และ `COM_G474` ด้วยเลข COM จากข้อ 0.8 เช่น `COM7:g431`)

สิ่งที่ได้ (ไฟล์ `analysis_B1_B2_B5.json`):
- **B1:** `poll_period_regular` เทียบกับ `poll_period_containing_status_report` โดย `max_abs_dev_ms` คือค่า J ที่วัดได้
- **B2:** `status_span` / `status_write_span` / `next_poll_slip_after_status` ถ้า slip เท่ากับระยะเวลาของ status write
  แปลว่าสาเหตุคือ console write แบบ blocking (`HAL_UART_Transmit` เป็น busy-wait และ 120 ไบต์ที่ 115200 ใช้ประมาณ 10.4 ms)
  ดูช่อง `writes_at_or_over_10ms_uart_timeout` ด้วย ถ้ามีค่ามากกว่า 0 แปลว่าบรรทัด status ถูกตัดเพราะชน timeout 10 ms
- **B5:** `poll_to_accept` คือ T_tx ที่วัดตรงด้วยเวลาของ MCU

### 2.3 B6 — campaign recovery ขนาดเล็ก (15 trial, ใช้เวลาประมาณ 4 นาที)
ต้องใช้ **2 terminal** (ใน VS Code กดปุ่ม `+` ที่แถบ Terminal)

**Terminal 1** เริ่มอัดก่อน (รอบนี้ไม่ต้องใส่ `--serial` เพราะ campaign ใช้ COM port อยู่):
```powershell
$lab = "research\icsec2026\lab-partB\labtool.py"
$run = python $lab new B6 recovery-15trials --flashed "G431 lab + G474 lab"
$run   # จดชื่อนี้ไว้
python $lab capture $run --setup A --seconds 420
```
**Terminal 2** เริ่มภายใน 10 วินาทีหลังจาก Terminal 1 ขึ้นคำว่า Recording:
```powershell
python research\icsec2026\injector\run_payload_campaign.py --campaign labB6_20261101_s20261101 --seed 20261101 --g431-port COM_G431 --g474-port COM_G474 --repetitions 5
```
(ชื่อ `--campaign` และ `--seed` ต้องใหม่ทุกครั้ง ถ้าทำซ้ำให้เปลี่ยนเลข)

campaign เสร็จก่อน capture ไม่เป็นไร รอให้ capture ครบ 420 วินาที แล้วใน Terminal 1:
```powershell
python $lab analyze $run --test B6
python $lab close $run --note "campaign dir: research/icsec2026/runs/labB6_20261101_s20261101"
```
ดูผล: `recovery_interval` คือเวลาจาก payload ยืนยัน NORMAL ถึง controller recovered (เวลาของ MCU)
ส่วน `recoveries_over_500ms` ให้ดูว่ามีกรณีแบบ R085 (523 ms) เกิดซ้ำหรือไม่ แล้วเทียบลำดับ trial กับ `run_plan.csv` ในโฟลเดอร์ campaign

---

## 3. Session 2 — B3 Watchdog stall injection

### 3.1 Flash firmware stall (ถอด G474 USB ออกก่อน แล้วเสียบเฉพาะ G431)
```powershell
powershell -ExecutionPolicy Bypass -File .\tools\flash_payload_demo.ps1 -CoreEnv nucleo_g431rb_payload_demo_stall_link -BootloaderEnv nucleo_g431rb_payload_demo_stall_link
```
firmware ตัวนี้จะทำให้ **PayloadLink task หยุดเองหลังบูต 10 วินาที**

### 3.2 ต่อสาย — Setup B (ถอด USB ทั้งหมดก่อน)
ถอดสาย analyzer ของ Setup A ออก แล้วต่อใหม่ตามตารางนี้ ส่วนสาย link ระหว่างบอร์ดปล่อยไว้ได้

| Analyzer | G431 ขา | สัญญาณ |
|---|---|---|
| CH0 | **D10** | stall (ขึ้น high ตอนเริ่ม stall) |
| CH1 | **D11** | wdrec (ขึ้น high ตอนบันทึก WATCHDOG_TIMEOUT) |
| CH2 | **RESET** (header ตัวเมียฝั่งไฟเลี้ยง: รูที่เขียนว่า RESET ซึ่งอยู่ถัดจาก IOREF และก่อน 3V3; ห้ามเสียบรู 3V3/5V/VIN) | nrst (pulse ลงตอน reset) |
| CH3 | **D13** | led (heartbeat หรือ beacon) |
| CH4 | **D4** | loop (มีการเปลี่ยนเฉพาะตอนแอปรันอยู่) |
| GND | **GND** | |

CH5–CH7 ปล่อยว่าง

### 3.3 วัด (payload-link stall)
เสียบ G431 และ analyzer (G474 จะเสียบหรือไม่ก็ได้)
```powershell
$run = python $lab new B3link stall-payloadlink --flashed "G431 stall_link"
python $lab capture $run --setup B --seconds 300 --serial COM_G431:g431
```
ระหว่างที่อัด 300 วินาที **ให้สังเกตไฟ LD2 บน G431**:
- **กรณี A, บอร์ดรันแอปเองใหม่** (LED กลับมากระพริบช้าทุกครึ่งวินาที แล้วอีก 10 วินาทีก็ stall อีก): ไม่ต้องทำอะไรเลย
  ระบบจะวนเป็น trial อัตโนมัติประมาณ 20 รอบใน 300 วินาที
- **กรณี B, LED กระพริบเร็วไม่หยุด (beacon) และแอปไม่กลับมา:**
  1. รอให้ beacon ขึ้นประมาณ 3 วินาที แล้วกดปุ่ม **RESET สีดำ** หนึ่งครั้ง LED ต้องยังกระพริบเร็วอยู่ (ยืนยันว่า warm reset ไม่ relaunch)
  2. ถอดแล้วเสียบ USB ของ G431 ใหม่ (power cycle) เพื่อเริ่ม trial ถัดไป
  3. ทำซ้ำจนได้ 10 trial (ใช้เวลาประมาณ 15 วินาทีต่อ trial)

แล้วรัน:
```powershell
python $lab analyze $run --test B3
python $lab close $run --note "observed: กรณี A หรือ B (เขียนสิ่งที่เห็น)"
```
ดูผล: `stall_to_record` เทียบกับ W3 (952 ms), `record_to_reset` เทียบกับ IWDG สูงสุด 2170 ms,
และ `relaunched_without_power_cycle` ที่บอกว่าแต่ละ trial แอปรันใหม่หลัง reset หรือไม่

### 3.4 ทำซ้ำกับ heartbeat stall
flash ตัว heartbeat:
```powershell
powershell -ExecutionPolicy Bypass -File .\tools\flash_payload_demo.ps1 -CoreEnv nucleo_g431rb_payload_demo_stall_heartbeat -BootloaderEnv nucleo_g431rb_payload_demo_stall_heartbeat
$run = python $lab new B3heartbeat stall-heartbeat --flashed "G431 stall_heartbeat"
python $lab capture $run --setup B --seconds 300 --serial COM_G431:g431
python $lab analyze $run --test B3
python $lab close $run --note "observed: ..."
```
รอบนี้ LED จะหยุดกระพริบตอน stall (เพราะ heartbeat เป็นตัวกระพริบ LED) และ `stall_to_record` เทียบกับ W3 1652 ms

---

## 4. Session 3 — B4 Boot-policy fault injection (ไม่ต้องใช้ analyzer)

**ถอด USB ของ G474 ออก** ให้เหลือ ST-Link ตัวเดียว (ของ G431) สาย analyzer ปล่อยไว้ได้

### 4.1 Flash firmware lab กลับมา + เขียน slot B
```powershell
powershell -ExecutionPolicy Bypass -File .\tools\flash_payload_demo.ps1 -CoreEnv nucleo_g431rb_payload_demo_lab -BootloaderEnv nucleo_g431rb_payload_demo_lab
$bf = "research\icsec2026\lab-partB\bootfault.py"
$run = python $lab new B4 boot-policy-fixed --flashed "G431 lab, fixed bootloader, slot B = lab_slot_b"
python $bf $run prepare-slot-b
python $bf $run read
```
`read` จะแสดง BootMetadata ทั้ง 13 ช่อง และบรรทัด `valid:` ถ้าขึ้น `valid: False` ตอนที่แอปรันอยู่ แปลว่า metadata ถูกแอปเขียนทับ (ตรงกับที่คาดไว้ด้านบน)

### 4.2 Scenario (bootloader ที่แก้แล้ว)
แต่ละคำสั่งรันเองอัตโนมัติ (reset, ฉีด fault, อ่าน metadata ผ่าน SWD, คืน flash) และพิมพ์บรรทัด `expect:` มาให้เทียบ
```powershell
python $bf $run scenario a                      # A เสีย → ต้อง LAUNCHED_B
python $bf $run scenario b                      # A และ B เสีย → ต้อง SAFE_LOOP (NoValidFirmwareSlot)
python $bf $run scenario c --resets 6           # B Pending → LAUNCHED_B 4 ครั้ง แล้ว SAFE_LOOP (BootLoopLimit)
python $bf $run scenario d --k 1 --resets 6
python $bf $run scenario d --k 2 --resets 6
python $bf $run scenario d --k 3 --resets 6     # fixed: B ต้องได้ 4 ครั้งทุกค่า k
python $bf $run scenario c --mode system --resets 6
python $bf $run scenario d --k 2 --mode system --resets 6
python $lab close $run
```
- โหมด `policy` (ค่าเริ่มต้น): หยุดทันทีที่ bootloader กระโดดเข้าแอป แอปจึงไม่ได้รัน เป็นการทดสอบตรรกะของ bootloader อย่างเดียว
- โหมด `system`: ปล่อยให้แอปรัน 2 วินาทีระหว่างการ reset แต่ละครั้ง เป็นการทดสอบทั้งระบบ ผลจะต่างจาก policy ได้เพราะเรื่อง RAM ที่ถูกเขียนทับ

### 4.3 Scenario d บน bootloader ก่อนแก้ (pre-fix)
build ไว้ให้แล้วที่ `C:\MyOS\WashiOS-prefix-bootloader` (commit `c8ab6f6^`, provision ด้วย CRC เดียวกัน)
```powershell
$run = python $lab new B4 boot-policy-prefix --flashed "G431 lab, PRE-FIX bootloader c8ab6f6^"
python $bf $run flash-bootloader prefix
python $bf $run scenario d --k 1 --resets 6 --bootloader prefix
python $bf $run scenario d --k 2 --resets 6 --bootloader prefix
python $bf $run scenario d --k 3 --resets 6 --bootloader prefix   # pre-fix: B ได้ 4−k ครั้ง
python $bf $run scenario c --resets 6 --bootloader prefix
python $bf $run flash-bootloader fixed                            # คืน bootloader ตัวที่แก้แล้ว
python $lab close $run
```
ผลละเอียดทุก reset อยู่ใน `b4_events.jsonl` ในโฟลเดอร์ run (มี metadata ก่อนและหลังทุกครั้ง)

---

## 5. ปิดวัน
1. ตรวจว่าทุก run ใน `research\icsec2026\lab-partB\runs\` มี `INVENTORY.sha256` (คือ close แล้ว)
2. Flash firmware ปกติกลับ (ถ้าต้องการ):
   `powershell -ExecutionPolicy Bypass -File .\tools\flash_payload_demo.ps1` (G431), `cd demo-payload; & $pio run -e nucleo_g474re -t upload` (G474)
3. ส่งโฟลเดอร์ `runs\` หรือ path เพื่อสรุปผลเทียบกับ E1/E2/W3/W5/W6/B3/B4/B6/F2/F4

## แก้ปัญหา
| อาการ | ทำอะไร |
|---|---|
| `labtool check` ไม่เจอ fx2lafw | ทำ Zadig ใหม่ (0.4), ปิด PulseView, เปลี่ยนพอร์ต USB |
| capture ขึ้น error เรื่อง samplerate | ใส่ `--rate 1m` (ค่าเริ่มต้นอยู่แล้ว) หรือลองพอร์ต USB 2.0 ด้านหลังเครื่อง |
| ช่องใดช่องหนึ่งนับได้ 0 | สายหลุดหรือเสียบผิดขา ให้ดูตารางอีกครั้ง |
| OpenOCD: `Error: open failed` | ST-Link ไม่เจอ ตรวจว่าเสียบบอร์ดเดียว ปิด serial monitor หรือ STM32CubeProgrammer ที่เปิดค้างไว้ |
| OpenOCD เลือกบอร์ดผิด | เหลือ USB บอร์ดเดียว หรือใส่ `--stlink-serial <serial>` |
| `run_payload_campaign` บอกว่า port busy | ปิด capture ที่เปิด `--serial` อยู่ (รอบ B6 ห้ามใส่ `--serial`) |
| `.ps1 cannot be loaded` | ใช้คำสั่งแบบ `powershell -ExecutionPolicy Bypass -File ...` ตามคู่มือนี้ |
