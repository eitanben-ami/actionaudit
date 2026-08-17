from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class Step:
    name: str
    uses: Optional[str] = None
    run: Optional[str] = None
    with_: dict = field(default_factory=dict)
    env: dict = field(default_factory=dict)


@dataclass
class Job:
    id: str
    runs_on: Optional[str] = None
    steps: List[Step] = field(default_factory=list)


@dataclass
class Workflow:
    path: str
    name: Optional[str] = None
    jobs: List[Job] = field(default_factory=list)


@dataclass
class AuditIssue:
    rule: str
    message: str
    path: str
    job: Optional[str] = None
    step: Optional[str] = None


@dataclass
class ActionReport:
    owner: str
    repo: str
    ref: Optional[str] = None
    is_private: bool = False


@dataclass
class ActionAuditReport:
    workflow: Workflow
    issues: List[AuditIssue] = field(default_factory=list)
    action_reports: List[ActionReport] = field(default_factory=list)
