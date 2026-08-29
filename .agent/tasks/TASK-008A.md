# TASK-008A: Docker Test Runner Container Build

**Milestone**: M5  
**Assigned to**: LatentCode  
**Status**: pending  
**Depends on**: None  

---

## Goal

Create the Docker container image used to safely execute pytest in isolation. This container provides a clean Python 3.11 environment with pytest and pytest-json-report pre-installed. It is the execution environment for the sandbox executor (TASK-008B). This task has no backend code dependencies and can be executed in parallel with earlier tasks.

---

## Context Files to Read

Before implementing:
1. `.agent/constitution.md`
2. `.agent/architecture.md`
3. This task file

---

## Inputs

- None (standalone task)

## Outputs

```
docker/test-runner/Dockerfile        ← New file
docker/test-runner/requirements.txt  ← New file
```

---

## Acceptance Criteria

### AC-1: Dockerfile exists and is valid
- `docker/test-runner/Dockerfile` exists
- Base image: `python:3.11-slim`
- Installs dependencies from `docker/test-runner/requirements.txt`
- Sets working directory to `/workspace`
- Default command: `pytest /workspace --json-report --json-report-file=/tmp/results.json -q`

### AC-2: Requirements file
- `docker/test-runner/requirements.txt` contains:
  ```
  pytest>=7.0
  pytest-json-report>=1.5
  ```

### AC-3: Image builds successfully
- Running `docker build -t migration-verifier-runner docker/test-runner` completes without errors

### AC-4: Image runs pytest
- Running `docker run --rm migration-verifier-runner pytest --version` prints the pytest version and exits 0

### AC-5: JSON report works
- Running pytest inside the container with `--json-report --json-report-file=/tmp/results.json` produces a valid JSON file at `/tmp/results.json`

---

## Non-Goals

- Do NOT write any Python backend code
- Do NOT implement the sandbox executor (that is TASK-008B)
- Do NOT add any security hardening to the Dockerfile itself (security constraints are applied at container runtime in TASK-008B)
- Do NOT include any application code in the image

---

## Technical Constraints

- Base image: `python:3.11-slim` (lightweight, matches project Python version)
- Only install `pytest` and `pytest-json-report` — no other packages
- The image should NOT contain any project code — code is bind-mounted at runtime
- Image tag: `migration-verifier-runner`

---

## Implementation Details

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /workspace

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

CMD ["pytest", "/workspace", "--json-report", "--json-report-file=/tmp/results.json", "-q"]
```

### requirements.txt

```
pytest>=7.0
pytest-json-report>=1.5
```

You may implement this exactly as shown or adjust as long as all ACs pass.

---

## Verification

```bash
docker build -t migration-verifier-runner docker/test-runner
docker run --rm migration-verifier-runner pytest --version
```

Both commands must succeed. The `pytest --version` command must print a version number and exit 0.

---

## Blocker Section

*(LatentCode fills this in if blocked)*

---

## Implementation Plan

*(LatentCode fills this in before implementing)*
