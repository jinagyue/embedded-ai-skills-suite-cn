"""Validate module resources and the packaged workflow bridge without hardware."""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / "skills_manifest.json").read_text(encoding="utf-8"))
assert sorted(p.relative_to(ROOT).as_posix() for p in ROOT.rglob("SKILL.md")) == ["SKILL.md"]
assert manifest["entry_file"] == "SKILL.md"
assert len(manifest["module_guides"]) == 14
assert len(manifest["backend_guides"]) == 12
for guide in [*manifest["module_guides"].values(), *manifest["backend_guides"].values()]:
    assert (ROOT / guide).is_file(), guide
for tool in manifest["tools"]:
    assert (ROOT / tool).is_file(), tool

env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
with tempfile.TemporaryDirectory(prefix="embeddedskills-package-") as directory:
    workspace = Path(directory)
    (workspace / "demo.uvprojx").write_text("<Project/>", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-X", "utf8", "-B", str(ROOT / "shared/scripts/external_embeddedskills_adapter.py"),
         "--embeddedskills-root", str(ROOT), "--workspace", str(workspace), "--action", "plan", "--json"],
        capture_output=True, text=True, encoding="utf-8", env=env, timeout=20,
    )
    assert result.returncode == 0, (result.stdout, result.stderr)
    data = json.loads(result.stdout)
    assert data["status"] == "ok", data
    assert data["details"]["keil_projects"] == [str(workspace / "demo.uvprojx")], data
    assert data["details"]["build_candidates"] == ["keil"], data
    assert data["adapter"]["action"] == "plan"

print("single-entry packaging and internal workflow bridge: OK")
