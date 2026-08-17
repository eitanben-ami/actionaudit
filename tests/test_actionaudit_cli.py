from __future__ import annotations

import inspect
import json
import tempfile
from pathlib import Path

import pytest

from actionaudit.cli import main
from actionaudit.models import ActionAuditReport, Job, Step, Workflow
from actionaudit.parser import parse_workflows
from actionaudit.reporter import render_report
from actionaudit.rules import apply_rules


def test_main_returns_zero_for_directory():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "workflow.yml"
        path.write_text("name: CI\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n", encoding="utf-8")
        assert main([tmp]) == 0


def test_main_returns_one_for_missing_path():
    assert main(["/tmp/missing-path-actionaudit"]) == 1


def test_main_supports_json_and_markdown():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "workflow.yml"
        path.write_text("name: CI\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout\n", encoding="utf-8")
        assert main([tmp, "--json"]) == 0
        assert main([tmp, "--markdown"]) == 0


def test_parse_empty_directory_returns_empty():
    with tempfile.TemporaryDirectory() as tmp:
        assert parse_workflows(Path(tmp)) == []


def test_apply_rules_does_not_mutate_original_report():
    workflow = Workflow(path="workflow.yml", jobs=[job(step("Install", uses="actions/checkout@v4"))])
    original = ActionAuditReport(workflow=workflow)
    apply_rules(original)
    assert not original.issues


def test_render_text_contains_path_and_summary():
    workflow = Workflow(path="workflow.yml", jobs=[job(step("Install", uses="actions/checkout"))])
    report = apply_rules(ActionAuditReport(workflow=workflow))
    text = render_report(report, format="text")
    assert "workflow.yml" in text
    assert "missing-pin" in text


def test_render_markdown_has_headings():
    workflow = Workflow(path="workflow.yml", jobs=[job(step("Install", uses="actions/checkout"))])
    report = apply_rules(ActionAuditReport(workflow=workflow))
    markdown = render_report(report, format="markdown")
    assert "# ActionAudit Report: workflow.yml" in markdown
    assert "## Issues" in markdown


def test_render_json_is_valid():
    workflow = Workflow(path="workflow.yml", jobs=[job(step("Install", uses="actions/checkout@v4"))])
    report = apply_rules(ActionAuditReport(workflow=workflow))
    payload = json.loads(render_report(report, format="json"))
    assert payload["workflow"] == "workflow.yml"
    assert isinstance(payload["issues"], list)


def test_main_returns_zero_on_valid_directory():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "workflow.yml"
        path.write_text("name: CI\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n", encoding="utf-8")
        assert main([tmp]) == 0


def test_main_returns_one_on_missing_path():
    assert main(["/tmp/missing-path-actionaudit"]) == 1


def test_main_json_returns_zero():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "workflow.yml"
        path.write_text("name: CI\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n", encoding="utf-8")
        assert main([tmp, "--json"]) == 0


def test_parse_multiple_workflows():
    with tempfile.TemporaryDirectory() as tmp:
        first = Path(tmp) / "a.yml"
        second = Path(tmp) / "b.yml"
        first.write_text("name: A\njobs:\n  a:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n", encoding="utf-8")
        second.write_text("name: B\njobs:\n  b:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n", encoding="utf-8")
        assert len(parse_workflows(Path(tmp))) == 2


def test_apply_rules_collects_multiple_issues():
    workflow = Workflow(path="workflow.yml", jobs=[
        job(step("A", uses="checkout@v4")),
        job(step("B", uses="docker://python:3")),
    ])
    report = apply_rules(ActionAuditReport(workflow=workflow))
    assert len(report.issues) >= 2


def job(step_item: Step) -> Job:
    return Job(id="test", runs_on="ubuntu-latest", steps=[step_item])


def step(name: str, *, uses: str | None = None, run: str | None = None) -> Step:
    return Step(name=name, uses=uses, run=run, with_={}, env={})
