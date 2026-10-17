---
name: session-handoff
description: 把已定案的工作交接給新 session 接手下一步。補的是內建 `start_session` 管不到的部分：交接的第一個動作是把交接文件 commit（步驟，不是詢問；交接文件在 gitignored 目錄時例外：不 commit、絕不 git add -f、只能共用工作樹），以及 brief 的必備區塊——交接文件路徑與 commit hash、「設計已定案」封印、逐條列出的未決事項、出貨與順序約束、未驗證項目、環境前置、git 狀態。**不限程式碼實作**：撰寫文章、重構、遷移、資料處理、文件改版都適用；**交接文件不限是 `docs/plans/` 的 plan**，可以是規格、規範文件組、或連載系列的大綱＋逐篇筆記＋寫作規則。當使用者要「開新 session 實作／撰寫這個 plan」、「開新 session 寫 X」、「接下來開新 session 寫下一篇」、「接著寫」、「開始實作了」、「把這個交出去做」、「另開 session 做這個」、「交接給新 session」、「換 session 接手」時使用，**不論下一步是寫程式還是寫文章、也不論有沒有一份叫 plan 的檔案**。
---

# 交接工作給接手的 session

擬定的那個 session 累積了大量討論脈絡，接手的人用不到；動工那一端要讀大量原始碼、
既有產出或參考資料，適合乾淨的 context。「設計定案 → 換 session 動工」是常見且正確的切換點。

**接手的不一定是寫程式，也不一定有一份叫 plan 的檔案。** 本 skill 統稱新 session 必須先讀的東西為
**交接文件**：計畫目錄下的 plan（見 `plan-write`）、別處的規格、**一組文件**（例如大綱 + 逐篇筆記 +
寫作規則），甚至沒有文件、只有口頭定案的需求（此時 brief 本身就是交接文件，必備內容一項都不能少）。

開 session、選工作樹、把結果送回來，都由內建的 `start_session` 處理。本 skill 只規範它管不到的兩件事：
**交接前要做什麼**，以及 **brief 裡必須寫什麼**。

---

## 遞送

- **CCD app**：用 `start_session`。使用者已明說要交出去，`initiation` 用 `"user_asked"`；
  `context` 用 `"fresh"`（交接點的對話通常很長，`fork` 會把整段討論帶過去，等於沒換 context）。
- **`use_worktree` 的選擇**：
  - 交接文件在 **gitignored 目錄**、**另一個 repo**、或**使用者要求不 commit** → 只能 `false`（共用工作樹），
    worktree 裡讀不到它，新 session 會照著一份讀不到的文件動工而不報錯
  - 其餘依 repo 慣例：直接提交 main 的 repo 用 `false`；走分支 + PR 的用 `true`
  - **brief 裡的提交方式要與這個選擇一致**（「直接提交 main」配 `false`），不要讓兩者打架
- **純 CLI / 沒有 `start_session`**：把 brief 放進**單一純文字 fenced code block**（不加 `bash` 標記），
  由使用者自行開 session 貼上，並在 brief 開頭寫明該不該開 worktree。

---

## 交接前檢查（兩項，缺一不可）

### 1. 把交接文件簽入（commit）

**交接的第一個動作就是 commit 交接文件**，不是「詢問要不要 commit」——交接本身就是授權。
worktree 讀不到未 commit 的內容；共用工作樹則會讓設計與動工的改動混在同一批 diff。

1. 先 `git check-ignore -v <路徑>` 判斷是否在 gitignored 目錄（有輸出就是，走例外 1），
   再看 `git status`。**不能只看 `git status`**——被忽略的檔案不會列出，看起來跟「已 commit」一樣。
   **交接文件是一組時，每一份都要確認**
2. 未 commit → **直接 commit**，訊息比照 repo 慣例（plan 類多為 `docs(plans): <主題>`）
3. brief 的 git 區塊寫上 **文件路徑 + commit hash + 目前分支**

**例外只有兩個**：

1. **交接文件位於 gitignored 目錄**（例如 `local/plans/`）：**不 commit，也絕不 `git add -f`**。
   gitignore 是該 repo 的決定，「交接本身就是授權」不涵蓋把不公開的文件推進版控。
   brief 寫明「交接文件位於 gitignored 目錄 <路徑>，不入版控」，`use_worktree: false`。
2. **使用者明確表示這次不要 commit**：brief 寫明「交接文件尚未 commit，位於主工作樹」，`use_worktree: false`。

> 新 session 需要的樣板 / fixture / 設定檔 / 既有產出若還躺在工作區，一併簽入。
> 交接文件在另一個 repo 時，commit 的是那個 repo，brief 的 git 區塊**兩個 repo 都寫**。

### 2. 是否真的定案

仍有「待定」段落，新 session 會在中途卡住或自行決定。先收斂；收斂不了就
**逐條列進 brief 並標「遇到時停下詢問，不要自行處理」**——光說「有些事還沒定」沒有用。

---

## brief 的必備內容

| 區塊 | 為何必要 |
|------|---------|
| **交接文件完整路徑 + 「先完整讀過」** | 新 session 沒有討論脈絡。一組文件就逐份列出並說明各放什麼 |
| **「設計已定案，不需重新討論」** | 否則已否決的方案會被重議一遍 |
| **出貨 / 順序約束** | 階段能否分開發布、有無前置工作——最容易中途才踩到 |
| **未決事項（逐條）** | 見上方「是否真的定案」 |
| **未驗證項目清單** | 區分已證實與推測，避免新 session 誤信推測為事實 |
| **環境前置** | 容器 / 服務是否已啟動、需要哪些外部相依 |
| **git 狀態** | commit hash、分支、提交方式；**多個 repo 就逐個寫** |

不需要塞進 brief 的：設計理由、被否決方案的論證、討論過程。**那些是文件的職責**——
需要複述才說得清，代表文件不夠自足，該回頭補文件。

**共用工作樹時，工作區若有別人的在途改動**：逐一列出路徑並要求「不要碰、不要 commit」，
指示用 `git commit -- <明確路徑>`，不要 `git add -A`。

**結果要送給開 session 以外的人時**（例如 B 正在彙整提問、等這份結果），才需要寫回報對象：
B 的 `local_…` session id，並註明「找不到就回報使用者，不要改送其他 session」。
送回本 session 是內建行為，不必寫。

---

## 範本

```
<一句話說明要做什麼——例如：實作 <文件路徑>／撰寫 <系列> 的第 N 篇>

先完整讀過：
- <文件 1 路徑> — <裡面放什麼>

設計已定案，不需重新討論其中的決策或替代方案（文件已記錄被否決的方案及理由）。

<出貨 / 順序約束>

核心內容（詳見 §X）：
- <逐項列出，讓新 session 一眼看到規模>

<若為 breaking change：破壞面與 commit / CHANGELOG 的標記要求>

尚未定案、遇到時請停下詢問，不要自行處理：
1. <...>

尚未驗證、需要你自行確認的項目：
1. <...>

環境：<容器 / 服務狀態、前置條件>
git：<commit hash、分支、提交方式（直接提交 main / 開 PR）；多個 repo 逐個寫；
      共用工作樹時別人的在途改動逐一列出並要求不要碰>
```

---

## 交接後

- **交接即交棒**：本 session 停止改動該工作涉及的檔案（共用工作樹時同時改會互相覆蓋）。
- plan 類文件的狀態列改為 `🚧 進行中`（格式見 `plan-write`）；多階段則更新對應階段列。
- 收到接手方的回報時，那是**它的說法不是證明**——看過 diff 或產出再告訴使用者完成了。
- 發現它做錯或卡住：**改交接文件 + 用 `SendMessage` 告知它**，不要自己動手改它正在動的檔案。

---

## 常見錯誤

- ❌ 因為「這次沒有 plan 檔案」就不叫這個 skill → ✅ 交接文件可以只有 brief 本身
- ❌ 停下來問「要不要先 commit？」→ ✅ **直接 commit**；只有 gitignored 或使用者明說不要時例外
- ❌ 交接文件在 gitignored 目錄，`git status` 沒列出就當已 commit，或用 `git add -f` 硬加 →
  ✅ `git check-ignore -v` 確認後不 commit，`use_worktree: false`
- ❌ 交接文件讀不到的情況下用 `use_worktree: true` → ✅ gitignored / 另一個 repo / 未 commit 一律 `false`
- ❌ 用 `context: "fork"` 交接 → ✅ `fresh`，換 context 正是交接的目的
- ❌ brief 只寫「實作 docs/plans/plan-xxx.md」→ ✅ 補齊必備區塊
- ❌ git 區塊只寫分支、沒寫 commit hash → ✅ 兩者都寫（gitignored 以「不入版控」代替 hash）
- ❌ 把設計理由複述進 brief → ✅ 那是文件的職責
- ❌ 交接後本 session 繼續改同一批檔案 → ✅ 交接即交棒
- ❌ 用 ` ```bash ` 包裝可複製的 brief → ✅ 純文字 fenced block
