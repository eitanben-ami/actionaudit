# actionaudit

Audit GitHub Actions workflows for action pinning and trusted source issues.

## About

`actionaudit` scans GitHub Actions workflow files and reports:

- Actions that are **not pinned** to a ref or SHA.
- Actions sourced from **untrusted or unusual paths** outside the `owner/repo` form.
- **Private or inaccessible** actions lacking a ref, which can break reproducibility.

It parses `.yml` workflow files in a directory, applies lightweight rule checks, and emits a report in text, Markdown, or JSON.

## Features

- Parse YAML workflows with `runs-on`, jobs, and `uses`-based steps.
- Detect missing pins, unexpected action sources, and private references.
- Report generation: plain text, Markdown, JSON.
- Zero external service calls; no GitHub token required.
- Python CLI with installable `pyproject.toml`.

## Installation

```bash
python -m pip install .
```

## Usage

```bash
actionaudit ./.github/workflows
actionaudit ./.github/workflows --json
actionaudit ./.github/workflows --markdown
```

Repository: https://github.com/eitanben-ami/actionaudit

## Project structure

```
actionaudit/
  actionaudit/
    __init__.py
    cli.py
    models.py
    parser.py
    reporter.py
    rules.py
  tests/
    test_actionaudit.py
    test_actionaudit_cli.py
  pyproject.toml
  README.md
  .gitignore
```

## Tags / keywords

github-actions, workflow-audit, security, supply-chain, python-cli, pinning

## License

MIT
