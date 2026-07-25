---
name: plan-handoff
description: 把已定案的 plan 交接給新 session 實作 —— 整理出可直接複製的交接 prompt（plan 路徑、「設計已定案」封印、出貨與順序約束、未驗證項目、環境前置、git 狀態）。當使用者要「開新 session 實作這個 plan」、「開始實作了」、「把這個 plan 交出去做」、「另開 session 做這個」時使用。
---

# 交接 plan 給實作 session

擬定 plan 的 session 累積了大量討論脈絡，實作用不到；而實作要讀大量原始碼、跑測試，
適合乾淨的 context。因此「plan 定案 → 換 session 實作」是常見且正確的切換點。

本 skill 規範**交接時要輸出什麼**，以及**為何不代為開 session**。

---

## 做法：輸出可複製的 prompt，由使用者自己開 session

交接時，整理一段自足的 prompt，放進**單一 fenced code block**（純文字，不加
`bash` 之類語言標記——那會讓部分介面顯示成可執行指令）。使用者複製後自行開新 session 貼上。

**不要用工具代為開 session**，即使環境提供這類工具：

- **多半會建立 git worktree**。worktree 有獨立的工作目錄，**主工作樹尚未 commit 的
  plan 在裡面不存在**（新檔案）或**是舊版**（已修改的檔案）——新 session 會照著
  一份它讀不到的 plan 動工，且不會報錯。
- **分支策略是使用者的決定**。有些人習慣直接在 main 上做，自動建分支會與其工作流衝突。
- **可攜性**：這類工具通常是特定介面專屬，寫進 skill 會讓其他環境無法照做。

輸出 prompt 讓使用者自己開，沒有以上任何問題。

---

## 交接前檢查（兩項，缺一不可）

### 1. plan 的 git 狀態

新 session 可能在不同的工作目錄或 checkout 狀態下啟動。交接前確認 plan 檔案的狀態，
**並在 prompt 中明說**：

- 已 commit → prompt 直接寫 plan 路徑即可
- 未 commit（新增或已修改）→ **先問使用者要不要 commit**。若不 commit，
  prompt 必須明寫「plan 檔案尚未 commit，位於主工作樹」，讓新 session 知道 git 起點

### 2. plan 是否真的定案

若 plan 仍有「待定」「未決」段落，交接會讓新 session 在實作中途卡住或自行決定。
先確認這些項目已收斂，或在 prompt 中明確標示哪些仍待使用者拍板、遇到時應停下詢問。

---

## 交接 prompt 的必備內容

| 區塊 | 為何必要 |
|------|---------|
| **plan 完整路徑 + 「先完整讀過」** | 新 session 沒有任何討論脈絡 |
| **「設計已定案，不需重新討論」** | 否則新 session 會把已否決的方案重議一遍，浪費大量往返 |
| **出貨 / 順序約束** | 階段能否分開發布、是否有前置 plan——最容易在實作中途才踩到 |
| **未驗證項目清單** | 區分「plan 已證實的」與「仍需自行確認的」，避免新 session 誤信推測為事實 |
| **環境前置** | 容器 / 服務是否已啟動、需要哪些外部相依 |
| **git 狀態** | plan 與相關檔案是否已 commit、目前在哪個分支 |

不需要塞進 prompt 的：plan 內文已寫的設計理由、被否決方案的完整論證、討論過程。
**那些是 plan 文件的職責**——若 prompt 需要複述才說得清，代表 plan 本身寫得不夠自足，
應該回頭補 plan 而不是加長 prompt。

---

## 範本

```
實作 <plan 的完整路徑>。

先完整讀過該 plan。設計已定案，不需重新討論其中的決策或替代方案
（plan 已記錄被否決的方案及理由）。

<出貨 / 順序約束——例如：階段 1 與階段 2 必須一起發布，原因見 plan §X>

核心變更（詳見 plan §X）：
- <逐項列出，讓新 session 一眼看到規模>

<若為 breaking change：說明破壞面與 commit / CHANGELOG 的標記要求>

plan 尚未驗證、需要你自行確認的項目：
1. <...>
2. <...>

環境：<容器 / 服務狀態、前置條件>
git：<plan 與相關檔案的 commit 狀態、目前分支>
```

---

## 交接後

- **本 session 停止改動該 plan 涉及的檔案**，避免與實作 session 衝突。
- plan 的狀態列改為 `🚧 進行中`（格式見 `plan-write`）；多階段 plan 則更新對應階段列。
- 若交接後才發現 plan 有誤或遺漏，**改 plan 檔案並告知使用者轉達**，
  不要在本 session 直接改實作涉及的原始碼。

---

## 常見錯誤

- ❌ 用工具代為開 session → ✅ 輸出可複製的 prompt，由使用者自己開
- ❌ prompt 只寫「實作 docs/plans/plan-xxx.md」→ ✅ 補齊上表六個區塊
- ❌ plan 未 commit 就交接、且未在 prompt 中說明 → ✅ 先問要不要 commit，
  不 commit 也要明寫狀態
- ❌ 把 plan 的設計理由複述進 prompt → ✅ 那是 plan 的職責；prompt 只給指向與約束
- ❌ 交接後本 session 繼續改同一批檔案 → ✅ 交接即交棒
- ❌ 用 ` ```bash ` 包裝交接 prompt → ✅ 用純文字 fenced block（避免被當成可執行指令）
