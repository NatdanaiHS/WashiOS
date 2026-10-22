# Toolchain for the formal package

State on 2026-09-08: UPPAAL 5.0.0 installed at `/opt/uppaal` (`/usr/bin/uppaal`, `/opt/uppaal/bin/verifyta`), OpenJDK 17 present. The verifier licence is **not yet activated**.

## UPPAAL (required)

1. Install a JDK 17 or newer. Arch Linux: `sudo pacman -S jdk-openjdk`. Windows: any Temurin/OpenJDK MSI.
2. Download UPPAAL 5.x from https://uppaal.org/downloads/ and obtain the free academic licence key
   from the same site (the key is tied to an e-mail; do not commit it).
3. Unpack; `verifyta` lives in `bin/` (Linux: `bin-Linux/verifyta`; Windows: `bin-Windows\verifyta.exe`).
4. First run: `/opt/uppaal/bin/verifyta -k <KEY>` once to store the licence (the lease renews online every 48 h by default; `-l <hours>` changes it), then `verifyta -v`.
5. Record the version string; `run_verifyta.sh` writes it to `results/<stamp>/verifyta_version.txt`.

Run everything:

```bash
research/icsec2026/formal/tooling/run_verifyta.sh          # defaults to /opt/uppaal/bin/verifyta
```

Open a model in the GUI for editing or simulation: `uppaal research/icsec2026/formal/models/payload_link.xml`.
Before running, replace `FAULT_SELECT`, `SCENARIO_SELECT`, `APP_CONFIRMS_SELECT` placeholders manually if you
load the raw file in the GUI; the script patches them for batch runs.

## Conformance replay (no extra tools)

```bash
python3 research/icsec2026/formal/conformance/check_frozen_traces.py
python3 -m unittest discover -s research/icsec2026/formal/conformance -p 'test_*.py'
```

## Manuscript

Tectonic 0.17.0 as before (`tmp/pdfs/` on the Windows machine; `tectonic` on PATH on Linux). Build into
`research/icsec2026/submission/build/` (gitignored) and promote only after QA, per `research/icsec2026/README.md`.
