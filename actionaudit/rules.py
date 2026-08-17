from __future__ import annotations

import re
from typing import List

from .models import ActionReport, ActionAuditReport, AuditIssue


_PIN_RE = re.compile(r"^(@[^/]+/[^@]+|(?:docker://)?[^@]+)@([a-f0-9]{40}|[vV]?\d+(?:\.\d+){0,2})$", re.IGNORECASE)
_PIN_DOCKER_RE = re.compile(r"^([^@]+)@sha256:[a-f0-9]{64}$", re.IGNORECASE)
_SSO_RE = re.compile(r"^[a-z0-9_-]+/[a-z0-9_-]+$", re.IGNORECASE)


def apply_rules(report: ActionAuditReport) -> ActionAuditReport:
    action_reports: List[ActionReport] = []
    for workflow in [report.workflow]:
        for job in workflow.jobs:
            job_issues = _check_job(job, workflow, action_reports)
            report.issues.extend(job_issues)
    report.action_reports.extend(action_reports)
    return report


def _check_job(job, workflow, action_reports: List[ActionReport]) -> List[AuditIssue]:
    issues: List[AuditIssue] = []
    for step in job.steps:
        issues.extend(_check_step(step, workflow, job, action_reports))
    return issues


def _check_step(step, workflow, job, action_reports: List[ActionReport]) -> List[AuditIssue]:
    issues: List[AuditIssue] = []
    uses = step.uses
    if uses is None:
        return issues
    if not _is_pinned(uses):
        issues.append(AuditIssue(rule="missing-pin", message="Action is not pinned to a ref or SHA.", path=workflow.path, job=job.id, step=step.name))
    if not _is_trusted_source(uses):
        issues.append(AuditIssue(rule="untrusted-source", message="Action source does not match owner/repo form.", path=workflow.path, job=job.id, step=step.name))
    report = _parse_action(uses)
    if report is not None:
        if report.is_private:
            issues.append(AuditIssue(rule="private-action", message="Private or inaccessible action without ref.", path=workflow.path, job=job.id, step=step.name))
        action_reports.append(report)
    return issues


def _is_pinned(uses: str) -> bool:
    if uses.startswith("docker://"):
        return bool(_PIN_DOCKER_RE.match(uses))
    return uses.startswith("./") or uses.startswith(".") or "@" in uses


def _is_trusted_source(uses: str) -> bool:
    if uses.startswith("docker://") or uses.startswith("./") or uses.startswith("."):
        return True
    source = uses.split("@")[0] if "@" in uses else uses
    return bool(_SSO_RE.match(source))


def _parse_action(uses: str) -> ActionReport | None:
    if uses.startswith("docker://"):
        reference = uses.split("docker://", 1)[1]
        image = reference.split("@")[0] if "@" in reference else reference
        owner, repo = image.split("/", 1) if "/" in image else (image, "")
        is_private = not _PIN_DOCKER_RE.match(uses)
        return ActionReport(owner=owner, repo=repo, ref=reference.split("@")[1] if "@" in reference else None, is_private=is_private)
    if uses.startswith("./") or uses.startswith("."):
        return None
    source = uses.split("@")[0] if "@" in uses else uses
    ref = uses.split("@")[1] if "@" in uses else None
    if "/" not in source:
        return None
    owner, repo = source.split("/", 1)
    is_private = "@" not in uses
    return ActionReport(owner=owner, repo=repo, ref=ref, is_private=is_private)
