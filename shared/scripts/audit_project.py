#!/usr/bin/env python3
"""Heuristic architecture audit for STM32/FreeRTOS projects.

This is intentionally conservative: it reports suspicious patterns for review,
not definitive bugs.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from collections import Counter

CODE_EXTS = {".c", ".h", ".cpp", ".hpp"}
SKIP_DIRS = {".git", "build", "Debug", "Release", "MDK-ARM", "EWARM"}

PATTERNS = {
    "hal_in_upper_layer": re.compile(r"\bHAL_[A-Za-z0-9_]+\s*\("),
    "mutable_extern": re.compile(r"^\s*extern\s+(?!const\b).+;", re.M),
    "blocking_delay": re.compile(r"\b(?:HAL_Delay|osDelay|vTaskDelay|Delay_us)\s*\("),
    "printf": re.compile(r"\b(?:printf|sprintf|snprintf)\s*\("),
    "fatfs": re.compile(r"\b(?:f_open|f_write|f_read|f_close|FatFs_[A-Za-z0-9_]+)\s*\("),
    "string_parser": re.compile(r"\b(?:strtok|sscanf|atof|atoi|strstr)\s*\("),
    "rtos_object": re.compile(r"\b(?:osMessageQueue|osSemaphore|osMutex|osEventFlags|osThread|xQueue|xSemaphore|xTask|vTask)"),
}

ISR_NAMES = re.compile(
    r"\b(?:IRQHandler|HAL_[A-Za-z0-9_]*(?:Callback|CpltCallback|EventCallback))\b"
)

LARGE_LOCAL_ARRAY = re.compile(
    r"(?:^|\n)\s*(?:static\s+)?(?:float|double|uint8_t|uint16_t|uint32_t|int|char)\s+([A-Za-z_]\w*)\s*\[\s*(\d+)\s*\]"
)


def iter_code(root: Path):
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in CODE_EXTS:
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        yield p


def layer_for(path: Path) -> str:
    parts = {p.lower() for p in path.parts}
    if "app" in parts:
        return "app"
    if "service" in parts:
        return "service"
    if "protocol" in parts:
        return "protocol"
    if "device" in parts:
        return "device"
    if "bsp" in parts:
        return "bsp"
    if "rtos" in parts:
        return "rtos"
    return "unknown"


def audit_file(root: Path, path: Path):
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    rel = path.relative_to(root).as_posix()
    findings = []
    layer = layer_for(path)

    # Giant composition files often indicate mixed responsibilities.
    if path.name.lower() in {"main.c", "freertos.c"}:
        lines = text.count("\n") + 1
        if lines > 500:
            findings.append(("HIGH", "giant_composition_file", rel, f"{lines} lines"))
        # business/protocol indicators inside generated composition file
        mixed = []
        for key in ("fatfs", "string_parser", "printf"):
            if PATTERNS[key].search(text):
                mixed.append(key)
        if mixed:
            findings.append(("MEDIUM", "mixed_business_in_composition", rel, ",".join(mixed)))

    # HAL leakage into upper layers.
    if layer in {"app", "service", "protocol"} and PATTERNS["hal_in_upper_layer"].search(text):
        findings.append(("HIGH", "hal_leak_to_upper_layer", rel, layer))

    # Mutable extern count.
    ext_count = len(PATTERNS["mutable_extern"].findall(text))
    if ext_count >= 5:
        findings.append(("MEDIUM", "many_mutable_externs", rel, str(ext_count)))

    # Suspicious ISR bodies: simple heuristic split around callback/IRQ symbol.
    if ISR_NAMES.search(text):
        suspicious = []
        for key in ("blocking_delay", "printf", "fatfs", "string_parser"):
            if PATTERNS[key].search(text):
                suspicious.append(key)
        if suspicious:
            findings.append(("HIGH", "suspicious_isr_work", rel, ",".join(suspicious)))

    # Large local/static arrays: still useful to review stack/memory ownership.
    for m in LARGE_LOCAL_ARRAY.finditer(text):
        n = int(m.group(2))
        if n >= 256:
            findings.append(("LOW", "large_array_review", rel, f"{m.group(1)}[{n}]"))

    # Protocol parsing in RTOS task/composition file.
    if ("freertos" in path.name.lower() or layer == "rtos") and PATTERNS["string_parser"].search(text):
        findings.append(("MEDIUM", "protocol_parser_in_task_layer", rel, "move to Protocol/"))

    return findings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project", type=Path)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    root = args.project.resolve()
    findings = []
    for path in iter_code(root):
        findings.extend(audit_file(root, path))

    counts = Counter(f[0] for f in findings)
    if args.json:
        print(json.dumps({
            "project": str(root),
            "summary": dict(counts),
            "findings": [
                {"severity": a, "rule": b, "file": c, "detail": d}
                for a, b, c, d in findings
            ],
        }, ensure_ascii=False, indent=2))
        return

    print(f"Project: {root}")
    print(f"Findings: HIGH={counts['HIGH']} MEDIUM={counts['MEDIUM']} LOW={counts['LOW']}")
    for sev, rule, rel, detail in findings:
        print(f"[{sev:6}] {rule:34} {rel} :: {detail}")


if __name__ == "__main__":
    main()
