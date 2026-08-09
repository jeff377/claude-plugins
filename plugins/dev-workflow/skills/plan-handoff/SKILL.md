---
name: plan-handoff
description: 把已定案的 plan 交接給新 session 接手下一步。**它規範的是流程不只是格式**：交接的第一個動作是把 plan commit（步驟，不是詢問），接著優先用 spawn task、否則輸出可複製 prompt，且 prompt 必須明寫工作樹與分支期望（worktree 或 local only），否則預設開的 worktree 會讀不到未 commit 的 plan。prompt 六個必備區塊：plan 路徑與 commit hash、「設計已定案」封印、出貨與順序約束、未驗證項目、環境前置、git 狀態。**不限程式碼實作**：撰寫文章、重構、遷移、資料處理、文件改版都適用；**plan 也不限放在 `docs/plans/`**。當使用者要「開新 session 實作／撰寫這個 plan」、「開新 session 寫 X」、「開始實作了」、「把這個 plan 交出去做」、「另開 session 做這個」、「交接給新 session」、「換 session 接手」時使用，**不論下一步是寫程式還是寫文章**。
---

# 交接 plan 給接手的 session

擬定 plan 的 session 累積了大量討論脈絡，接手的人用不到；而動工那一端要讀大量原始碼、
既有產出或參考資料，還要跑測試與查證，適合乾淨的 context。
因此「plan 定案 → 換 session 動工」是常見且正確的切換點。

**接手的不一定是寫程式。** 撰寫系列文章、批次遷移、資料清理、文件改版都適用；
plan 也不限放在 `docs/plans/`。判別法只有一個：**下一步要不要換一個乾淨的 context 去做。**

本 skill 規範**交接時要做哪些動作**、**要輸出什麼**，以及**用哪種方式把它交出去**。
其中「先把 plan commit」與「prompt 必須明寫工作樹期望」是硬性步驟，
不是可以憑記憶重現的格式範本。

---

## 交接方式：優先用 spawn task，否則輸出可複製的 prompt

不論走哪條路，**prompt 的內容要求完全相同**（見下方「必備內容」與「範本」）。
差別只在遞送方式。

### 首選：`spawn_task`（CCD app 環境）

環境有 `spawn_task` 這類工具時用它——把交接 prompt 當作 task 的 prompt 送出，
使用者點一下就會在**新的 session** 裡開始。

- **仍由使用者點擊才啟動**，控制權沒有交出去——只是把「複製貼上」換成「點一下」。
- **啟動時可選 worktree 或 local only，預設是建 worktree**（實測 2026-08-01：未選
  local only 送出的 task，跑在 `.claude/worktrees/` 底下、掛在自動產生的
  `claude/*` 分支上）。

> **因此交接 prompt 必須明寫工作樹與分支的期望**，例如「請在主工作樹的 main 上進行」
> 或「這個任務適合開 worktree」。沒寫的話，使用者可能按預設開了 worktree，而 prompt 裡
> 「依 repo 慣例直接提交 main」之類的指示就會與實際環境對不上，得中途導正。
>
> 走 worktree 時還要注意：**主工作樹尚未 commit 的 plan 在 worktree 裡看不到**
> （新檔案不存在、已修改的是舊版），新 session 會照著一份它讀不到的 plan 動工且不報錯。
> 這正是下方「交接前檢查」堅持先 commit 的理由。

> 別把它當成背景執行的 agent：它是一個獨立 session，有自己的對話與 context，
> 不會把結果回報進本 session。

### 備援：輸出可複製的 prompt

沒有這類工具時（純 CLI、其他介面），把 prompt 放進**單一 fenced code block**
（純文字，不加 `bash` 之類語言標記——那會讓部分介面顯示成可執行指令），
由使用者自行開新 session 貼上。

**`spawn_task` 不可攜**，所以 skill 不能只寫這一條；備援路徑必須保留。

### 走 local only / 手動開 session 時：共用工作樹

選 local only 的 spawn task、或使用者手動開一個不加 `--worktree` 的 session，都會與本
session **共用同一棵工作樹**。兩邊同時改同一批檔案會互相覆蓋，所以下方「交接後」的
**交接即交棒**不是建議而是硬要求。（走 worktree 則無此問題，但換成上面那個
「讀不到未 commit 的 plan」的風險。）

---

## 交接前檢查（兩項，缺一不可）

### 1. 把 plan 簽入（commit）

**交接的第一個動作就是把 plan commit 掉**，不是「詢問要不要 commit」。
這是交接流程的一個步驟，不是一個選項——交接本身就是使用者對這個動作的授權。

理由：新 session 可能開在 worktree（**讀不到主工作樹的未 commit 內容**，會照著一份
它打不開的 plan 動工且不報錯），也可能共用主工作樹（讀得到，但 plan 會與實作改動
混在同一批 diff，之後難以分辨哪些是設計、哪些是實作）。兩種情境下先 commit 都較好。

流程：

1. `git status` 確認 plan 檔案狀態
2. 未 commit（新增或已修改）→ **直接 commit**，訊息比照 repo 慣例
   （多數 repo 為 `docs(plans): <plan 主題>`，摘要寫階段數與是否為破壞性變更）
3. 已 commit → 取 commit hash
4. prompt 的 git 區塊寫上 **plan 路徑 + commit hash + 目前分支**

**唯一的例外**：使用者明確表示這次不要 commit。此時 prompt 必須明寫
「plan 尚未 commit，位於主工作樹」，且該任務**不可開 worktree**（只能選 local only）。

> 順帶檢查 plan 以外的相關檔案是否也該一併簽入——若實作 session 需要參照的
> 樣板 / fixture / 設定檔還躺在工作區，worktree 裡同樣看不到。

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

- ❌ 因為「可能建 worktree」就整個不用 spawn task → ✅ 有這類工具就優先用，純 CLI 才退回可複製 prompt
- ❌ prompt 沒交代工作樹 / 分支期望 → ✅ 明寫「在主工作樹的 main 上進行」或「適合開 worktree」，否則預設會開 worktree、與 prompt 裡的 git 指示打架
- ❌ prompt 只寫「實作 docs/plans/plan-xxx.md」→ ✅ 補齊上表六個區塊
- ❌ 停下來問「要不要先 commit plan？」→ ✅ **直接 commit**，那是交接流程的步驟不是選項；
  只有使用者明確說不要時才走未 commit 路徑（並在 prompt 明寫狀態、禁用 worktree）
- ❌ prompt 的 git 區塊只寫分支、沒寫 plan 的 commit hash → ✅ 兩者都寫
- ❌ 把 plan 的設計理由複述進 prompt → ✅ 那是 plan 的職責；prompt 只給指向與約束
- ❌ 交接後本 session 繼續改同一批檔案 → ✅ 交接即交棒（兩邊共用同一棵工作樹，同時改會互相覆蓋）
- ❌ 用 ` ```bash ` 包裝交接 prompt → ✅ 用純文字 fenced block（避免被當成可執行指令）
