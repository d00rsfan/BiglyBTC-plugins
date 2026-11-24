import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from assemble_catalogue import ASSET, REPOSITORY, assemble


class CatalogueTests(unittest.TestCase):
    def test_checked_package_and_refusals(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            asset = root / ASSET
            data = b"fixture artifact"
            asset.write_bytes(data)
            revision = "a" * 40
            version = "0.1.0.5"
            entry = {"id": "azlocprov", "version": version, "platform": "linux-amd64", "qt": "6.12.0",
                     "minHostApi": 1, "maxHostApi": 1, "minHostAbi": 1, "maxHostAbi": 1,
                     "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                     "nativeCommit": revision, "upstreamCommit": "b" * 40,
                     "url": f"https://github.com/{REPOSITORY}/releases/download/v{version}/{ASSET}"}
            (root / "catalogue-entry.json").write_text(json.dumps(entry))
            self.assertEqual(assemble(root, revision, 7, 30)["releases"], [entry])
            with self.assertRaises(ValueError):
                assemble(root, "c" * 40, 7, 30)
            with self.assertRaises(ValueError):
                assemble(root, revision, 0, 30)
            asset.write_bytes(data[::-1])
            with self.assertRaises(ValueError):
                assemble(root, revision, 7, 30)
