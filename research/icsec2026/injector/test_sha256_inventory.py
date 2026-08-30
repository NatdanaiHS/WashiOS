import csv
import hashlib
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


INJECTOR_DIR = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "create_sha256_inventory", INJECTOR_DIR / "create_sha256_inventory.py"
)
assert SPEC is not None and SPEC.loader is not None
inventory = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = inventory
SPEC.loader.exec_module(inventory)


class InventoryTests(unittest.TestCase):
    def test_hashes_sorted_files_and_excludes_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            data = root / "data"
            data.mkdir()
            (data / "b.bin").write_bytes(b"b")
            (data / "a.bin").write_bytes(b"a")
            output = data / "SHA256SUMS.csv"
            count = inventory.create_inventory(root, [data], output)
            self.assertEqual(2, count)
            with output.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(["data/a.bin", "data/b.bin"], [row["path"] for row in rows])
            self.assertEqual(hashlib.sha256(b"a").hexdigest().upper(), rows[0]["sha256"])
            with self.assertRaises(FileExistsError):
                inventory.create_inventory(root, [data], output)


if __name__ == "__main__":
    unittest.main()
