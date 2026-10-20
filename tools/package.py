"""Build only the installable mod and its user documentation."""
from pathlib import Path
import hashlib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
NAME = "ProjectZomboidDrillPressFix"
VERSION = "0.1.0"
out = ROOT / "dist" / f"{NAME}-{VERSION}.zip"
out.parent.mkdir(exist_ok=True)
sources = sorted((ROOT / NAME).rglob("*"))
docs = [ROOT / p for p in ["README.md", "CHANGELOG.md", "TESTING.md", "docs/INVESTIGATION.md"]]
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr(f"{NAME}/common/", "")
    for p in sources:
        if p.is_file() and p.name != ".keep":
            z.write(p, p.relative_to(ROOT).as_posix())
    for p in docs:
        z.write(p, f"{NAME}/{p.relative_to(ROOT).as_posix()}")
with zipfile.ZipFile(out) as z:
    assert z.testzip() is None
    assert f"{NAME}/42/mod.info" in z.namelist()
    assert all(n.startswith(NAME + "/") for n in z.namelist())
digest = hashlib.sha256(out.read_bytes()).hexdigest()
checksum = out.with_suffix(".zip.sha256")
checksum.write_text(f"{digest}  {out.name}\n", encoding="ascii")
print(f"{out.name}: {len(out.read_bytes())} bytes")
print(f"SHA256 {digest}")
