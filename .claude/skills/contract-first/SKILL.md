---
name: contract-first-alignment
description: Use this skill when frontend and backend APIs are misaligned, unclear, or causing integration issues. Enforces a contract-first workflow to ensure both sides agree on API specifications before implementation.
---

# Contract-First Alignment Skill

This skill enforces a **contract-first development approach** to eliminate misalignment between frontend and backend systems.

## When to Activate

* Frontend and backend integration is failing or inconsistent
* API response format differs from expectation
* Unclear or undocumented API contract
* Frequent breaking changes between FE/BE
* Starting a new feature involving API design
* Refactoring APIs or data models
* Debugging integration issues between teams

## Core Principle

> **The contract is the single source of truth.**
> No frontend or backend implementation should proceed without a clearly defined and agreed contract.

## Step-by-Step Alignment Process

### 1. Identify the Mismatch

#### Symptoms

* Frontend parsing errors
* Undefined/null fields
* API response shape mismatch
* Type errors (TypeScript / runtime)
* Backend returning unexpected structure

#### Actions

* [ ] Capture actual API response (logs / network tab)
* [ ] Compare with frontend expected types/interface
* [ ] List all mismatched fields explicitly

---

### 2. Define / Extract the Contract

If contract **does NOT exist**, create one.
If contract **exists but unclear**, rewrite it clearly.

#### Contract Format (Required)

```typescript
// Example: User API Contract

type GetUserResponse = {
  id: string
  email: string
  name: string
  avatarUrl?: string
  createdAt: string
}

type GetUserError = {
  error: string
  code: number
}
```

#### OR OpenAPI Style

```yaml
GET /api/user/{id}

response:
  200:
    application/json:
      {
        "id": "string",
        "email": "string",
        "name": "string",
        "avatarUrl": "string | null",
        "createdAt": "ISO8601 string"
      }
```

#### Requirements

* [ ] Field names explicitly defined
* [ ] Types clearly specified (string, number, enum, nullable)
* [ ] Optional vs required fields defined
* [ ] Error response defined
* [ ] Date/time format standardized (ISO 8601)

---

### 3. Validate the Contract with Stakeholder (YOU)

⚠️ **CRITICAL STEP — DO NOT SKIP**

Before implementation:

* [ ] Confirm contract matches product requirements
* [ ] Ask for clarification on ambiguous fields
* [ ] Validate naming consistency
* [ ] Validate edge cases

#### Questions to Ask

* Should this field ever be null?
* What happens if data is missing?
* Is this field required for UI rendering?
* Are there pagination / limits?
* Should errors be standardized?

If ANY uncertainty exists → **STOP and discuss with user**

---

### 4. Freeze the Contract

Once agreed:

* [ ] Mark contract as FINAL
* [ ] Share with both frontend & backend
* [ ] Store in a central location (e.g. `/contracts`, OpenAPI spec)

#### Rules After Freeze

* ❌ No silent changes
* ❌ No breaking changes without versioning
* ✅ All changes require discussion

---

### 5. Implement Against Contract

#### Backend Responsibilities

* [ ] Return EXACT contract shape
* [ ] No extra/missing fields
* [ ] Validate response before sending
* [ ] Normalize data format

#### Frontend Responsibilities

* [ ] Use typed interfaces (TypeScript)
* [ ] Do NOT guess fields
* [ ] Handle optional/null safely
* [ ] Implement error handling per contract

---

### 6. Add Runtime Validation (Recommended)

#### Backend Validation

```typescript
import { z } from 'zod'

const ResponseSchema = z.object({
  id: z.string(),
  email: z.string().email(),
  name: z.string()
})

function sendResponse(data: unknown) {
  const validated = ResponseSchema.parse(data)
  return validated
}
```

#### Frontend Validation

```typescript
const result = ResponseSchema.safeParse(apiResponse)

if (!result.success) {
  console.error('Contract mismatch', result.error)
}
```

#### Verification Steps

* [ ] Response matches schema at runtime
* [ ] Fail fast on mismatch
* [ ] Logs clearly indicate contract violations

---

### 7. Contract Testing

#### Example Tests

```typescript
test('API matches contract', async () => {
  const res = await fetch('/api/user/1')
  const json = await res.json()

  expect(json).toMatchObject({
    id: expect.any(String),
    email: expect.any(String),
    name: expect.any(String)
  })
})
```

#### Verification Steps

* [ ] Contract tests exist for all endpoints
* [ ] CI fails on contract mismatch
* [ ] Mock data follows contract

---

### 8. Versioning Strategy

#### When Breaking Changes Are Needed

* [ ] Create new version (`/v2/api/...`)
* [ ] Maintain backward compatibility
* [ ] Deprecate old version gradually

#### NEVER

* ❌ Change field type silently
* ❌ Remove fields without notice
* ❌ Rename fields without versioning

---

## Anti-Patterns (MUST AVOID)

#### ❌ Backend-driven guessing

> "Frontend can just adapt"

#### ❌ Frontend assumptions

> "API probably returns this"

#### ❌ Silent contract drift

> "Just add one field quickly"

#### ❌ No error contract

> Inconsistent error formats

---

## Pre-Integration Checklist

Before FE/BE integration:

* [ ] Contract defined and agreed
* [ ] Types shared (or generated)
* [ ] Mock API available
* [ ] Edge cases defined
* [ ] Error handling defined
* [ ] Pagination/filtering defined (if needed)

---

## Debugging Workflow (When Broken)

1. Capture real API response
2. Compare with contract
3. Identify mismatch
4. Decide:

   * Fix backend?
   * Fix frontend?
   * Update contract?
5. Re-confirm with stakeholder
6. Update both sides

---

## Recommended Tools

* OpenAPI / Swagger
* Zod (runtime validation)
* tRPC (end-to-end typesafety)
* TypeScript shared types
* Mock Service Worker (MSW)

---

## Final Rule

> ❗ If frontend and backend disagree → the contract is wrong or missing.
> Fix the contract FIRST, not the code.

---

如果你想，我可以幫你再升級成：

* 🔥 **AI 自動檢查 contract mismatch 的版本（更 Claude Code 風格）**
* 🔥 **整合 Supabase / Next.js / tRPC 的實戰版**
* 🔥 **加上 CI/CD 自動驗證 contract 的 skill**
