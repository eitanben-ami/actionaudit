from __future__ import annotations

import argparse
import sys
from pathlib import Path

from actionaudit.parser import parse_workflows
from actionaudit.rules import apply_rules
from actionaudit.reporter import render_report
from actionaudit.models import ActionAuditReport, Workflow


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit GitHub Actions workflows for action pinning and source trust.")
    parser.add_argument("path", nargs="?", default=".", help="Workflow file or directory. Defaults to current directory.")
    parser.add_argument("--json", action="store_true", help="Emit JSON report instead of plain text.")
    parser.add_argument("--markdown", action="store_true", help="Emit Markdown report instead of plain text.")
    args = parser.parse_args(argv)

    path = Path(args.path)
    if not path.exists():
        sys.stderr.write(f"error: {path} does not exist\n")
        return 1

    output_format = "json" if args.json else "markdown" if args.markdown else "text"
    workflows = parse_workflows(path)
    if not workflows:
        report = ActionAuditReport(workflow=Workflow(path=str(path)))
        sys.stdout.write(render_report(report, format=output_format) + "\n")
        return 0

    reports = []
    for workflow in workflows:
        report = apply_rules(ActionAuditReport(workflow=workflow))
        reports.append(report)

    if len(reports) == 1:
        sys.stdout.write(render_report(reports[0], format=output_format) + "\n")
    else:
        combined_issues = []
        combined_actions = []
        for report in reports:
            combined_issues.extend(report.issues)
            combined_actions.extend(report.action_reports)
        aggregated = reports[0]
        aggregated.issues = combined_issues
        aggregated.action_reports = combined_actions
        sys.stdout.write(render_report(aggregated, format=output_format) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
