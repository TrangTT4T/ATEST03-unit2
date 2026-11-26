"""pytest plugin: the requirement traceability matrix of every run.

Each test carries one requirement marker (@pytest.mark.add_to_cart ...; registry:
dataset/requirements.json, the Unit 1 Day 1 matrix). At the end of the session this plugin writes
reports/traceability.md and .csv (helper_utility/traceability.py).

* Every collected test is listed, also the ones ``-m`` deselected (manual, data_creating, auth):
  they count as NOT RUN instead of silently missing. The list is taken before deselection.
* Framework tests (tests/unit/) are not product tests and are left out.
* With pytest-xdist the workers collect; they send their list back through ``workeroutput``.
* One Recorder per pytest session (no module-level state), so a nested session in a test cannot
  overwrite the outer one.
"""
from pathlib import Path

import pytest

from helper_utility.traceability import RunResult, load_requirements, write_reports

WORKER_KEY = "traceability_items"


def _requirements_file(config: pytest.Config) -> Path:
    return Path(config.rootpath, "dataset", "requirements.json")


def pytest_configure(config: pytest.Config) -> None:
    requirements = load_requirements(_requirements_file(config))
    for tag, requirement in requirements.items():
        config.addinivalue_line("markers", f"{tag}: requirement {requirement.id} - {requirement.title}")
    config.pluginmanager.register(Recorder(config), "traceability-recorder")


class Recorder:
    def __init__(self, config: pytest.Config) -> None:
        self.config = config
        self.items: dict = {}  # nodeid -> (test file, test name, marker names)
        self.status: dict = {}  # nodeid -> passed / failed / error / skipped

    # --- what exists (before -m deselects anything) ---------------------------------------------
    @pytest.hookimpl(tryfirst=True)
    def pytest_collection_modifyitems(self, items: list) -> None:
        for item in items:
            if "unit" in Path(item.path).relative_to(self.config.rootpath).parts:
                continue
            marks = sorted({m.name for m in item.iter_markers()})
            self.items[item.nodeid] = (Path(item.path).name, item.name, marks)

    def pytest_sessionfinish(self) -> None:
        if hasattr(self.config, "workeroutput"):  # xdist worker: hand the list to the controller
            self.config.workeroutput[WORKER_KEY] = self.items

    @pytest.hookimpl(optionalhook=True)
    def pytest_testnodedown(self, node) -> None:  # xdist controller
        self.items.update(getattr(node, "workeroutput", {}).get(WORKER_KEY, {}))

    # --- what happened ------------------------------------------------------------------------
    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        if self.status.get(report.nodeid) in {"failed", "error"}:
            return  # a teardown never turns a failure back into a pass
        if report.failed:
            self.status[report.nodeid] = "failed" if report.when == "call" else "error"
        elif report.skipped:
            self.status[report.nodeid] = "skipped"
        elif report.when == "call":
            self.status[report.nodeid] = "passed"

    # --- the matrix ----------------------------------------------------------------------------
    def pytest_terminal_summary(self, terminalreporter) -> None:
        if hasattr(self.config, "workeroutput") or self.config.option.collectonly:
            return
        if not any(nodeid in self.status for nodeid in self.items):
            return  # no product test ran (e.g. only tests/unit): keep the last real matrix
        results = [
            RunResult(test_file, name, frozenset(marks), self.status.get(nodeid, "skipped"))
            for nodeid, (test_file, name, marks) in sorted(self.items.items())
        ]
        rows = write_reports(_requirements_file(self.config), results, Path(self.config.rootpath, "reports"))
        terminalreporter.section("Requirement traceability")
        terminalreporter.write_line(", ".join(f"@{r.requirement.tag} {r.status}" for r in rows))
        terminalreporter.write_line("Reports: reports/traceability.md, reports/traceability.csv")
