---
name: config-audit
description: 定期健檢 Claude Code 設定檔語料（CLAUDE.md、rules/、skills/、commands/、hooks、plugin、memory）—— 量測常駐 context 成本、抓失效引用與過期量化斷言、偵測跨檔衝突、判定「常駐 vs 按需」錯置、檢查 skill description 觸發重疊與 plugin 版本漂移。核心判準是「這段會不會改變下一個 session 的行為」，不是「長不長」。當使用者要「整理 CLAUDE.md」、「精簡 rules」、「設定檔健檢」、「config audit」、「skill 太多太亂」、「context 太肥」、「規則互相衝突」、「定期整理 .claude」之類需求時使用。**產出分級報告供逐項確認，不自動改寫規則。**
---

# Claude Code 設定檔健檢

設定檔語料（CLAUDE.md / rules / skills / commands / memory）是**指揮 agent 的憲法**。
它會隨程式碼演進而漂移，但沒有任何機制會告訴你它漂了 —— 編譯器不看它、測試不跑它、
CI 不驗它。這個 skill 提供可重複的體檢方法。

**產出是分級報告，不自動改寫。** 靜默改動規則的風險高於省下的時間：一條被誤刪的規則
不會報錯，只會讓未來每個 session 悄悄做錯事，而你要幾週後才會發現。

---

## 第一原則：判準是「會不會改變行為」，不是「長不長」

**這是本 skill 最重要的一節。** 「精簡」若被機械執行，第一個被砍的往往是最有價值的部分 ——
那些「我們曾經這樣錯過」的踩雷紀錄。它們看起來像贅述，實際上是唯一能阻止重蹈覆轍的東西。

對每一段內容問：**這段在下一個 session 會不會改變 agent 的行為？**

| 類型 | 例 | 處置 |
|------|----|------|
| **指令** | 「一律用 `StringComparison.Ordinal`」 | ✅ 留常駐 |
| **判準** | 「這個字串是拿來比對身分還是呈現給人？」 | ✅ 留常駐 —— 判準比指令更值錢，它處理指令沒列舉到的情境 |
| **反例警示** | 「曾嘗試全域改 `Infer`，結果炸掉 seed」 | ✅ 留常駐，但壓成一句 + 指向按需文件存細節 |
| **推導過程 / 實測數據 / 歷史敘事** | 「37 → 185 筆失敗的對照實驗」 | ⚠️ 搬按需區，常駐只留結論 |
| **已被推翻或已失效的內容** | 指向已刪除檔案、已退役的閘門 | ❌ 刪 |

### 不得砍除（即使冗長）

- **「本節先前寫的是 X，已於 YYYY-MM-DD 推翻」** 這類自我更正 —— 它防止下一個 agent
  從舊資料重新推導出同一個錯誤結論。
- **「留著這段是因為它示範了一個反覆出現的錯法」** 這類明示保留理由的段落 —— 作者已經
  預期到有人會想刪它。
- **誤報清單與判別法**（「這個檢查會有 N 種已知誤報，逐筆判讀」）—— 砍掉會讓後續每次
  執行都重新踩一次。

> 真的要精簡時，**先問能不能搬，再問能不能刪**。搬到按需文件的內容成本歸零但知識不失；
> 刪掉的知識找不回來。

---

## 語料範圍

先確認這個 repo 實際有哪些層，不存在的層直接略過、不要臆造。

| 層 | 位置 | 載入時機 | 成本 |
|----|------|---------|------|
| 全域指引 | `~/.claude/CLAUDE.md` + `~/.claude/rules/`（經 `@import`） | **每 session 常駐** | 高 |
| 專案指引 | `<repo>/.claude/CLAUDE.md` + `<repo>/.claude/rules/` | **每 session 常駐** | 高 |
| Skill 描述 | 所有 skill 的 `description` frontmatter | **每 session 常駐** | 中（只有描述） |
| Skill 本文 | `SKILL.md` 內文、`references/` | 呼叫時才載 | 低 |
| Commands | `.claude/commands/*.md` | 呼叫時才載 | 低 |
| 按需脈絡 | 專案自訂（如 `docs/repo-ops/gotchas/`） | 明確要求時才讀 | 低 |
| 機制 | `settings.json`、`hooks/` | 不進 context，但會執行 | — |
| 記憶 | `~/.claude/projects/<slug>/memory/` | `MEMORY.md` 常駐、個別檔按需 | 低 |

**常駐區是唯一有固定成本的地方，優化火力集中在此。** 其餘只在被叫用時付費。

---

## 執行流程

### 步驟 0 — 量測基線

沒有數字就沒有取捨。先量常駐總量與各檔佔比：

```bash
FILES=$(ls ~/.claude/CLAUDE.md ~/.claude/rules/*.md .claude/CLAUDE.md .claude/rules/*.md 2>/dev/null)
echo "常駐總量：$(cat $FILES | wc -c) 字元（約 $(( $(cat $FILES | wc -c) / 3500 ))k tokens）"
for f in $FILES; do printf "%7d  %s\n" $(wc -c < "$f") "$f"; done | sort -rn
```

換算粗估：中英混排約 **3,500 字元 ≈ 1k tokens**。

把數字與上次健檢比對（若報告有存檔），**趨勢比絕對值重要**。單看 100KB 不知道好壞，
但「三個月從 60KB 長到 125KB」就是明確訊號。

### 步驟 1 — 失效引用（機械，最高投報）

設定檔會引用檔案路徑、型別名、指令。程式碼改名時它們不會跟著改。

```bash
FENCE=$(printf '%c%c%c' 96 96 96)
for f in .claude/CLAUDE.md .claude/rules/*.md ~/.claude/CLAUDE.md ~/.claude/rules/*.md; do
  [ -e "$f" ] || continue
  awk -v F="$FENCE" 'index($0,F)==1{s=!s; next} !s' "$f" \
  | perl -nE 'while(/(?<![\w\/.-])((?:src|tests|docs|tools|apps|samples|lib|packages|\.claude|\.github)\/[\w.\/-]*?\.(?:csproj|slnx|props|targets|axaml|razor|json|yml|yaml|md|cs|ts|js|py|xml|sh))(?![\w])/g){say $1}' \
  | sort -u | while read -r p; do [ -e "$p" ] || echo "  ${f/#$HOME/~} → $p"; done
done
```

設計要點（**別自己重寫成更簡單的版本，這三個濾網都是必要的**）：

- `awk` 剝掉 code fence —— 範例程式碼裡的路徑是示意，不是引用。
- perl 的 `(?![\w])` 後瞻 —— 否則 `Bee.Definition.csproj` 會被切成 `Bee.Definition.cs` 而誤報。
- 只抓含 `/` 的路徑 —— 裸檔名（`code-style.md`）可能指向另一層的檔案，判不準。

**剩下的仍需逐筆判讀**：markdown 引言區（`>`）或 `<!-- ❌ 禁止 -->` 註解內的示意路徑
是合法誤報。實務上噪音很低（個位數），逐筆看得完。

再檢 `@import` 是否都解得到：

```bash
grep -hoE '^@[A-Za-z0-9~./_-]+' .claude/CLAUDE.md ~/.claude/CLAUDE.md 2>/dev/null | sed 's/^@//' \
| while read -r p; do q="${p/#\~/$HOME}"; [ -e "$q" ] || [ -e ".claude/$p" ] || echo "MISSING import: $p"; done
```

### 步驟 2 — 過期的量化斷言（機械偵測 + 實際重跑）

**寫得越具體的宣稱，過期得越快。** 「目前有 28 處 `[Collection]`」「兩者皆零使用」
「有 6 個直接下游」—— 這些在寫下當天是對的，半年後多半不是。

好消息是它們**可以重跑驗證**。先撈出來：

```bash
grep -rnoE '[0-9]+ (處|筆|個|條)[^。\n]{0,25}|零(使用|caller|孤兒|例外)|(20[0-9]{2}-[0-9]{2}-[0-9]{2})' \
  .claude/rules/ .claude/CLAUDE.md ~/.claude/rules/ 2>/dev/null
```

然後**實際重跑**每個宣稱背後的量測（多半是一行 grep），比對數字。

處置：

| 情況 | 處置 |
|------|------|
| 數字仍正確 | 不動。可選擇性更新日期戳 |
| 數字已變、結論不變 | 更新數字，或**改寫成不帶數字的定性描述**（更耐久） |
| 數字已變且結論翻轉 | **P0** —— 這條規則現在正在誤導 agent |
| 量測方法已不存在（檔案沒了、指令沒了） | 該段落已無錨點，刪或改寫 |

> 帶日期戳的自我更正（「已於 X 推翻」）**不適用本步驟** —— 它記的是歷史事件，不是現況宣稱。
> 判別法：**這句在講「現在是什麼」還是「當時發生了什麼」？** 前者才要重驗。

### 步驟 3 — 衝突與重複

同一主題散在多檔時，結論可能已經分岔。先找出跨檔共同主題：

```bash
for f in .claude/rules/*.md ~/.claude/rules/*.md; do
  echo "### ${f/#$HOME/~}"; grep -E '^#{2,3} ' "$f" | sed 's/^/  /'
done
```

比對重疊的節標題，逐組讀出結論是否一致。三種樣態：

| 樣態 | 處置 |
|------|------|
| **直接矛盾** — A 說必須、B 說禁止 | **P0**。定出哪個為真，另一邊刪除或改為指向前者 |
| **同義重述** — 兩處講同一件事、都對 | 留最完整的一份，另一處改為單行交叉引用 |
| **刻意分工** — 兩檔各管一面，文件已自述邊界 | 不動。**確認那句邊界宣告本身還成立** |

也要檢查**檔案內部**的矛盾：規則常在新增段落時與舊段落打架。特別留意帶「例外」「但是」
「唯一」的句子 —— 出現第二個「唯一」就是訊號。

### 步驟 4 — 常駐 vs 按需錯置

**這一步通常貢獻最大的減量，且不損失任何知識。**

逐檔掃常駐區，用第一原則的四分類表判每個段落。凡歸類為「推導過程 / 實測數據 /
歷史敘事」者，都是搬家候選 —— 搬到按需區，常駐只留一句結論 + 指路。

搬去哪：

1. 專案若已有按需脈絡目錄（如 `docs/repo-ops/gotchas/`），**沿用既有結構**，不要另立新的。
2. 沒有的話，**先提議建立**（在報告中說明），不要自作主張建目錄。
3. 內容若只服務單一工作流程（「怎麼新增一個 X」），更好的家是 **skill** —— 呼叫時才載。

判別捷徑：**這段是不是只有在做某類特定工作時才需要？** 是 → 按需區。
每個 session 都該知道 → 常駐。

### 步驟 5 — Skill / Command / Plugin 健檢

```bash
for d in .claude/skills/*/ ~/.claude/skills/*/; do
  [ -e "$d/SKILL.md" ] || { echo "缺 SKILL.md: $d"; continue; }
  n=$(grep -m1 '^name:' "$d/SKILL.md" | sed 's/^name: *//')
  [ "$n" = "$(basename $d)" ] || echo "name 與目錄名不符: $d (name=$n)"
  printf "%5d 字描述  %s\n" "$(grep -m1 '^description:' "$d/SKILL.md" | wc -c)" "$(basename $d)"
done | sort -rn
```

檢查項：

- **frontmatter 完整**：`name` 存在且等於目錄名；`description` 存在。
- **description 是常駐成本** —— 它每個 session 都載入。過長的描述要壓縮，但**不要為了短而砍掉觸發詞**：
  description 的工作是讓 skill 在對的時候被叫用，觸發詞漏了等於 skill 等於不存在。
- **觸發重疊**：兩個 skill 的觸發情境若大幅重疊，agent 會挑錯。合併，或在各自 description
  末尾明確劃界（「**不負責 X（見 other-skill）**」）。
- **SKILL.md 內引用的檔案存在**：套用步驟 1 的同一個檢查，範圍換成 skill 目錄。
- **零使用的 skill**：長期沒被叫用的，通常是 description 觸發不到，不是功能沒用 ——
  **先修描述，不要急著刪**。

### 步驟 5b — Plugin 版本漂移（有裝 plugin 才做）

**同一個 plugin 會同時存在於四個位置，各自獨立漂移。** 只看其中一兩個必定誤判：

| 位置 | 怎麼看 | 誰更新它 |
|------|--------|---------|
| 開發用 clone | `git -C <plugin-repo> log --oneline -1` 與 `git status` | 你手動 commit / push |
| marketplace clone | `git -C ~/.claude/plugins/marketplaces/<mp> log --oneline -1` | `claude plugin update` 時拉取 |
| 已安裝 cache | `ls ~/.claude/plugins/cache/<mp>/<plugin>/` | `claude plugin update` 時解出新版目錄 |
| **安裝註冊表** | `~/.claude/plugins/installed_plugins.json` | 指向 cache 中的**哪一版**才生效 |

```bash
MP=<marketplace-name>; PLUGIN=<plugin-name>; REPO=<plugin-repo-path>
echo "開發 clone:"; git -C "$REPO" log --oneline -1; git -C "$REPO" status --short
echo "marketplace:"; git -C ~/.claude/plugins/marketplaces/$MP log --oneline -1
echo "cache 目錄:"; ls -1 ~/.claude/plugins/cache/$MP/$PLUGIN/
echo "註冊表（實際生效）:"
python3 -c "
import json,os
d=json.load(open(os.path.expanduser('~/.claude/plugins/installed_plugins.json')))
for k,v in d['plugins'].items():
    for e in v: print(' ', k, '| scope=', e.get('scope'), '| ver=', e.get('version'), '|', e.get('projectPath','-'))
"
```

兩個必知的陷阱：

1. **註冊表對同一個 plugin 會有多筆，user scope 與 project scope 各一。
   project scope 覆蓋 user scope。** `claude plugin update` **預設只更新 user scope**
   （`--scope` 的 default 就是 `user`），即使你人在該 repo 目錄下也一樣 ——
   輸出會明講 `at user scope`。project scope 必須顯式指定：

   ```bash
   claude plugin update <plugin>@<marketplace> --scope project   # 於目標 repo 目錄下執行
   ```

   兩者都要跑。其他 repo 的 project scope 不受影響，得各自到該 repo 下再跑一次 ——
   而且從這個 repo 完全看不出來它們落後了，只有讀註冊表才知道。
2. **開發 clone 有未 commit 的改動時，後面三個位置永遠拿不到。**
   健檢時第一個要看的是 `git status`，不是版本號 —— 版本號在 `plugin.json` 裡，
   改了但沒 commit 一樣顯示新版，看起來像已經發布了。

> 重開 app **不會**更新任何一層 —— 它只重讀註冊表。正確順序是
> **commit + push → `claude plugin update`（user 與 project 兩次）→ 開一個新 session**。

**「Restart to apply changes」指的是新開 session，不是重開整個行程**（實測 2026-08-12）。
註冊表在 **session 啟動時**讀取，不是行程啟動時 —— 在既有的 Claude Code 行程裡開一個
新 session，就會載到更新後的版本。當前 session 則不會熱更新，改到天亮也看不到。

### 驗證載入了什麼：問 peer session，別急著開新的

`ListAgents` 會列出這台機器上其他的 Claude session。**挑一個啟動時間晚於更新的，
用 `SendMessage` 直接問它看得到哪些 skill** —— 它啟動時載入的東西就是答案。
比起 `spawn_task`（需要使用者點擊）或 `claude -p`（另一個行程，且可能因 OAuth 過期而起不來），
這是最輕的一條，且不需要任何人動手。

問話要指定**可分辨版本的探針**，不要只問「有沒有更新」：

- **新增的 skill 名**（只存在於新版）
- **更名前後的兩個名字**（如 `plan-handoff` → `session-handoff`）—— 更名是最好的探針，
  一眼分辨且不受描述改寫干擾

並明講「照你 skill 清單裡實際寫的回我，不要去讀磁碟上的檔案」——
否則對方可能去 `ls` cache 目錄，那回答的是磁碟狀態，不是它載入的狀態，題目就答錯了。

### 步驟 6 — 記憶

**委派給 `anthropic-skills:consolidate-memory`**，不要在這裡重造一套。它已經處理合併重複、
修正過期、修剪索引。

本 skill 只負責一件它不管的事：**判斷記憶檔裡有沒有東西該搬進 repo**。
記憶是私有、未入版控、換機器就沒了；凡屬「團隊該共享、該隨程式碼演進、該被 review」的
知識，正確的家是 `rules/` 或按需文件，不是記憶。

---

## 報告格式

寫進 scratchpad（拋棄式產物，不入版控）。決議落地後才改動實際檔案。

```markdown
# 設定檔健檢 — YYYY-MM-DD

## 基線
常駐 XXX,XXX 字元（約 NNk tokens），N 個檔。前次 YYY,YYY（+N.N%）。

## P0 — 正在誤導 agent（建議立即處理）
- [ ] `<檔>:<行>` — <一句問題> → <建議動作>

## P1 — 失效 / 矛盾（應處理）
## P2 — 搬家候選（減常駐成本，不損知識）
- [ ] `<檔>` §<節> — <N> 字元，屬「推導過程」→ 搬 `<目標>`，常駐留一句結論

## P3 — 精簡建議（可選）

## 已檢查且乾淨
<明確列出，讓下次健檢知道哪些不必重看>
```

**「已檢查且乾淨」不可省略。** 沒有它，下次健檢無法區分「這項沒問題」與「這項上次沒查」。

---

## 動手改的規則

1. **逐項確認後才改**，不要拿到報告就整批套用。
2. **一類一次 commit**（失效引用一批、搬家一批），讓每筆改動可獨立回退。
3. **搬家是移動不是重寫** —— 原文照搬到目標檔，常駐區改成結論 + 指路。順手改寫等於
   在沒有測試的情況下重構。
4. **改完驗證雙語同步**：文件若有 `.md` / `.zh-TW.md` 雙版，兩份都要改。
5. **不為了讓數字好看而刪內容** —— 常駐量是指標不是目標。

---

## 反模式

| 反模式 | 為什麼錯 |
|--------|---------|
| 「這段很長，精簡一下」 | 長度不是判準。**先問它會不會改變行為** |
| 砍掉踩雷紀錄與自我更正 | 它們是唯一阻止重蹈覆轍的東西，且作者通常已明示為何保留 |
| 自動套用報告 | 誤刪的規則不會報錯，只會讓未來每個 session 悄悄做錯 |
| 為湊「單一真相來源」硬合併刻意分工的兩檔 | 文件已自述邊界時，分工是設計不是重複 |
| 把所有數字都更新成最新 | 歷史紀錄（「當時量到 37 筆」）本來就該保留舊值 |
| 沒有基線就開始砍 | 沒有前後數字，無從判斷這次健檢有沒有用 |
| 在報告裡建目錄 / 改結構 | 結構決策要先提議、經確認 |

---

## 執行頻率

**先手動跑，累積 2–3 次再考慮自動化。** 排程一個還沒驗證過價值的流程，只會產生
沒人看的報告。

有節奏可綁時，最自然的錨點是**發版後**（版本節奏 ≒ 規則漂移節奏），而不是固定日曆週期 ——
沒有變動的月份跑健檢是純浪費。
