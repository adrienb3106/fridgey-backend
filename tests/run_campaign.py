#!/usr/bin/env python3
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET


# Paths: this script lives in fridgey-backend/tests
TESTS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = TESTS_DIR.parent
ROOT = BACKEND_DIR.parent  # repo root
RESULTS_DIR = BACKEND_DIR / "results"


def run(cmd_args, cwd=None, env=None):
    proc = subprocess.run(
        cmd_args,
        cwd=cwd or ROOT,
        env=env or os.environ.copy(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return proc.returncode, proc.stdout


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, content: str):
    path.write_text(content, encoding="utf-8")


def parse_junit(xml_path: Path):
    if not xml_path.exists():
        return {"tests": 0, "failures": 0, "errors": 0, "skipped": 0, "time": 0.0}
    tree = ET.parse(xml_path)
    root = tree.getroot()
    # Pytest may produce either <testsuite> or <testsuites>
    if root.tag == "testsuite":
        suites = [root]
    else:
        suites = list(root.findall("testsuite"))
    totals = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0, "time": 0.0}
    for s in suites:
        totals["tests"] += int(s.attrib.get("tests", 0))
        totals["failures"] += int(s.attrib.get("failures", 0))
        totals["errors"] += int(s.attrib.get("errors", 0))
        totals["skipped"] += int(s.attrib.get("skipped", 0))
        try:
            totals["time"] += float(s.attrib.get("time", 0.0))
        except ValueError:
            pass
    return totals


def parse_coverage_xml(xml_path: Path):
    if not xml_path.exists():
        return None
    tree = ET.parse(xml_path)
    root = tree.getroot()
    # coverage.py XML root is <coverage line-rate="...">
    line_rate = root.attrib.get("line-rate")
    if line_rate is None:
        return None
    try:
        return round(float(line_rate) * 100.0, 2)
    except ValueError:
        return None


def pytest_run(name: str, markers: str | None, with_cov: bool):
    out_dir = RESULTS_DIR / name
    ensure_dir(out_dir)

    junit_xml = out_dir / "report.xml"
    cov_xml = out_dir / "coverage.xml"

    base_cmd = [sys.executable, "-m", "pytest"]

    # Select tests
    if markers is None:
        # all tests
        pass
    elif markers == "tv":
        base_cmd += ["-m", "tv", "tests/TV"]
    elif markers == "not tv":
        base_cmd += ["-m", "not tv", "tests"]

    # Quiet output; always produce JUnit XML
    cmd = base_cmd + ["-q", f"--junitxml={junit_xml}"]

    if with_cov:
        cmd += [
            "--cov=fridgey-backend/app",
            f"--cov-report=term-missing",
            f"--cov-report=xml:{cov_xml}",
        ]

    # Ensure coverage file is written inside the run folder when enabled
    env = os.environ.copy()
    if with_cov:
        env["COVERAGE_FILE"] = str(out_dir / ".coverage")

    # Run from backend directory so artifacts (.coverage) live under backend
    rc, out = run(cmd, cwd=BACKEND_DIR, env=env)
    write_text(out_dir / "stdout.txt", out)
    write_text(out_dir / "return_code.txt", str(rc))

    junit = parse_junit(junit_xml)
    cov = parse_coverage_xml(cov_xml) if with_cov else None

    # Write a brief summary.json-like txt
    summary_lines = [
        f"name: {name}",
        f"return_code: {rc}",
        f"tests: {junit['tests']}",
        f"failures: {junit['failures']}",
        f"errors: {junit['errors']}",
        f"skipped: {junit['skipped']}",
        f"time: {junit['time']}",
    ]
    if cov is not None:
        summary_lines.append(f"coverage: {cov}%")
    write_text(out_dir / "summary.txt", "\n".join(summary_lines) + "\n")

    return {
        "name": name,
        "rc": rc,
        "junit": junit,
        "coverage": cov,
        "out_dir": str(out_dir),
    }


def main():
    global RESULTS_DIR
    ensure_dir(RESULTS_DIR)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_root = RESULTS_DIR / timestamp
    ensure_dir(run_root)

    # Temporarily set RESULTS_DIR to the timestamped folder
    RESULTS_DIR = run_root

    runs = []
    runs.append(pytest_run("all_no_cov", markers=None, with_cov=False))
    runs.append(pytest_run("all_cov", markers=None, with_cov=True))
    runs.append(pytest_run("tu_no_cov", markers="not tv", with_cov=False))
    runs.append(pytest_run("tu_cov", markers="not tv", with_cov=True))
    runs.append(pytest_run("tv_no_cov", markers="tv", with_cov=False))
    runs.append(pytest_run("tv_cov", markers="tv", with_cov=True))

    # Global syntheses
    synth = []
    synth.append("== Synthèse sans couverture ==")
    for name in ("all_no_cov", "tu_no_cov", "tv_no_cov"):
        r = next(x for x in runs if x["name"] == name)
        j = r["junit"]
        synth.append(
            f"{name}: rc={r['rc']} tests={j['tests']} fail={j['failures']} err={j['errors']} skip={j['skipped']} time={j['time']:.2f}s"
        )

    synth.append("")
    synth.append("== Synthèse avec couverture ==")
    for name in ("all_cov", "tu_cov", "tv_cov"):
        r = next(x for x in runs if x["name"] == name)
        j = r["junit"]
        cov = r["coverage"]
        cov_s = f"{cov}%" if cov is not None else "n/a"
        synth.append(
            f"{name}: rc={r['rc']} tests={j['tests']} fail={j['failures']} err={j['errors']} skip={j['skipped']} time={j['time']:.2f}s coverage={cov_s}"
        )

    write_text(run_root / "SUMMARY.txt", "\n".join(synth) + "\n")

    print(f"Campagne terminée. Résultats dans: {run_root}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        print(f"Erreur: {e}")
        sys.exit(1)
