#!/usr/bin/env python3
"""Create the non-generated folders for the recommended architecture."""
from pathlib import Path
import argparse

DIRS = [
    "BSP/Driver",
    "BSP/Service",
    "BSP/Board",
    "BSP/Port",
    "Device",
    "Protocol",
    "Service",
    "App",
    "RTOS",
    "Common",
    "Config",
    "Tests/unit",
    "Tests/integration",
]

GITKEEP = "# Created by embedded-dev-skills-suite\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project", type=Path)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    root = args.project.resolve()
    for d in DIRS:
        p = root / d
        print(p)
        if not args.dry_run:
            p.mkdir(parents=True, exist_ok=True)
            keep = p / ".gitkeep"
            if not any(p.iterdir()):
                keep.write_text(GITKEEP, encoding="utf-8")


if __name__ == "__main__":
    main()
