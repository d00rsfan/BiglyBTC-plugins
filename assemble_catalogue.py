#!/usr/bin/env python3
"""Assemble an unsigned catalogue from a qualified azlocprov build artifact."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import time

ASSET = "azlocprov-linux-amd64.tar.zst"
REPOSITORY = "d00rsfan/BiglyBTC-plugin-azlocprov"
FIELDS = {"id", "version", "platform", "qt", "minHostApi", "maxHostApi", "minHostAbi",
          "maxHostAbi", "bytes", "sha256", "nativeCommit", "upstreamCommit", "url"}


def assemble(artifact, revision, sequence, valid_days):
    if not re.fullmatch("[0-9a-f]{40}", revision) or sequence <= 0 or not 1 <= valid_days <= 90:
        raise ValueError("Expected a full source revision, positive sequence and 1 to 90 days")
    descriptor = artifact / "catalogue-entry.json"
    if not 0 < descriptor.stat().st_size <= 4096:
        raise ValueError("Unexpected catalogue entry size")
    entry = json.loads(descriptor.read_bytes())
    if not isinstance(entry, dict) or entry.keys() != FIELDS:
        raise ValueError("Unexpected catalogue entry fields")
    version = entry["version"]
    if not isinstance(version, str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+\.[1-9][0-9]*", version):
        raise ValueError("Expected a versioned CI plugin package")
    if (entry["id"], entry["platform"], entry["qt"], entry["nativeCommit"], entry["url"]) != (
            "azlocprov", "linux-amd64", "6.12.0", revision,
            f"https://github.com/{REPOSITORY}/releases/download/v{version}/{ASSET}"):
        raise ValueError("Plugin identity does not match the qualified build and release repository")
    if not isinstance(entry["upstreamCommit"], str) or not re.fullmatch("[0-9a-f]{40}", entry["upstreamCommit"]):
        raise ValueError("Missing immutable upstream revision")
    for key in ("minHostApi", "maxHostApi", "minHostAbi", "maxHostAbi"):
        if type(entry[key]) is not int or entry[key] != 1:
            raise ValueError("Unsupported SDK contract")
    asset = artifact / ASSET
    if type(entry["bytes"]) is not int or not 0 < asset.stat().st_size == entry["bytes"] <= 64 * 1024 * 1024:
        raise ValueError("Invalid plugin asset size")
    with asset.open("rb") as file:
        if entry["sha256"] != hashlib.file_digest(file, "sha256").hexdigest():
            raise ValueError("Plugin artifact bytes differ from the catalogue entry")
    return {"schema": 1, "sequence": sequence, "expiresAt": int(time.time()) + valid_days * 86400,
            "releases": [entry]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path)
    parser.add_argument("revision")
    parser.add_argument("sequence", type=int)
    parser.add_argument("output", type=Path)
    parser.add_argument("--valid-days", type=int, default=30)
    args = parser.parse_args()
    result = assemble(args.artifact, args.revision, args.sequence, args.valid_days)
    with args.output.open("x") as file:
        json.dump(result, file, separators=(",", ":"))
        file.write("\n")
