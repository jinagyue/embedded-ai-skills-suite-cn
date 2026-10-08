#!/usr/bin/env python3
"""Read-only dependency discovery; never connects to devices."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import shutil
import sys
from pathlib import Path


PACKAGES = {
    "pyserial": "core: serial observation",
    "pyelftools": "core: ELF analysis",
    "PyYAML": "optional: EIDE configuration",
    "python-can": "optional: CAN interfaces",
    "cantools": "optional: DBC decoding",
}
TOOLS = {
    "keil": ("UV4.exe",),
    "cmake": ("cmake",),
    "ninja": ("ninja",),
    "make": ("make", "mingw32-make"),
    "arm-gcc": ("arm-none-eabi-gcc",),
    "arm-gdb": ("arm-none-eabi-gdb",),
    "arm-addr2line": ("arm-none-eabi-addr2line",),
    "arm-size": ("arm-none-eabi-size",),
    "jlink": ("JLink.exe", "JLink", "JLinkExe"),
    "openocd": ("openocd",),
    "probe-rs": ("probe-rs",),
    "tshark": ("tshark",),
    "ssh": ("ssh",),
    "scp": ("scp",),
}


def common_locations(tool: str) -> list[Path]:
    if os.name != "nt":
        return []
    candidates = []
    if tool == "keil":
        candidates.extend(Path(drive + "/Keil_v5/UV4/UV4.exe") for drive in ("C:", "D:", "E:"))
    elif tool in {"jlink", "tshark"}:
        for key in ("ProgramFiles", "ProgramFiles(x86)"):
            location = os.environ.get(key)
            if not location:
                continue
            base = Path(location)
            if tool == "tshark":
                candidates.append(base / "Wireshark" / "tshark.exe")
            else:
                segger = base / "SEGGER"
                if segger.is_dir():
                    candidates.extend(segger.glob("JLink*/JLink.exe"))
    return candidates


def collect() -> dict:
    packages = {}
    for name, purpose in PACKAGES.items():
        try:
            version = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            version = None
        packages[name] = {"version": version, "available": version is not None, "purpose": purpose}
    tools = {}
    for name, aliases in TOOLS.items():
        path = next((found for alias in aliases if (found := shutil.which(alias))), None)
        if path is None:
            path = next((str(p) for p in common_locations(name) if p.is_file()), None)
        tools[name] = {"path": path, "available": path is not None}
    extensions = Path.home() / ".vscode" / "extensions"
    builders = sorted(str(p) for p in extensions.glob("cl.eide-*/res/tools/win32/unify_builder/unify_builder.exe")) if extensions.is_dir() else []
    tools["eide-unify-builder"] = {"path": builders[0] if builders else None, "available": bool(builders)}
    return {
        "python": {"version": sys.version.split()[0], "executable": sys.executable},
        "packages": packages,
        "tools": tools,
        "core_packages_ready": all(packages[n]["available"] for n in ("pyserial", "pyelftools")),
        "note": "Not discovered means absent from PATH and checked common locations. Drivers and hardware were not tested.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = collect()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("Python:", result["python"]["version"])
        for name, value in result["packages"].items():
            print(name + ":", value["version"] or "not installed")
        for name, value in result["tools"].items():
            print(name + ":", value["path"] or "not discovered")


if __name__ == "__main__":
    main()
