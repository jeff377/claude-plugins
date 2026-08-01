---
name: plan-handoff
description: 把已定案的 plan 交接給新 session 實作 —— 整理出可直接複製的交接 prompt（plan 路徑、「設計已定案」封印、出貨與順序約束、未驗證項目、環境前置、git 狀態）。當使用者要「開新 session 實作這個 plan」、「開始實作了」、「把這個 plan 交出去做」、「另開 session 做這個」時使用。
---

# 交接 plan 給實作 session

擬定 plan 的 session 累積了大量討論脈絡，實作用不到；而實作要讀大量原始碼、跑測試，
適合乾淨的 context。因此「plan 定案 → 換 session 實作」是常見且正確的切換點。

本 skill 規範**交接時要輸出什麼**，以及**用哪種方式把它交出去**。

---

## 交接方式：優先用 spawn task，否則輸出可複製的 prompt

不論走哪條路，**prompt 的內容要求完全相同**（見下方「必備內容」與「範本」）。
差別只在遞送方式。

### 首選：`spawn_task`（CCD app 環境）

環境有 `spawn_task` 這類工具時用它——把交接 prompt 當作 task 的 prompt 送出，
使用者點一下就會在**新的 session** 裡開始。實測（2026-08-01）：

- **在主工作樹、當前分支上跑**，不建 git worktree。所以主工作樹裡**尚未 commit 的
  plan 新 session 讀得到**，這一點與早期的假設相反。
- **仍由使用者點擊才啟動**，控制權沒有交出去——只是把「複製貼上」換成「點一下」。

> 別把它當成背景執行的 agent：它是一個獨立 session，有自己的對話與 context，
> 不會把結果回報進本 session。

### 備援：輸出可複製的 prompt

沒有這類工具時（純 CLI、其他介面），把 prompt 放進**單一 fenced code block**
（純文字，不加 `bash` 之類語言標記——那會讓部分介面顯示成可執行指令），
由使用者自行開新 session 貼上。

**`spawn_task` 不可攜**，所以 skill 不能只寫這一條；備援路徑必須保留。

### 兩條路都要守的一件事：共用工作樹

新 session 與本 session **共用同一棵工作樹**（spawn task 如此；使用者手動開一個
不加 `--worktree` 的 session 也是如此）。兩邊同時改同一批檔案會互相覆蓋，
所以下方「交接後」的**交接即交棒**不是建議而是硬要求。

---

## 交接前檢查（兩項，缺一不可）

### 1. plan 的 git 狀態

新 session 讀得到主工作樹的未 commit 內容（見上方「共用工作樹」），所以未 commit
**不會**讓 plan 讀不到。但仍要確認狀態並在 prompt 中明說 git 起點：

- 已 commit → prompt 直接寫 plan 路徑與 commit hash
- 未 commit → prompt 明寫「plan 尚未 commit」。**建議先 commit**，理由不是讀不讀得到，
  而是實作 session 會在同一棵樹上動工，未 commit 的 plan 容易與實作改動混在同一批
  diff 裡，事後分不清哪些是決策、哪些是實作

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

- ❌ 以「會建 worktree、讀不到未 commit 的 plan」為由拒用 spawn task → ✅ 實測不建 worktree、在主工作樹跑；有這類工具就優先用，純 CLI 才退回可複製 prompt
- ❌ prompt 只寫「實作 docs/plans/plan-xxx.md」→ ✅ 補齊上表六個區塊
- ❌ plan 未 commit 就交接、且未在 prompt 中說明 → ✅ 先問要不要 commit，
  不 commit 也要明寫狀態
- ❌ 把 plan 的設計理由複述進 prompt → ✅ 那是 plan 的職責；prompt 只給指向與約束
- ❌ 交接後本 session 繼續改同一批檔案 → ✅ 交接即交棒（兩邊共用同一棵工作樹，同時改會互相覆蓋）
- ❌ 用 ` ```bash ` 包裝交接 prompt → ✅ 用純文字 fenced block（避免被當成可執行指令）
