"""Package reviewed local sources only; no dependencies, downloads or credentials."""
import hashlib
import json
import pathlib
import plistlib
import shutil
import sys
import tempfile

root = pathlib.Path(__file__).resolve().parents[1]
app = pathlib.Path(sys.argv[1])
expected = root / "dist/Technical Interview Lab.app"
if app != expected or any(p.is_symlink() for p in (root, app, app.parent, app / "Contents")):
    raise SystemExit("UNSAFE_BUNDLE_PATH")
staged = pathlib.Path(tempfile.mkdtemp(prefix="resources-", dir=root / ".build-cache"))
for name, target in [("ui", "ui"), ("tia_runtime", "runtime/tia_runtime"),
                     ("agents", "runtime/agents"), ("policy", "runtime/policy")]:
    source = root / name
    if not source.exists() and name == "policy":
        continue
    if not source.is_dir() or any(p.is_symlink() for p in source.rglob("*")):
        raise SystemExit("UNSAFE_BUNDLE_SOURCE")
    shutil.copytree(source, staged / target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
manifest = {"schema": "tia-app-build/v1", "version": "0.3.0",
            "live_transport_enabled": False, "development_python": "/usr/bin/python3",
            "sources": {str(p.relative_to(staged)): hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in staged.rglob("*") if p.is_file()}}
(staged / "build-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
resources = app / "Contents/Resources"
if resources.is_symlink():
    raise SystemExit("UNSAFE_RESOURCES")
if resources.exists():
    shutil.rmtree(resources)  # Generated bundle resources only, never session storage.
staged.rename(resources)
info = {"CFBundleName": "Technical Interview Lab", "CFBundleDisplayName": "Technical Interview Lab",
        "CFBundleIdentifier": "local.hal.technical-interview-lab",
        "CFBundleExecutable": "TechnicalInterviewLab", "CFBundlePackageType": "APPL",
        "CFBundleShortVersionString": "0.3.0", "CFBundleVersion": "3",
        "TIADevelopmentBuild": True, "LSMinimumSystemVersion": "12.0",
        "NSHighResolutionCapable": True, "NSPrincipalClass": "NSApplication",
        "NSAppTransportSecurity": {"NSAllowsArbitraryLoads": False}}
with (app / "Contents/Info.plist").open("wb") as handle:
    plistlib.dump(info, handle)
