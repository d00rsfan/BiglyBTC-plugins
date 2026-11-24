#!/usr/bin/env python3
"""Archive explicitly selected files from a tested plugin build."""

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import tempfile


def run(*args, **kwargs):
    return subprocess.check_output(args, text=True, timeout=30,
                                   env=dict(os.environ, LC_ALL="C"), **kwargs).strip()


def files(directory, names, suffix):
    for name in names.split():
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", name) or not name.endswith(suffix):
            raise ValueError(f"Unexpected package filename: {name}")
        path = directory / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Expected a regular build input: {path}")
        yield path


def pack(source, build, output, component, kind, run_number, libraries, headers, core):
    if not re.fullmatch("[A-Za-z][A-Za-z0-9-]*", component):
        raise ValueError("Invalid component identifier")
    if kind not in {"module", "host-library"}:
        raise ValueError("Invalid component kind")
    if not re.fullmatch("[1-9][0-9]*", run_number):
        raise ValueError("Expected a positive workflow run number")
    if run("dpkg", "--print-architecture") != "amd64":
        raise ValueError("Expected an amd64 package build")
    cache = (build / "CMakeCache.txt").read_text()
    if not re.search(r"^CMAKE_BUILD_TYPE:STRING=Release$", cache, re.MULTILINE):
        raise ValueError("A Release build is required")

    source_revision = run("git", "rev-parse", "HEAD", cwd=source)
    if source_revision != os.environ["GITHUB_SHA"]:
        raise ValueError("Unexpected source revision")
    project_version = re.search(r"^CMAKE_PROJECT_VERSION:STATIC=([0-9]+\.[0-9]+\.[0-9]+)$", cache, re.MULTILINE)
    if not project_version:
        raise ValueError("Expected a three-part project version")
    version = f"{project_version[1]}.{run_number}"
    expected_suffix = ".so" if kind == "module" else ".a"
    inputs = list(files(build, libraries, expected_suffix))
    public_headers = list(files(source, headers, ".hpp"))
    if (not inputs or len(inputs) != len(set(inputs)) or
            len(public_headers) != len(set(public_headers))):
        raise ValueError("Library and header inputs must be nonempty where required and unique")
    if kind == "module" and len(inputs) != 1:
        raise ValueError("Expected a single loadable module")
    if kind == "host-library" and not public_headers:
        raise ValueError("The caller needs the public headers of the host library")
    for library in inputs:
        if kind == "module":
            header = run("readelf", "-h", library)
            if not re.search(r"Type:\s+DYN", header) or not re.search(r"Machine:.*X86-64", header):
                raise ValueError(f"Expected an amd64 ELF module: {library}")
            if not re.search(r"\bGLOBAL\s+DEFAULT\s+\d+\s+biglybtc_plugin_entry$",
                             run("readelf", "--dyn-syms", "--wide", library), re.MULTILINE):
                raise ValueError("Missing SDK entry point")
        elif not run("ar", "t", library):
            raise ValueError(f"Expected a nonempty static archive: {library}")

    package_name = f"{component}-{version}-ubuntu-26.04-amd64"
    output.mkdir()
    with tempfile.TemporaryDirectory(prefix="biglybtc-component-") as temporary:
        payload = Path(temporary) / package_name
        (payload / "lib").mkdir(parents=True)
        for library in inputs:
            shutil.copyfile(library, payload / "lib" / library.name)
        if public_headers:
            (payload / "include").mkdir()
            for header in public_headers:
                shutil.copyfile(header, payload / "include" / header.name)
        for name in ("LICENSE", "README.md", "SOURCE_PROVENANCE.json"):
            shutil.copyfile(source / name, payload / name)
        if (source / "NOTICE.md").is_file():
            shutil.copyfile(source / "NOTICE.md", payload / "NOTICE.md")
        if core:
            prefix = Path(core).resolve(strict=True)
            if not (prefix / "include/biglybtc/bencode.hpp").is_file():
                raise ValueError("Expected an installed BiglyBTCCore prefix")
            shutil.copytree(prefix, payload / "dependencies/biglybtc-core")
        metadata = {
            "component": component,
            "kind": kind,
            "version": version,
            "platform": "ubuntu-26.04-amd64",
            "revision": source_revision,
            "repository": os.environ["GITHUB_REPOSITORY"],
            "run": int(os.environ["GITHUB_RUN_ID"]),
            "libraries": [f"lib/{library.name}" for library in inputs],
        }
        (payload / "build.json").write_text(json.dumps(metadata, indent=2) + "\n")

        archive = output / (package_name + ".tar.gz")
        with tarfile.open(archive, "w:gz") as stream:
            stream.add(payload, arcname=package_name)
        with tarfile.open(archive, "r:gz") as stream:
            for member in [*metadata["libraries"], "build.json", "LICENSE", "SOURCE_PROVENANCE.json"]:
                if not stream.getmember(f"{package_name}/{member}").isfile():
                    raise ValueError(f"Missing package member: {member}")
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        (output / "SHA256SUMS").write_text(f"{digest}  {archive.name}\n")
    print(f"Packaged {package_name}")


if __name__ == "__main__":
    environment = os.environ
    component = environment["COMPONENT"]
    output = Path(environment["RUNNER_TEMP"]) / f"{component}-component-package"
    pack(Path(environment["GITHUB_WORKSPACE"]), Path(environment["BUILD_DIR"]), output,
         component, environment["KIND"], environment["GITHUB_RUN_NUMBER"],
         environment["LIBRARIES"], environment["HEADERS"], environment["DEPENDENCY_PREFIX"])
    with Path(environment["GITHUB_OUTPUT"]).open("a") as github_output:
        print(f"directory={output}", file=github_output)
