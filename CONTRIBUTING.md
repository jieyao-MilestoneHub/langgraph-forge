# Contributing to langgraph-forge

Thanks for wanting to help. This doc captures the project's engineering conventions so your first PR lands cleanly.

## Dev environment

```bash
# Install uv (one-time, if you don't have it)
# Windows (PowerShell):   irm https://astral.sh/uv/install.ps1 | iex
# macOS / Linux:          curl -LsSf https://astral.sh/uv/install.sh | sh

git clone https://github.com/CoreNovus/langgraph-forge.git
cd langgraph-forge
uv sync --dev
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg
```

`uv sync --dev` installs core runtime deps + the `dev` extras (ruff, pyright, pytest, pre-commit, build, twine, git-cliff). Cloud extras (`bedrock`, `vertex`, `azure`) are **not** installed by default — CI doesn't need them and most development doesn't either.

## Branch strategy

- **`develop`** is the active branch. All regular work commits land here via short-lived feature branches merged with squash (or via push for maintainers).
- **`main`** is release-only. It receives merges from `develop` via PR when we cut a tagged release (`0.1.0a1`, `0.1.0rc1`, `0.1.0`, ...).
- Never force-push to `main`. Never run a deploy workflow against `main` outside a release cut.

Create your branch from `develop`:

```bash
git switch develop
git pull
git switch -c feat/my-thing
```

## Commit convention

We use [Conventional Commits](https://www.conventionalcommits.org/) (enforced by a commit-msg hook) because `git-cliff` generates the changelog from commit prefixes. Valid prefixes:

| Prefix | Use for |
|---|---|
| `feat` | New user-facing feature |
| `fix` | Bug fix |
| `docs` | Docs-only change |
| `test` | Tests (added or refactored) |
| `refactor` | Structural change, no behaviour diff |
| `perf` | Performance improvement |
| `build` | Build system / dependency change |
| `ci` | GitHub Actions / pre-commit change |
| `chore` | Repo metadata, release cuts, misc |
| `style` | Formatting only |
| `revert` | Revert a prior commit |

Scope is the subpackage when relevant: `feat(builders): ...`, `test(deploy): ...`, `refactor(scaffold): ...`. Breaking changes get a `!`: `feat(deploy)!: rename prepare to build`.

### TDD discipline

Every new behaviour lands as a pair:

1. `test(<scope>): <behaviour>` — failing test.
2. `feat(<scope>): <behaviour>` — minimum impl to pass.

Combine into one `feat(...)` commit only when test + impl together are under ~30 LOC and separating adds no review value. Refactor commits land after green, with `refactor(<scope>): <what + why>`, no new tests, no behaviour diff.

## Code quality gates

Each commit must keep these green:

- `uv run ruff format --check .`
- `uv run ruff check .`
- `uv run pyright`
- `uv run pytest -q`

Pre-commit runs ruff + pyright + detect-private-key locally on every commit. CI runs the full matrix `{3.11, 3.12, 3.13} × {ubuntu, macos, windows}`.

## PR checklist

Before requesting review, verify:

- [ ] Every changed branch has a test that exercises it (logic check)
- [ ] Each input parameter has typical / edge / invalid cases (boundary check)
- [ ] Every `raise` path has a test asserting the specific exception (error check)
- [ ] Mutations of persistent state (graph state, envelope, cache) assert both the fields that changed and the fields that did not (object-state check)
- [ ] One assertion per test (multi-field checks use structure comparison)
- [ ] Tests have no network, no real LLM calls, no wall-clock timestamps, no unseeded randomness
- [ ] Commit messages follow Conventional Commits
- [ ] `README.md` or inline docstrings updated if the public API changed
- [ ] Any `NotImplementedError` added or removed is reflected in the docs

## Adding a new deployment adapter (in-tree)

1. `src/langgraph_forge/deploy/<name>.py` — satisfy the Protocol (`name`, `requires_extras`, `prepare`, `invoke`, `template_fragment`). Import the cloud SDK **lazily** inside `prepare` / `invoke`.
2. `src/langgraph_forge/scaffold/templates/deploy_fragments/<name>/src/{{ package_name }}/deploy.py.j2` — the scaffolded `deploy.py` importing your adapter.
3. `pyproject.toml` — add extras + entry-point declaration under `langgraph_forge.deployment_adapters`.
4. `tests/unit/deploy/test_<name>.py` — Protocol conformance + extras + stub behaviour.

## Adding a new deployment adapter (out of tree)

Publish your own package (`langgraph-forge-modal`, `langgraph-forge-cloudflare`, ...) with an entry-point targeting the `langgraph_forge.deployment_adapters` group. Users `pip install your-package` and the adapter appears in `list-deploy` automatically. No changes to this repo required.

## Releasing

Maintainers only. See internal docs (coming with phase 9 of the plan).

## Code of conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md) v2.1. Unacceptable behaviour can be reported per SECURITY.md's private-disclosure process.
