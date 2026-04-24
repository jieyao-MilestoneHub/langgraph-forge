# Git Workflow Rules

## Branch Strategy (CRITICAL)

- **`develop`** — active development branch; all work happens here
- **`main`** — production branch; NEVER push or deploy directly

## Hard Rules

1. **All commits go to `develop`**, never directly to `main`
2. **`develop` → `main` ONLY via Pull Request** — no direct merges, no force pushes
3. **Never run `gh workflow run` without `--ref develop`** — omitting `--ref` defaults to `main`
4. **Never trigger deploys targeting `main`** unless explicitly asked by the user after a PR merge

## Correct Commands

```bash
# Trigger workflow on develop (always specify --ref)
gh workflow run backend-deploy.yml --ref develop -f environment=dev -f image_tag=<sha>
gh workflow run mcp-deploy.yml --ref develop -f environment=dev

# Push only to develop
git push origin develop

# PR to merge develop → main (never direct push)
gh pr create --base main --head develop
```

## Environment Mapping

| Branch | Environment |
|--------|-------------|
| `develop` | dev |
| `main` | prod |
