---
name: org-baseline
description: 稽核並套用 GitHub org 內所有共同維護 repo 的一致設定 —— 合併方式（只允許 squash、合併後刪分支、允許 auto-merge）、main 的 branch protection 與各 repo 的必要檢查、CODEOWNERS、CONTRIBUTING 是否連到 org 共用指南。基準檔放在 `<org>/.github/repo-baseline.json`（單一權威來源），本 skill 只讀它、比對、在使用者同意後套用。當使用者要「新 repo 照 org 設定」、「檢查所有 repo 設定是否一致」、「org 設定稽核」、「branch protection 對齊」、「新開的 repo 要設什麼」、「協作規則套到所有 repo」之類需求時使用，在 org 新增 repo 時也要主動使用。**改 GitHub 設定是對外動作：每個 repo 先列出差異、取得使用者同意才套用；不為了讓稽核通過而改基準檔。**
---

# Org repo 基準：稽核與套用

一個 GitHub org 裡共同維護的 repo，設定與協作規則應該一致。三樣東西各有位置，**本 skill 只負責第二樣**：

| 內容 | 權威來源 |
|------|---------|
| 協作規則本文（fork 流程、誰來合併） | `<org>/.github/CONTRIBUTING.md`（GitHub 會把它當成 org 的預設 community health 檔案） |
| GitHub 設定（合併方式、保護、必要檢查、CODEOWNERS） | `<org>/.github/repo-baseline.json` |
| agent 的行為規則（例如 auto-merge 只用於維護者自己的 PR） | 使用者的常駐 rules（如 `~/.claude/rules/polhem-repos.md`） |

## 基準檔格式

```json
{
  "settings":   { "allow_squash_merge": true, "allow_merge_commit": false, "...": "repos/{repo} 的欄位" },
  "protection": { "strict": true, "enforce_admins": true, "required_approving_review_count": 0, "...": "..." },
  "codeowners": "* @maintainer",
  "repos":      { "<repo>": { "required_checks": ["build", "docs"] } },
  "excluded":   { "<repo>": "為什麼不套用基準" }
}
```

`settings` 與 `protection` 是共用值；每個 repo 唯一不同的是 `required_checks`，因為 job 名稱各自不同。
欄位以該 org 的檔案為準，不在這裡複寫。

## 腳本

`scripts/org_baseline.py`（需要 `gh` 已登入且對 repo 有 admin 權限、`python3`）：

```bash
python3 <skill 目錄>/scripts/org_baseline.py audit --org <org>             # 列出全部差異，有差異時 exit 1
python3 <skill 目錄>/scripts/org_baseline.py apply --org <org> <repo>      # 只顯示會改什麼
python3 <skill 目錄>/scripts/org_baseline.py apply --org <org> <repo> --confirm
```

audit 的每一行標示修法：`[apply]` 由 apply 經 API 修正；`[commit]`（CODEOWNERS、CONTRIBUTING）要透過該 repo
平常的 commit 流程修正，腳本不改檔案。org 裡不在基準檔、也不在 `excluded` 的 repo 會被列出來 —— 新 repo 漏登記就是這樣被發現的。

## 流程

### 稽核（定期，或使用者問「設定一致嗎」）

1. 跑 `audit`，把結果整理成「repo × 差異」表給使用者。
2. 逐項判讀：差異是**該修**，還是**該登記為例外**（寫進 `excluded` 並附理由）？不確定就問。
3. 不為了讓稽核通過而改基準檔的共用值 —— 那等於改規則，需要使用者明確決定。

### 套用 `[apply]` 的差異

1. **先確認必要檢查在每個 PR 都會啟動。** 被設為必要檢查的 job，所在 workflow 的 `pull_request` 觸發不能有
   `paths-ignore` 或 `paths`：只改文件的 PR 不會啟動那個 job，就會永遠等不到必要檢查而無法合併。要跳過只改文件的
   變更，改在 job 內偵測、跳過步驟並回報成功（job 必須啟動）。
2. **必要檢查的名稱要與實際 check run 完全一致。** matrix job 的名稱帶參數（`build (ubuntu-latest)`、`build (20)`），
   以最近一次 PR 或 main commit 的 check run 為準：`gh api repos/<org>/<repo>/commits/<sha>/check-runs --jq '.check_runs[].name'`。
3. 跑 `apply`（不帶 `--confirm`）把將要送出的設定給使用者看，**取得同意後**才加 `--confirm`。
4. 套用後再跑一次 `audit` 對帳。
5. 開了保護後，`enforce_admins` 讓維護者也只能走 PR：若該 repo 原本直接 commit 到 main，它的 CONTRIBUTING
   與 agent 規則要一起改。

### 修正 `[commit]` 的差異

- CODEOWNERS：`.github/CODEOWNERS` 放基準的那一行。
- CONTRIBUTING：repo 自有的 CONTRIBUTING 只寫建置、測試與 repo 特有的慣例，共用的協作規則連到
  `https://github.com/<org>/.github/blob/main/CONTRIBUTING.md`，不複寫。沒有自有 CONTRIBUTING 的 repo 由 GitHub 顯示 org 版。
- 依該 repo 的工作流程提交（通常是分支 + PR）。

### org 新增 repo

1. 在 `<org>/.github/repo-baseline.json` 的 `repos` 登記它與必要檢查（第一次 CI 跑完後才知道確切名稱）。
2. 加 CODEOWNERS；CONTRIBUTING 視需要加（連到共用指南）。
3. 確認 CI 的只改文件跳過是在 job 內（見上方「套用」第 1 點）。
4. `apply` → `audit` 對帳。

## 常見錯誤

- ❌ 必要檢查所在的 workflow 用 `paths-ignore` 跳過文件變更 → ✅ 在 job 內偵測，job 一定要啟動
- ❌ 必要檢查寫 `build`，但 matrix 實際回報 `build (ubuntu-latest)` → ✅ 以 check run 名稱為準
- ❌ 稽核有差異就改基準檔讓它通過 → ✅ 先判讀是該修還是例外；改共用值要使用者決定
- ❌ 一次對所有 repo `apply --confirm` → ✅ 逐 repo 給使用者看過、同意後才套用
- ❌ 在 repo 的 CONTRIBUTING 複寫協作規則 → ✅ 連到 org 共用指南
