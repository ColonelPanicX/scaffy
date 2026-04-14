---
title: Coding Playbook
description: General coding standards and best practices — a guiding hand, not a rulebook
---

# Coding Playbook

A reference for how to build software well. This is a starting point — project-level
conventions in `CLAUDE.md` or `.collab/context.md` take precedence over anything here.

> Not every project is a code project. Sections marked **[code]** apply only when the
> project produces runnable software.

---

## 1. Project Structure [code]

Separate concerns clearly from day one. A project that mixes business logic, CLI code,
config, and tests in one file is a project that's hard to extend, test, or hand off.

**Guiding principles:**

- **Core logic stays separate from interfaces.** A library shouldn't know whether it's
  being called by a CLI, a GUI, or a test.
- **One entry point.** Know exactly where execution starts.
- **Config and secrets never live next to source code.** They change per environment;
  source code should not.

**Common layout for a Python project:**

```
project-root/
  src/package/        # core library / business logic
    __init__.py
    __main__.py       # entry point: python -m package
  tests/
    unit/
    integration/
  config/             # runtime config (gitignored)
  .gitignore
  pyproject.toml
```

Adapt this to your language and framework. The principle — not the exact layout — is what matters.

---

## 2. Code Style [code]

Consistency beats preference. Pick a style and enforce it with tooling so it's never a
debate in code review.

### Naming

| Context | Convention |
|---------|-----------|
| Variables, functions | `snake_case` (Python) / `camelCase` (JS/TS/Java) |
| Classes | `PascalCase` |
| Constants | `UPPER_SNAKE_CASE` |
| Files and directories | `lowercase-hyphenated` or `snake_case` (match language norms) |

### Type Hints [Python]

Annotate all function signatures. Return types included.

```python
# Good
def get_user(user_id: str) -> dict[str, str]: ...

# Bad — no hints, no contract
def get_user(user_id): ...
```

### Imports

- Standard library → third-party → local (in that order)
- No wildcard imports (`from module import *`)
- Type-only imports under `if TYPE_CHECKING:` guard

### The single most important style rule

**No `print()` in library or core code.** Return structured results. Only the CLI or
presentation layer should produce output. This keeps core logic testable and reusable.

---

## 3. Configuration and Secrets

### Configuration

- Never hardcode values that belong in config (URLs, timeouts, feature flags).
- Load config once, at startup — not scattered throughout the codebase.
- Commit a `config.example` with placeholder values. Never commit the real config.

```python
# Good — one place, loaded once
config = load_config("config/config.json")

# Bad — scattered hardcodes
BASE_URL = "https://api.example.com"   # in three different files
```

### Secrets

**Never commit secrets.** Not in source files, not in config files, not in comments,
not in commit messages. Gitignored files have been accidentally staged before and will be again.

| Type | Examples | Where it lives |
|------|---------|----------------|
| Config | base URLs, feature flags, timeouts | `config/config.json` (gitignored) |
| Secrets | API keys, tokens, passwords | Environment variables or a secrets manager |

Load secrets from environment variables at runtime:

```python
import os
api_key = os.environ["MY_SERVICE_API_KEY"]  # raises KeyError if missing — that's correct
```

---

## 4. Error Handling

**Fail loudly at system boundaries. Handle gracefully inside loops.**

The goal is: when something goes wrong, the error message tells you exactly what failed
and why — not a vague crash three layers up.

```python
# Good — specific, logged, recoverable
try:
    result = fetch_resource(resource_id)
except ResourceNotFoundError as e:
    logger.warning("Resource %s not found — skipping", resource_id)
    return None

# Bad — silent swallow
try:
    result = fetch_resource(resource_id)
except Exception:
    pass

# Bad — bare except
try:
    result = fetch_resource(resource_id)
except:
    result = None
```

**Never use `except Exception: pass`.** If you're catching an exception, do something
intentional: log it, return a fallback, re-raise with context, or let it propagate.

---

## 5. Testing [code]

### Structure

```
tests/
  unit/          # fast, isolated, no external state
  integration/   # touches files, network, databases, or external services
```

### What to test

- Unit tests cover logic: functions, transformations, edge cases
- Integration tests cover boundaries: file I/O, API calls, database queries
- Don't test the framework — test your code

### The gate before merging

At minimum, the following must pass clean before any code merges:

```bash
lint-tool .          # e.g. ruff, eslint, flake8
formatter --check .  # e.g. black, prettier
type-checker .       # e.g. mypy, tsc
pytest -m "not slow" # or equivalent fast test suite
```

Define these in CI so they run automatically on every pull request.

---

## 6. Git Governance

### Branch naming

```
main          ← stable / production
dev           ← primary development (optional but recommended)
feat/<slug>   ← new feature
fix/<slug>    ← bug fix
chore/<slug>  ← maintenance (deps, config, docs)
```

Prefix with issue number when your tracker supports it: `feat/42-add-export`

### Commit messages

Imperative mood, present tense, lowercase. One line. Add a body if the why isn't obvious.

```
# Good
add s3 export for ec2 instances
fix null pointer in config loader
update dependencies to patch CVE-2026-1234

# Bad
Added s3 export
Fixed a bug
Updates
```

### Issue-first rule

For any team or structured project: open an issue before starting a branch.
Every PR references the issue it closes:

```
Closes #42
```

### CI baseline

Every code project gets a CI workflow that runs on push and pull request:

```yaml
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install deps
        run: [your install command]
      - name: Lint
        run: [your lint command]
      - name: Test
        run: [your test command]
```

This is the floor. Add type checking, coverage, security scanning on top of it.

---

## 7. Guardrails

These apply to both humans and AI agents working in the project.

### Never without explicit approval

| Action | Why |
|--------|-----|
| `rm -rf` or bulk file deletion | Irreversible |
| `git reset --hard` | Destroys uncommitted work |
| Force push to a shared branch | Rewrites history others depend on |
| Direct push to `main` | Bypasses review |
| Global package / environment changes | Affects everything outside the project |
| Architectural changes not covered by existing context | Needs a decision, not an assumption |

### Always required

- Secrets stay out of the repo — no exceptions
- New files fit the established project structure
- CI must pass before merge
- Breaking changes are documented, not silently shipped

---

## 8. Anti-Patterns

| Anti-Pattern | Why It's Wrong | Correct Approach |
|---|---|---|
| `print()` in library code | Breaks testability and reuse | Return results; print in the CLI layer |
| Hardcoded config values | Breaks portability | Read from config file or env vars |
| `except Exception: pass` | Silently hides bugs | Log and handle, or let it propagate |
| Loading config at import time | Causes side effects, makes testing hard | Load lazily or at startup in `main()` |
| Wildcard imports | Pollutes namespace, breaks tooling | Import explicitly |
| `git add .` blindly | May stage secrets, logs, build artifacts | Stage specific files by name |
| Secrets in config files | Even gitignored files get accidentally staged | Env vars or a secrets manager |
| Tests that test the framework | Wasted coverage | Test your logic, not third-party behavior |
| Comments that describe what the code does | Code should be self-documenting | Comment the *why*, not the *what* |
| Skipping the test on "just a small change" | Small changes cause regressions too | Run the fast suite before every commit |
| One giant file | Hard to read, test, and maintain | Split by responsibility when complexity grows |
| Abstractions built for one use | Premature generalization | Write it inline; extract when used 3+ times |
