"""Flaky-test report (Day 8, B2): run the suite N times, or read N JUnit files, and sort every test.

    python tools/flaky_report.py --runs 3                      # runs pytest 3 times, then reports
    python tools/flaky_report.py --runs 3 -- tests/test_cart.py -m critical   # extra pytest arguments
    python tools/flaky_report.py reports/run_1.xml reports/run_2.xml        # reads existing JUnit files

Each test lands in one group:

* stable      passed (or xfailed / skipped) in every run
* failing     failed in every run: a real defect or a broken test - analyse its trace (B1)
* flaky       passed in some runs and failed in others: quarantine it and find the root cause

Exit code 1 when a test is flaky or failing, so a CI job can stop on it.
"""
import argparse
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS_FOLDER = ROOT / "reports" / "flaky"


class FlakyReport:
    ############################################################################
    # Collect methods
    # Scope: JUnit files > one outcome per test per run
    ############################################################################
    def __init__(self):
        self.outcomes: dict[str, list[str]] = defaultdict(list)  # test id -> outcome of each run
        self.run_count = 0

    def read_junit_file(self, path: Path):
        """Add the outcome of every test case of one JUnit file (one run)."""
        self.run_count += 1
        for case in ET.parse(path).iter("testcase"):
            test_id = f"{case.get('classname')}::{case.get('name')}"
            self.outcomes[test_id].append(self._outcome(case))

    @staticmethod
    def _outcome(case) -> str:
        if case.find("failure") is not None or case.find("error") is not None:
            return "failed"
        if case.find("skipped") is not None:
            return "skipped"  # skipped or xfailed: neither proves nor breaks stability
        return "passed"

    ############################################################################
    # Report methods
    # Scope: Console > stable / failing / flaky groups
    ############################################################################
    def groups(self) -> dict[str, list[str]]:
        """{"stable": [...], "failing": [...], "flaky": [...]} by test id."""
        result: dict[str, list[str]] = {"stable": [], "failing": [], "flaky": []}
        for test_id, outcomes in sorted(self.outcomes.items()):
            failed = outcomes.count("failed")
            if failed == 0:
                result["stable"].append(test_id)
            elif failed == len(outcomes):
                result["failing"].append(test_id)
            else:
                result["flaky"].append(test_id)
        return result

    def print_report(self) -> int:
        """Print the groups; return the exit code (1 when a test is failing or flaky)."""
        groups = self.groups()
        print(f"\nFlaky report over {self.run_count} runs, {len(self.outcomes)} tests")
        print(f"  stable : {len(groups['stable'])}")
        for name in ("failing", "flaky"):
            print(f"  {name:7}: {len(groups[name])}")
            for test_id in groups[name]:
                print(f"    - {test_id}   {' '.join(self.outcomes[test_id])}")
        return 1 if groups["failing"] or groups["flaky"] else 0


def run_suite(runs: int, pytest_args: list[str]) -> list[Path]:
    """Run pytest ``runs`` times, each run writing its own JUnit file; return the files."""
    RUNS_FOLDER.mkdir(parents=True, exist_ok=True)
    files = []
    for run in range(1, runs + 1):
        junit_file = RUNS_FOLDER / f"run_{run}.xml"
        print(f"Run {run}/{runs}: pytest {' '.join(pytest_args)}")
        subprocess.run([sys.executable, "-m", "pytest", "-q", f"--junitxml={junit_file}", *pytest_args], cwd=ROOT)
        files.append(junit_file)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description="Sort tests into stable / failing / flaky over several runs.")
    parser.add_argument("junit_files", nargs="*", type=Path, help="JUnit files of earlier runs")
    parser.add_argument("--runs", type=int, default=0, help="run pytest this many times first")
    argv = sys.argv[1:]
    split = argv.index("--") if "--" in argv else len(argv)  # everything after "--" goes to pytest
    args, pytest_args = parser.parse_args(argv[:split]), argv[split + 1:]
    files = run_suite(args.runs, pytest_args) if args.runs else args.junit_files
    if not files:
        parser.error("give JUnit files or --runs N")
    report = FlakyReport()
    for path in files:
        report.read_junit_file(path)
    return report.print_report()


if __name__ == "__main__":
    sys.exit(main())
