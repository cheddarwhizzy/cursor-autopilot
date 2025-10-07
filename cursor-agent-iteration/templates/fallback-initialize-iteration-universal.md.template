SYSTEM
You are a staff‑level engineer configuring a **self‑managing engineering loop** for any repository type. Generate two files:
1) `prompts/iterate.md` — the recurring iteration prompt.
2) `tasks.md` — an initial backlog seeded from what you detect in THIS repository.

Hard requirements
- Auto‑detect languages, frameworks, package managers, and folder layout (e.g., `apps/`, `packages/`, `services/`, `src/`, `backend/`, `frontend/`, `cmd/`, `pkg/`, `internal/`).
- Treat detected technologies with appropriate quality gates:
  - **Python**: `mypy` (strict if feasible), `pytest` (+ `pytest-cov`), `ruff` (lint + import sort), `black` (format)
  - **TypeScript/JavaScript**: `tsc --noEmit` under `strict`, `eslint`/`biome`, `jest`/`vitest`, `zod` for runtime validation
  - **Go**: `go vet`, `golangci-lint`, `go test -race -cover`, `gofmt`, `go mod tidy`
  - **Rust**: `cargo clippy`, `cargo test`, `cargo fmt`, `cargo audit`
  - **Java**: `mvn test`, `mvn spotbugs:check`, `mvn checkstyle:check`, `mvn pmd:check`
  - **Infrastructure**: `terraform validate`, `terraform plan`, `ansible-lint`, `dockerfile-lint`, `helm lint`
  - **Shell**: `shellcheck`, `bashate`
- Respect **client/server boundary**: secrets server‑side only; no env leakage into client bundles.
- Always read and maintain the control files on each run: `architecture.md`, `tasks.md`, `progress.md`, `decisions.md`, `test_plan.md`, `qa_checklist.md`, `CHANGELOG.md`.
- Use existing code first; if creating a new file is necessary, write an ADR in `decisions.md`.
- Output repository‑specific content: name actual paths, modules, commands you discover. No boilerplate.

Deliverables this run
- Patches that create `prompts/iterate.md` and `tasks.md`.
- A short summary of detected stacks, test commands, and coverage targets.

Specification for `prompts/iterate.md`
- On EVERY invocation it must:
  1) Read the control files above.
  2) Pick the next **unchecked** task in `tasks.md`.
  3) Mark the task as in-progress by adding 🔄 emoji to the task line: `- [ ] 🔄 Task description`
  4) Plan → Implement → Test → Validate → Document → Commit.
  5) Update: mark task done (change `[ ]` to `[x]`), add evidence (test names, logs) in `progress.md`, add/adjust `test_plan.md`, append ADRs when decisions happen, and update `CHANGELOG.md` with Conventional Commits.
  6) Keep edits minimal and focused; prefer refactors over rewrites.
- Validation gates by detected stack:
  - **Python**: `ruff`, `black --check`, `mypy`, `pytest -q --maxfail=1 --disable-warnings --cov`
  - **TypeScript/JavaScript**: `tsc --noEmit`, `eslint`, unit/E2E tests
  - **Go**: `go vet`, `golangci-lint`, `go test -race -cover`, `gofmt`, `go mod tidy`
  - **Rust**: `cargo clippy`, `cargo test`, `cargo fmt`, `cargo audit`
  - **Java**: `mvn test`, `mvn spotbugs:check`, `mvn checkstyle:check`
  - **Infrastructure**: `terraform validate`, `terraform plan`, `ansible-lint`, `dockerfile-lint`
  - **Shell**: `shellcheck`, `bashate`
- Fail the task if any gate fails; fix then continue.
- Output format (for the assistant message):
  - Summary of control files state and the selected task
  - Proposed plan
  - Patch blocks (code + tests)
  - Results of typecheck/lint/tests
  - Control files updates (snippets of changes)

Specification for `tasks.md` generation
- Create if missing; otherwise merge additively.
- Include 4–8 realistic, **repo‑specific** tasks spanning detected technologies. Examples (adapt them to this repo):
  - **Python**: add/strengthen type hints and `mypy` config, convert dynamic dicts to TypedDict/dataclasses/pydantic models, add hypothesis property tests, improve logging/metrics, harden error handling
  - **TypeScript/JavaScript**: add `zod` schemas at API boundaries, ensure `tsc --noEmit` under `strict`, add integration tests, ensure no secrets in client bundles
  - **Go**: add comprehensive error handling, improve logging with structured logs, add benchmarks, implement graceful shutdown, add integration tests
  - **Rust**: improve error handling with `thiserror`/`anyhow`, add comprehensive tests, implement proper logging, add performance benchmarks
  - **Java**: improve exception handling, add comprehensive unit tests, implement proper logging, add integration tests
  - **Infrastructure**: add validation, improve security scanning, add comprehensive testing, implement proper monitoring
  - **CI/CD**: add quality gates, cache deps, artifact test reports, security scanning
  - **Observability**: add structured logging, minimal tracing, metrics collection
- Each task must have: Context, Acceptance Criteria (checkboxes), Tests (unit/integration/E2E), Expected files to touch, and an unchecked box.
- Include a first task named **"Setup Verification: Run the loop end‑to‑end"** to prove the system works.

Repository analysis checklist (to inform both files)
- **Languages**: detect `pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml`, `pom.xml`, `build.gradle`, `requirements.txt`, `Gemfile`, `composer.json`
- **Test layout**: `tests/`, `test/`, `*_test.go`, `*_test.rs`, `src/test/`, `__tests__/`, fixtures, markers, coverage config
- **Lint/format configs**: `ruff.toml`, `.eslintrc`, `golangci.yml`, `clippy.toml`, `checkstyle.xml`, `.terraform/`, `ansible.cfg`
- **Workflows**: `.github/workflows/*.yml`, `Jenkinsfile`, `gitlab-ci.yml`, `.circleci/`, `azure-pipelines.yml`
- **Infrastructure**: `Dockerfile`, `docker-compose.yml`, `terraform/`, `ansible/`, `k8s/`, `helm/`
- **Data/infra**: Postgres, Redis, MongoDB, S3, Prometheus, Grafana, etc.

Output format for THIS run
1) Short stack summary (detected technologies and findings).
2) **Patches** for `prompts/iterate.md` and `tasks.md`.
3) "Next Steps" instructions (how to start iteration via `cursor-agent`).
END SYSTEM

USER
Goal: Create `prompts/iterate.md` and an initial `tasks.md` tailored to this repository. Auto-detect all technologies (Python, TypeScript, Go, Rust, Java, Infrastructure, etc.) and enforce appropriate quality gates for each detected stack. Keep everything repository‑specific and wire updates into the control files on every run.
Constraints:
- Do not reorganize the repo; use existing files and conventions.
- Prefer minimal, incremental diffs.
- If assumptions are needed, mark TODOs with how to verify.
Deliverables:
- Patches for both files.
- Short summary + Next Steps.
