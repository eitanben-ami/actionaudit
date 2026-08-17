from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from actionaudit.models import ActionAuditReport, Job, Step, Workflow
from actionaudit.parser import parse_workflows
from actionaudit.rules import apply_rules, _is_pinned, _is_trusted_source


def test_missing_pin_positive():
    workflow = Workflow(path="workflow.yml", jobs=[job(step("Install", uses="actions/checkout"))])
    report = apply_rules(ActionAuditReport(workflow=workflow))
    assert any(issue.rule == "missing-pin" for issue in report.issues)


def test_pinned_action_is_clean():
    workflow = Workflow(path="workflow.yml", jobs=[job(step("Install", uses="actions/checkout@11"))])
    report = apply_rules(ActionAuditReport(workflow=workflow))
    assert not any(issue.rule == "missing-pin" for issue in report.issues)


def test_untrusted_source_negative():
    workflow = Workflow(path="workflow.yml", jobs=[job(step("Install", uses="checkout@v4"))])
    report = apply_rules(ActionAuditReport(workflow=workflow))
    assert any(issue.rule == "untrusted-source" for issue in report.issues)


def test_local_action_is_trusted_and_pinned():
    workflow = Workflow(path="workflow.yml", jobs=[job(step("Local", uses="./local-action"))])
    report = apply_rules(ActionAuditReport(workflow=workflow))
    assert not any(issue.rule == "missing-pin" for issue in report.issues)
    assert not any(issue.rule == "untrusted-source" for issue in report.issues)


def test_docker_unpinned_action_issues_private():
    workflow = Workflow(path="workflow.yml", jobs=[job(step("Container", uses="docker://python:3"))])
    report = apply_rules(ActionAuditReport(workflow=workflow))
    assert any(issue.rule == "missing-pin" for issue in report.issues)
    assert any(issue.rule == "private-action" for issue in report.issues)


def test_parse_workflow_from_directory():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "workflow.yml"
        path.write_text("name: CI\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n", encoding="utf-8")
        workflows = parse_workflows(Path(tmp))
        assert len(workflows) == 1
        assert workflows[0].jobs[0].steps[0].uses == "actions/checkout@v4"


@pytest.mark.parametrize(
    "uses,expected",
    [
        ("actions/checkout@v4", True),
        ("owner/repo@a1b2c3", True),
        ("actions/checkout", False),
        ("./local", True),
    ],
)
def test_pin_parametrized(uses, expected):
    assert _is_pinned(uses) is expected


@pytest.mark.parametrize(
    "uses,expected",
    [
        ("actions/checkout@v4", True),
        ("./local", True),
        ("docker://python:3@sha256:abcd", True),
        ("checkout@v4", False),
    ],
)
def test_trusted_parametrized(uses, expected):
    assert _is_trusted_source(uses) is expected


def job(step_item: Step) -> Job:
    return Job(id="test", runs_on="ubuntu-latest", steps=[step_item])


def step(name: str, *, uses: str | None = None, run: str | None = None) -> Step:
    return Step(name=name, uses=uses, run=run, with_={}, env={})
