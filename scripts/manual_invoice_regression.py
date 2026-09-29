#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_ROOT = PROJECT_ROOT / "uploaded_documents" / "manual-regression"

CASES = (
    (
        "A1",
        "a1.pdf",
        "A1_REAL_PDF_PATH",
        "tests/test_a1_real_pdf_e2e.py::test_real_a1_pdf_end_to_end",
    ),
    (
        "Electrohold",
        "electrohold.pdf",
        "ELECTROHOLD_REAL_PDF_PATH",
        "tests/test_electrohold_real_pdf_collections_e2e.py::test_real_electrohold_collections_end_to_end",
    ),
    (
        "Toplofikacia",
        "toplofikacia.pdf",
        "TOPLOFIKACIA_REAL_PDF_PATH",
        "tests/test_toplofikacia_real_pdf_e2e.py::test_real_toplofikacia_pdf_end_to_end",
    ),
)


def run_case(label, filename, environment_name, test_id):
    pdf_path = FIXTURE_ROOT / filename
    if not pdf_path.is_file():
        return False, f"fixture missing: {filename}"

    environment = os.environ.copy()
    environment[environment_name] = str(pdf_path)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "--tb=no",
            test_id,
        ],
        cwd=PROJECT_ROOT,
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode == 0:
        return True, "passed"
    return False, f"failed with exit code {result.returncode}"


def main():
    failures = 0
    for case in CASES:
        passed, detail = run_case(*case)
        status = "PASS" if passed else "FAIL"
        print(f"{status} {case[0]}: {detail}")
        if not passed:
            failures += 1

    print(f"SUMMARY passed={len(CASES) - failures} failed={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
