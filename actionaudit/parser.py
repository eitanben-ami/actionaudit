from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional

import yaml

from .models import Job, Step, Workflow

_WORKFLOW_GLOB = "*.yml"


def parse_workflows(path: Path) -> List[Workflow]:
    path = path.resolve()
    if path.is_file():
        return [_parse_file(path)]
    return [_parse_file(p) for p in sorted(path.glob(_WORKFLOW_GLOB)) if p.is_file()]


def _parse_file(path: Path) -> Workflow:
    text = path.read_text(encoding="utf-8")
    document = yaml.safe_load(text) or {}
    jobs = document.get("jobs") or {}
    parsed_jobs: List[Job] = []
    workflow_name = document.get("name")
    for job_id, job_data in jobs.items():
        if not isinstance(job_data, dict):
            continue
        steps = [_parse_step(step) for step in (job_data.get("steps") or []) if isinstance(step, dict)]
        parsed_jobs.append(Job(id=str(job_id), runs_on=job_data.get("runs-on"), steps=steps))
    return Workflow(path=str(path), name=str(workflow_name) if workflow_name is not None else None, jobs=parsed_jobs)


def _parse_step(step_data: dict) -> Step:
    run = step_data.get("run")
    uses = step_data.get("uses")
    name = step_data.get("name") or (uses or run or "step")
    with_ = step_data.get("with") or {}
    env = step_data.get("env") or {}
    return Step(name=str(name), uses=str(uses) if uses is not None else None, run=str(run) if run is not None else None, with_=dict(with_), env=dict(env))
