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


def parse_coverage_details(xml_path: Path):
    if not xml_path.exists():
        return None
    tree = ET.parse(xml_path)
    root = tree.getroot()

    def to_float(v, default=0.0):
        try:
            return float(v)
        except Exception:
            return default

    files = []
    total_lines = 0
    covered_lines = 0

    for pkg in root.findall("packages/package"):
        for cls in pkg.findall("classes/class"):
            filename = cls.attrib.get("filename", "")
            rate = to_float(cls.attrib.get("line-rate", 0.0))

            # Collect lines
            line_elems = cls.findall("lines/line")
            if not line_elems:
                for m in cls.findall("methods/method"):
                    line_elems.extend(m.findall("lines/line"))

            lt = len(line_elems)
            lc = 0
            missed_list = []
            for le in line_elems:
                hits = int(le.attrib.get("hits", 0))
                if hits > 0:
                    lc += 1
                else:
                    try:
                        num = int(le.attrib.get("number", 0))
                        if num:
                            missed_list.append(num)
                    except Exception:
                        pass
            lm = max(lt - lc, 0)

            methods = cls.findall("methods/method")
            ft = len(methods)
            fc = 0
            missed_funcs = []
            for m in methods:
                mr = to_float(m.attrib.get("line-rate", 0.0))
                if mr > 0:
                    fc += 1
                else:
                    missed_funcs.append(m.attrib.get("name", "<anonymous>"))

            files.append({
                "filename": filename,
                "line_rate": round(rate * 100.0, 2),
                "lines_total": lt,
                "lines_covered": lc,
                "lines_missed": lm,
                "missed_lines": sorted(missed_list),
                "funcs_total": ft,
                "funcs_covered": fc,
                "funcs_missed": max(ft - fc, 0),
                "missed_funcs": missed_funcs,
            })

            total_lines += lt
            covered_lines += lc

    overall_rate = round((covered_lines / total_lines) * 100.0, 2) if total_lines else 0.0
    return {
        "overall": {
            "line_rate": overall_rate,
            "files": len(files),
            "lines_total": total_lines,
            "lines_covered": covered_lines,
            "lines_missed": max(total_lines - covered_lines, 0),
        },
        "files": files,
    }


def pytest_run(name: str, markers: str | None, with_cov: bool):
    out_dir = RESULTS_DIR / name
    ensure_dir(out_dir)

    junit_xml = out_dir / "report.xml"
    cov_xml = out_dir / "coverage.xml"
    cov_html = out_dir / "htmlcov"

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
        # Run from backend dir; target the Python package/module name
        cmd += [
            "--cov=app",
            "--cov-report=term-missing",
            f"--cov-report=xml:{cov_xml}",
            f"--cov-report=html:{cov_html}",
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

    # Append detailed coverage for the full run (all_cov)
    try:
        all_cov = next(x for x in runs if x["name"] == "all_cov")
        cov_xml_path = Path(all_cov["out_dir"]) / "coverage.xml"
        det = parse_coverage_details(cov_xml_path)
        if det and det.get("files"):
            synth.append("")
            synth.append("== Détails de couverture (all_cov) ==")
            ov = det["overall"]
            synth.append(
                f"Global: fichiers={ov['files']} lignes={ov['lines_covered']}/{ov['lines_total']} ({ov['line_rate']}%) manquantes={ov['lines_missed']}"
            )
            for f in sorted(det["files"], key=lambda x: (x["line_rate"], x["filename"])):
                synth.append(
                    f"- {f['filename']}: lignes {f['lines_covered']}/{f['lines_total']} ({f['line_rate']}%), fonctions {f['funcs_covered']}/{f['funcs_total']}"
                )
                if f["lines_missed"]:
                    synth.append("  lignes manquantes: " + ", ".join(map(str, f["missed_lines"])))
                if f["funcs_missed"]:
                    synth.append("  fonctions non couvertes: " + ", ".join(f["missed_funcs"]))
    except Exception as e:
        synth.append("")
        synth.append(f"(Info) Détails couverture indisponibles: {e}")

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
