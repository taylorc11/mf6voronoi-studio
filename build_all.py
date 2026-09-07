#!/usr/bin/env python3
"""build_all.py — build app + portable ZIP + installer in one command."""
import os
import sys
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from version import __version__, APP_ID

DIST_APP = os.path.join(HERE, "dist", APP_ID)


def run(script, *args) -> int:
    print(f"\n=== {script} {' '.join(args)} ===")
    return subprocess.call([sys.executable, script, *args], cwd=HERE)


def main() -> int:
    rebuild = "--rebuild" in sys.argv
    do_installer = "--no-installer" not in sys.argv
    do_portable = "--no-portable" not in sys.argv

    if rebuild or not os.path.isdir(DIST_APP):
        if run("build_exe.py") != 0:
            print("App build failed — aborting.")
            return 2
    else:
        print(f"Using existing app build: {DIST_APP}")

    results = []
    if do_portable:
        results.append(("Portable ZIP", run("build_portable.py")))
    if do_installer:
        results.append(("Windows installer", run("build_installer.py")))

    print("\n================ build_all summary ================")
    print(f"Version: {__version__}")
    print(f"App    : {DIST_APP}  (OK)")
    for name, rc in results:
        status = "OK" if rc == 0 else f"skipped/failed (exit {rc})"
        print(f"{name:18}: {status}")
    print("==================================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
