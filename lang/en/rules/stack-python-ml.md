---
paths:
  - "**/*.py"
  - "**/*.ipynb"
---
# stack-python-ml: Python and ML checklist

> Source: condensed from ECC (MIT) `python-reviewer` and `mle-reviewer` (third_party/ECC@ccd8da1). Project rules (CLAUDE.md, project-conventions) and the existing code's conventions win over this file. Use the same items when writing and when reviewing.
>
> Scope: apply to the code you write or change now. Report violations outside the change instead of fixing them (the project's surgical-change rule wins).

## Python checks (by severity)
- Security (first): no f-string SQL (parameterize). Shell commands via `subprocess` with a list. Block `..` in user-controlled paths. No `eval`/`exec`, untrusted `pickle`/`joblib`/`yaml.load`, hardcoded secrets, or MD5/SHA1 for security.
- Error handling: no bare `except` and no swallowed exceptions (catch specific ones and log). Use `with` for files and resources.
- Types: type hints on public functions; no needless `Any`, no missing `Optional`.
- Idioms: no mutable default arguments (`def f(x=[])`), use `is None`, `isinstance`, named constants or `Enum` instead of magic numbers, `"".join` instead of `+` in loops.
- Structure: split functions over 50 lines, over 5 parameters (dataclass), nesting over 4 levels, and duplicated code.
- Concurrency: locks around shared state, careful with sync/async mixing, batch queries instead of queries in loops (N+1).
- Minor: import order, `logging` instead of `print`, no `import *`, do not shadow builtins (`list`, `dict`).

## ML checks (only when touching data, training, evaluation, or serving)
- Leakage: split by time and by entity (user). No random split on time-dependent data. Fit scalers, encoders, and tokenizers on the training split only. Never use columns unavailable at prediction time (post-outcome values, future labels) as features.
- Reproducibility: the run must repeat from code, config, dataset version, and seed without notebook state. Record hyperparameters, preprocessing, dependency versions, code hash, metrics, and artifact location. Handle randomness and GPU nondeterminism deliberately, and version artifacts so a retry never overwrites a previous one.
- Evaluation: compare with a baseline (current or simple model). Pick metrics that match the cost of errors (not accuracy alone). Look at metrics per important slice and at the errors themselves. Do not tune repeatedly against the test set. Decide promotion criteria before selecting a model and block when they are not met.
- Serving: share training and serving preprocessing or test their equivalence. The input schema rejects missing and out-of-range values. Put the model version in outputs and logs, and provide timeouts, a fallback, and a way back to the previous artifact.
- Privacy and secrets: no personal data or keys in datasets, notebooks, logs, or artifacts. Flag a notebook that production retraining depends on.

## Checks to run
- Run only what the project already has (`pytest`, `ruff check .`, `mypy .`, `bandit -r .`). Ask before installing new packages.
- Report findings by severity with file:line, and do not restructure code unless asked.
