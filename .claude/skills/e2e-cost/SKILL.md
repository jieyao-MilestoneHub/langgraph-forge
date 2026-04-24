---
name: e2e-cost
description: Estimate the Bedrock LLM cost of running goal lane E2E tests BEFORE execution. Use this before running any significant E2E test batch. Warns if estimated cost exceeds thresholds. Based on real spec max_iterations and Claude Sonnet 4.6 pricing.
---

# E2E Cost Estimator

Run this **before** executing E2E tests to know the Bedrock cost upfront.

## Warning Thresholds

| Scope | Warn at | Stop & Confirm at |
|-------|---------|-------------------|
| Single workflow | > $3.00 | > $5.00 |
| One category (8-16 tests) | > $10.00 | > $20.00 |
| Full functional suite (40 tests) | > $20.00 | > $40.00 |
| Functional + Quality (80 tests) | > $40.00 | > $80.00 |

## Model Pricing (Claude Sonnet 4.6 on AWS Bedrock, 2025)

| Token Type | Price |
|-----------|-------|
| Input | $3.00 / 1M tokens |
| Output | $15.00 / 1M tokens |

> **Note**: `LLMUsageTracker` in `tests/e2e/real_aws/conftest.py` still uses Haiku pricing
> ($0.25/$1.25). The tracker is 12× too cheap. Use the numbers below for real budgeting.

## Cost Formula

```
cost_per_workflow ≈ max_iterations × (5,000 input_tokens × $3/1M + 400 output_tokens × $15/1M)
                  = max_iterations × $0.021
```

The 5,000 input / 400 output per iteration is a conservative midpoint:
- System prompt is ~3,000 tokens (loaded once, passed every iteration)
- Tool output accumulates as conversation history (~1,000-2,000 tokens per prior step)
- Agent output per turn: ~200-600 tokens

High-tool-count or multi-phase workflows cost more per iteration than simple ones.

---

## Quick Estimate Script

Run from `backend-api/`:

```bash
cd /home/docker_admin/develop/convilyn/backend-api
python3 - <<'EOF'
import json, glob, sys

INPUT_COST_PER_1M  = 3.00   # Claude Sonnet 4.6 Bedrock
OUTPUT_COST_PER_1M = 15.00
AVG_INPUT_PER_ITER  = 5000
AVG_OUTPUT_PER_ITER = 400

def per_iter_cost():
    return (AVG_INPUT_PER_ITER * INPUT_COST_PER_1M / 1e6 +
            AVG_OUTPUT_PER_ITER * OUTPUT_COST_PER_1M / 1e6)

def load_max_iterations(spec_id: str) -> int:
    cat, name = spec_id.split(".", 1)
    search_dirs = [
        f"app/orchestrator/specs/goal_lane",
        f"app/orchestrator/specs/{cat}",
        f"app/orchestrator/specs/enterprise",
    ]
    for d in search_dirs:
        try:
            spec = json.load(open(f"{d}/{name}.json"))
            return spec.get("agent_config", {}).get("max_iterations", 25)
        except FileNotFoundError:
            continue
    return 25  # fallback

# --- Specify which workflows to estimate ---
# Replace with your actual test targets, or use sys.argv[1:] for a list
TARGET_WORKFLOWS = [
    # career_toolkit
    "goal_lane.resume_to_job_ready",
    "goal_lane.cover_letter",
    "goal_lane.interview_prep",
    "goal_lane.resume_section_rewriter",
    "goal_lane.jd_requirement_extractor",
    "goal_lane.jd_comparison_table",
    "goal_lane.rejection_feedback_analyzer",
    "goal_lane.career_document_organizer",
    # document_analysis
    "goal_lane.contract_summary",
    "goal_lane.contract_comparison",
    "goal_lane.nda_review",
    "goal_lane.financial_statement_summary",
    "goal_lane.commercial_document_generator",
    "goal_lane.business_report_summary",
    "goal_lane.vendor_comparison",
    "goal_lane.proposal_generator",
    "goal_lane.proposal_reviewer",
    "goal_lane.action_items_extractor",
    "goal_lane.compliance_checklist",
    "goal_lane.policy_structurer",
    "goal_lane.sop_builder",
    # enterprise
    "enterprise.audit_evidence_pack",
    "enterprise.policy_update_impact",
    "enterprise.release_compliance_gate",
    # learning_tools (add when specs exist)
]

print(f"\n{'workflow_id':<48} {'max_iter':>8}  {'est_cost':>9}")
print("-" * 70)

total = 0.0
warn_workflows = []
for wf in TARGET_WORKFLOWS:
    iters = load_max_iterations(wf)
    cost  = iters * per_iter_cost()
    total += cost
    flag = "  ⚠️ HIGH" if cost > 3.0 else ""
    if cost > 3.0:
        warn_workflows.append((wf, cost))
    print(f"{wf:<48} {iters:>8}  ${cost:>8.4f}{flag}")

print("-" * 70)
print(f"{'TOTAL':<48} {'':>8}  ${total:>8.4f}")
print(f"  + quality suite (×2):                                    ${total*2:>8.4f}")

print()
if total > 40.0:
    print("🛑 STOP: Full suite cost exceeds $40. Confirm with user before proceeding.")
elif total > 20.0:
    print("⚠️  WARNING: Full suite cost exceeds $20. Consider running one category at a time.")
elif total > 10.0:
    print("⚠️  Note: Moderate cost. Recommend running categories sequentially with -x.")
else:
    print("✅ Cost within normal range. Safe to proceed.")

if warn_workflows:
    print(f"\nHigh-cost workflows (>$3 each):")
    for wf, c in warn_workflows:
        print(f"  {wf}: ${c:.4f}")
EOF
```

---

## Known High-Cost Workflows (as of 2026-03-27)

| Workflow | max_iterations | Est. Cost |
|---------|--------------|-----------|
| `goal_lane.resume_to_job_ready` | 120 | ~$2.52 |
| `goal_lane.interview_prep` | 45 | ~$0.95 |
| `goal_lane.career_document_organizer` | 45 | ~$0.95 |
| `goal_lane.jd_comparison_table` | 45 | ~$0.95 |
| `goal_lane.cover_letter` | 40 | ~$0.84 |
| `goal_lane.resume_section_rewriter` | 35 | ~$0.74 |

Full functional suite (24 workflows, career_toolkit + document_analysis + enterprise): **~$16.80**

Full functional + quality (×2): **~$33.60**

---

## Per-Category Estimates

Run one category at a time with `-x` to limit waste on failures:

```bash
# Step 1 — cheapest category first, fail fast
poetry run pytest tests/e2e/goal_lane/functional/career_toolkit/ -x  # ~$7.20
poetry run pytest tests/e2e/goal_lane/functional/document_analysis/ -x  # ~$6.30
poetry run pytest tests/e2e/goal_lane/functional/enterprise/ -x  # ~$1.65
poetry run pytest tests/e2e/goal_lane/functional/learning_tools/ -x  # ~TBD
```

---

## Updating This Estimate

When `max_iterations` changes in a spec JSON, the cost estimate changes proportionally.
The script above reads specs live — re-run before each test session.

If `LLMUsageTracker` pricing is updated in `tests/e2e/real_aws/conftest.py`, update the
pricing constants in this file too (`INPUT_COST_PER_1M`, `OUTPUT_COST_PER_1M`).
