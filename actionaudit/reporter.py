from __future__ import annotations

import json
import sys
from typing import List

from .models import ActionAuditReport, AuditIssue


def render_report(report: ActionAuditReport, format: str = "text") -> str:
    if format == "json":
        return _render_json(report)
    if format == "markdown":
        return _render_markdown(report)
    return _render_text(report)


def _render_json(report: ActionAuditReport) -> str:
    payload = {
        "workflow": report.workflow.path,
        "issues": [
            {
                "rule": issue.rule,
                "message": issue.message,
                "job": issue.job,
                "step": issue.step,
            }
            for issue in report.issues
        ],
        "actions": [
            {
                "owner": item.owner,
                "repo": item.repo,
                "ref": item.ref,
                "is_private": item.is_private,
            }
            for item in report.action_reports
        ],
    }
    return json.dumps(payload, indent=2)


def _render_markdown(report: ActionAuditReport) -> str:
    lines = [f"# ActionAudit Report: {report.workflow.path}\n"]
    if not report.issues:
        lines.append("No issues found.\n")
    else:
        lines.append("## Issues\n")
        for issue in report.issues:
            location = f"{issue.job}/{issue.step}" if issue.job and issue.step else issue.job or issue.step or ""
            lines.append(f"- **{issue.rule}**: {issue.message} `({location})`\n")
    lines.append("\n## Actions\n\n")
    for item in report.action_reports:
        lines.append(f"- `{item.owner}/{item.repo}` ref=`{item.ref}` private={item.is_private}\n")
    return "\n".join(lines)


def _render_text(report: ActionAuditReport) -> str:
    lines = [f"ActionAudit: {report.workflow.path}"]
    if not report.issues:
        lines.append("No issues found.")
        return "\n".join(lines)
    lines.append("Issues:")
    for issue in report.issues:
        location = f"{issue.job}/{issue.step}" if issue.job and issue.step else issue.job or issue.step or ""
        lines.append(f"- {issue.rule}: {issue.message} [{location}]")
    lines.append("Actions:")
    for item in report.action_reports:
        lines.append(f"- {item.owner}/{item.repo} ref={item.ref or '<none>'} private={item.is_private}")
    return "\n".join(lines)


def render_to_stdout(report: ActionAuditReport, format: str = "text") -> None:
    sys.stdout.write(render_report(report, format=format))
    sys.stdout.write("\n")
