# Unit Testing Strategy

單元測試必須以「**測試項目本身**」為導向，而不是以「函式名稱 / 類別名稱」為導向。每個測試在新增或修改時，作者要能明確回答：這個測試在驗證下面哪一類檢查，以及為什麼這個輸入值落在該類別。

## 四類必檢項目

任何新寫或修改的單元測試，都必須確認以下四類中「**適用的每一類都有覆蓋**」（不適用的類別可不寫，但要能說明為何不適用）：

### 1. 邏輯檢查（Logic Check）

- 給定正確、預期的輸入，系統是否執行**正確的計算**並走過**正確的程式路徑**？
- 所有分支（if / elif / else / match / switch / early return）都要有一個測試把它踩到。
- 條件組合（AND / OR）要覆蓋到能讓整體布林值翻轉的輸入對。
- 純函式優先用「已知輸入 → 已知輸出」的 parametrized / table-driven 風格，一行一 case。

### 2. 邊界檢查（Boundary Check）

對每個輸入參數，至少三類：

| 類型 | 說明 | 範例（預期 3–7 的整數） |
|------|------|-----------------------|
| **Typical** | 典型、處於合法範圍中間 | `5` |
| **Edge** | 剛好在合法邊界上 | `3`、`7` |
| **Invalid** | 越界、型別錯誤、空、過長、過大 | `2`、`8`、`-1`、`None`、`"foo"` |

其他常見邊界：空集合（`[]` / `{}` / `""`）、單元素、極大 / 極小值、Unicode / 多 locale（此 repo 有 en/zh/ja/ko）、時區邊界（UTC 對比本地）、浮點精度、off-by-one。

### 3. 錯誤處理（Error Handling）

- 對 invalid 輸入與外部失敗（network / DB / LLM / S3 / DynamoDB），系統是否**以定義過的方式**回應？
  - 丟出特定例外類別（而不是泛型 `Exception`）；
  - 回傳特定 error result / discriminated union；
  - 不吃掉錯誤、不印到 stdout 後假裝沒事。
- 每個 `raise` / `throw` 路徑都要有一個測試觸發它，並 assert 訊息或 error code（不只是「有丟」）。
- 絕不用 `assert not raises` 當作通過條件；錯誤處理測試必須 assert 錯誤本身。
- Retry / timeout / circuit breaker 的測試：要 assert 呼叫次數與結束條件，不能只 assert 最終結果。

### 4. 物件導向性檢查（Object State Check）

若執行被測程式碼會改變任一**持久物件**（DB row、DynamoDB item、S3 object、Redux / TanStack Query cache、LangGraph `state`、checkpoint），測試必須：

1. 在執行前讀一次狀態（baseline）；
2. 執行；
3. 讀一次狀態並 assert **每一個預期被改的 key / field** 的新值；
4. Assert **不該被改的欄位沒被改到**（防止意外的 side-effect / 違反 immutability）。

對本 repo 特別重要：`GoalAgentState`、`MultiAgentEnvelope.specialist_results`、`handoff_history`、`exception_queue`、`domain_envelopes` 的每一次 merge 都要用這個模式測，因為 reducer 的錯誤會沉默地污染後續步驟。

## 最佳實踐（Best Practices）

### 使用單元測試框架（不要手刻）

為每個程式碼區塊寫全自訂的 assertion 腳手架是浪費時間；每個主流語言都有成熟框架，就用它。本 repo 的唯一答案：

| 語言 / 位置 | 框架 | 輔助 |
|-------------|------|------|
| Backend Python (`backend-api/`, `mcp_server/*/`) | **pytest**（**不是** `unittest`） | `pytest-asyncio`、`pytest.mark.parametrize`、`pytest-mock`、`moto`（AWS in-memory）、`freezegun`（時間） |
| Frontend TS/TSX (`frontend-web/`) | **Jest** | `@testing-library/react`、`jest.useFakeTimers`、MSW（網路 mock） |

不自創 assertion helper、不手寫 test runner、不在 `if __name__ == "__main__"` 裡寫 ad-hoc 測試。新功能的測試必須放進框架能自動收集到的位置（`tests/unit/**/test_*.py`、`**/*.test.ts(x)`），否則 CI 看不到 = 等於沒寫。

### 自動化單元測試（多觸發點，不能漏）

單元測試必須在**多個事件上自動觸發**，靠人工記得去跑 = 遲早會忘：

- **Pre-commit hook**（`.pre-commit-config.yaml`）— 已對 backend 跑 `ruff / black / pyright`、對 frontend 跑 `prettier / eslint / tsc`。受影響的測試在這一關先過（fail → 修 → 重 stage → 重 commit，**禁用 `--no-verify`**）。
- **Push to `develop`** — 觸發 `Backend CI` + frontend lint/type/test。這是合流前最後一道自動閘。合流前紅燈 = 先修好再合，**不修 CI 繞過**。
- **Release / deploy 前** — 合到 `main` 的 PR 必須 CI 全綠，`backend-deploy.yml` / `mcp-deploy.yml` 才會在 develop 推動後跑（見 `CLAUDE.md` 的 CI/CD 段）。
- **排程全量跑**（未來要補）— Flaky test 與環境 drift 只有在「長時間沒人碰的那塊」才現形；如果 repo 新增 nightly schedule workflow，要把 `tests/unit/` 完整跑一次。

新寫測試時，腦中必問：「這個測試會在上述幾個觸發點自動跑到？」如果答案是零，配置錯了 —— 先修配置，再合測試。

### 一次斷言（One Assertion per Test）

每個單元測試只該產生**一個 true/false 結果**。多個 assertion 混在同一個測試裡，失敗時無法一眼看出是哪一條掛掉，也會遮蔽後面的 assertion（第一條 fail 後，後面的根本不會跑）。

規則：

- 一個 `test_xxx` / `it(...)` 對應**一個行為宣稱** + **一個 `assert` / `expect`**。
- 命名用 `test_<主詞>_<情境>_<預期行為>` 或 `it("<主詞> <should|returns|raises> ... when ...")` —— 測試名本身就說出那個唯一結果是什麼。
- 不同輸入產生不同結果 → 用 `pytest.mark.parametrize` 或 `it.each` 把它拆成 N 個測試；**不要**在一個測試裡寫 for-loop 疊 assertion。
- 要同時驗證一個物件的多個欄位 → 合併成**一個結構比對**（`assert result == expected_dict` / `expect(obj).toEqual(expected)`），整體 pass/fail 就是一個結果；而不是五行 `assert result.a == ...` + `assert result.b == ...`。
- 例外驗證：`with pytest.raises(MyError, match="..."):` / `expect(() => ...).toThrow(MyError)` —— 這本身就是一次斷言。

### AAA 結構

每個測試 = **Arrange / Act / Assert** 三段，空行區隔；不要讓 setup 混進 assertion 段。配合「一次斷言」，`Assert` 段落只有一行。

### 決定性與隔離

- **No network, no real AWS, no wall-clock, no random without seed** — 會讓測試變 flaky 的通通 mock 掉或注入。時間用 `freezegun` / `jest.useFakeTimers`，亂數用固定 seed。
- 單元測試 = Moto / in-memory，**不是** LocalStack、不是真 AWS。那是 integration / e2e 的工作（見 `CLAUDE.md` 的三層測試表）。
- 每個測試必須能單獨跑、也能任意順序跑。共享狀態一律在 fixture teardown 清掉。

### 測公開契約，不測實作細節

- 測 return value、persistent side-effect、emitted event、raised exception —— 這些是合約。
- **不要**測 private method、不要 assert 中間變數長什麼樣、不要 assert mock 被呼叫的**順序**（除非順序本身就是合約）。
- 重構改變實作但不改變行為時，測試不該壞。如果壞了，多半是測試測錯了層。

### Mock 的紀律

- Mock 用來隔離外部邊界（network、AWS、LLM、DB）；不 mock 自己寫的 pure function。
- 一個測試裡 mock 超過 3 個東西 → 被測單元太大，先拆它再測。
- Mock 的 return value 必須是真實 API 會回的 shape（用 recorded fixture 或 Pydantic factory），不要手刻假物件。

### 覆蓋率是信號不是目標

- 新寫 / 修改的模組目標行覆蓋 ≥ 80%、分支覆蓋 ≥ 70%，但**邏輯 + 邊界 + 錯誤 + 物件狀態四類都有覆蓋**比數字重要。
- 100% 行覆蓋 + 零邊界測試 = 假安全感。寧可 75% 但四類齊全。

### 從一開始就寫，不要「之後補」

單元測試最常被跳過的藉口：prototype、小範圍、趕時間。這三個理由會隨時間累積成技術債：一旦 code 先上、測試缺席變成常態，之後沒人會回頭補；重構時缺少 safety net，壞了沒人察覺；新進的人照抄現狀「原來這裡不用寫測試」。

本 repo 的立場：**新模組 / 新 specialist / 新 processor / 新 API 路由 / 新 spec 驗證邏輯，在同一個 commit 或同一個 PR 內附測試**，不拆成「先上程式，下個 sprint 補測試」。Tier D 之後的 agent / prompt pack / eval harness 新增件同樣適用。

例外只有一種：**research spike / 確定會被丟掉的 prototype**。這類 code 必須在 commit message / PR description 明確標注「SPIKE, not production-bound」，且不得合進 `develop` 的生產路徑。

單元測試 only（不碰 LocalStack / 真 AWS）：

```bash
# Backend
poetry run pytest tests/unit/ -v
poetry run pytest tests/unit/path/test_file.py::test_name -v   # 單一 case

# Frontend
pnpm test                  # 全部
npx jest <pattern>         # 單一檔 (NOT `npm test -- --testPathPattern`)
```

`tests/integration/` 與 `tests/e2e/` 不屬於本規則 —— 那兩層有自己的成本與基礎設施，見 `CLAUDE.md` 的 Local environment 段。

## 作者 Checklist（commit 前）

新寫或修改測試後：

- [ ] 每個被改過的分支都有測試踩到
- [ ] 每個參數都有 typical + edge + invalid 三類（不適用請註解說明）
- [ ] 每個 `raise` / `throw` 路徑都有測試，且 assert 了具體例外型別或 error code
- [ ] 被動過的持久物件（DB / envelope / state / cache）都 assert 了該改的欄位**與**不該改的欄位
- [ ] 每個測試只有**一個 assertion**（多欄位用結構比對合併，不是疊多行 `assert`）
- [ ] 測試名稱能在不看 body 的情況下描述清楚它在驗什麼
- [ ] 沒有 network / 真 AWS / 無 seed 的亂數 / 未凍結的時鐘
- [ ] 測試可獨立跑、可任意順序跑
- [ ] 測試被框架自動收集到（路徑 + 命名符合 pytest / Jest 慣例），pre-commit 或 CI 會觸發到
