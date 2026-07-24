from pathlib import Path
import struct
import subprocess

Import("env")


CRC32_NIBBLE_TABLE = (
    0x00000000,
    0x1DB71064,
    0x3B6E20C8,
    0x26D930AC,
    0x76DC4190,
    0x6B6B51F4,
    0x4DB26158,
    0x5005713C,
    0xEDB88320,
    0xF00F9344,
    0xD6D6A3E8,
    0xCB61B38C,
    0x9B64C2B0,
    0x86D3D2D4,
    0xA00AE278,
    0xBDBDF21C,
)


def project_path(option_name, default_value):
    raw_value = env.subst(str(env.GetProjectOption(option_name, default_value)))
    path = Path(raw_value)
    if not path.is_absolute():
        path = Path(env.subst("$PROJECT_DIR")) / path
    return path.resolve()


def project_int(option_name, default_value):
    return int(str(env.GetProjectOption(option_name, default_value)), 0)


def crc32(data):
    crc = 0xFFFFFFFF
    for value in data:
        crc ^= value
        crc = ((crc >> 4) ^ CRC32_NIBBLE_TABLE[crc & 0x0F]) & 0xFFFFFFFF
        crc = ((crc >> 4) ^ CRC32_NIBBLE_TABLE[crc & 0x0F]) & 0xFFFFFFFF
    return (~crc) & 0xFFFFFFFF


def objcopy_to_binary(source_elf, output_bin):
    objcopy = env.subst("$OBJCOPY")
    if not objcopy or objcopy == "$OBJCOPY":
        objcopy = "arm-none-eabi-objcopy"

    result = subprocess.run(
        [objcopy, "-O", "binary", str(source_elf), str(output_bin)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(
            "WashiBoot provisioning failed while converting Slot A ELF to binary:\n"
            + result.stderr
        )


def validate_vector_table(data, slot_base, slot_length):
    if len(data) < 8:
        raise SystemExit("WashiBoot provisioning failed: Slot A image is too small.")

    initial_stack, reset_handler = struct.unpack_from("<II", data, 0)
    reset_handler_address = reset_handler & ~0x1
    ram_base = project_int("custom_washiboot_ram_base", "0x20000000")
    ram_length = project_int("custom_washiboot_ram_length", "0x8000")

    stack_in_ram = ram_base <= initial_stack <= (ram_base + ram_length)
    reset_in_slot = slot_base <= reset_handler_address < (slot_base + slot_length)
    reset_is_thumb = (reset_handler & 0x1) == 0x1

    if not stack_in_ram or not reset_in_slot or not reset_is_thumb:
        raise SystemExit(
            "WashiBoot provisioning failed: Slot A vector table is invalid. "
            f"SP=0x{initial_stack:08X}, reset=0x{reset_handler:08X}."
        )


slot_a_elf = project_path(
    "custom_washiboot_slot_a_elf",
    "../core/.pio/build/nucleo_g431rb/firmware.elf",
)
slot_a_base = project_int("custom_washiboot_slot_a_base", "0x08004000")
slot_a_length = project_int("custom_washiboot_slot_a_length", "0xE000")

if not slot_a_elf.exists():
    raise SystemExit(
        "WashiBoot provisioning failed: Slot A firmware ELF was not found at "
        f"{slot_a_elf}. Build the matching core environment first."
    )

build_dir = Path(env.subst("$BUILD_DIR"))
build_dir.mkdir(parents=True, exist_ok=True)
slot_a_bin = build_dir / "slot_a_provision.bin"
objcopy_to_binary(slot_a_elf, slot_a_bin)

slot_a_data = slot_a_bin.read_bytes()
if len(slot_a_data) > slot_a_length:
    raise SystemExit(
        "WashiBoot provisioning failed: Slot A image is too large "
        f"({len(slot_a_data)} bytes > {slot_a_length} bytes)."
    )

validate_vector_table(slot_a_data, slot_a_base, slot_a_length)
slot_a_crc = crc32(slot_a_data)

env.Append(
    CPPDEFINES=[
        ("WASHIBOOT_DEFAULT_EXPECTED_CRC32", f"0x{slot_a_crc:08X}UL"),
        ("WASHIBOOT_DEFAULT_SLOT_A_CRC_LENGTH", f"{len(slot_a_data)}UL"),
    ]
)

print(
    "WashiBoot: provisioned Slot A "
    f"{slot_a_elf.name}, {len(slot_a_data)} bytes, CRC32=0x{slot_a_crc:08X}"
)
