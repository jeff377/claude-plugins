---
name: changelog-draft
description: 整理 CHANGELOG（自上一版 tag 至 HEAD），依 Conventional Commits 分類、建議版號、產出草稿供使用者 review。先偵測該 repo 既有的 CHANGELOG 慣例（單語/雙語、單層/兩層明細）再沿用，不強加格式。當使用者提到「整理 CHANGELOG」、「準備發版」、「draft changelog」、「發 vX.Y.Z」、「下一版要發了」、「整理 release notes」之類情境時使用。**只產草稿，不 commit、不改版號檔、不打 tag。**
---

# CHANGELOG 整理

整理自上一版 tag 至 HEAD 的所有 commits，產出符合
[Keep a Changelog](https://keepachangelog.com/zh-TW/1.1.0/) 格式的條目草稿，
由使用者 review 後再走該 repo 的發版流程。

## 設計前提

- **沿用該 repo 既有慣例，不強加格式** —— 語言、結構、起始版本一律先偵測（Step 0）
- **不自動 commit / push**、**不改版號檔**、**不打 git tag** —— 那些屬發版流程，
  等使用者 review 完才動手
- 文件分工：CHANGELOG 是**版本差**紀錄；設計決策史屬 ADR；現行行為屬該 repo 的
  對外文件。三者互補 —— CHANGELOG 條目對應重大行為改動時應**連結對應 ADR**（若該 repo 有）

## Step 0：偵測該 repo 的既有慣例

**動筆前先讀既有 CHANGELOG**，把下列四項判定出來。這些是**可從檔案本身讀出的事實**，
不要憑假設，也不要照搬別的 repo。

| 要判定 | 怎麼看 |
|--------|--------|
| **語言** | 有無 `CHANGELOG.<lang>.md` 之類的並存檔？有就是多語，**每份都要改** |
| **結構** | 條目是「每條一行 WHAT」還是「多句含 WHY」？有無 per-version 明細目錄（如 `docs/changelogs/<版號>.md`）？ |
| **起始版本** | 最舊的條目是哪一版？**不回補更早的歷史**，除非使用者明說要 |
| **ADR 連結慣例** | 既有條目有沒有連向 ADR？ADR 目錄在哪（常見 `docs/adr/`）？**沒有該目錄就跳過 Step 4** |

```bash
ls CHANGELOG*.md                      # 語言版本
head -60 CHANGELOG.md                 # 結構、起始版本、ADR 連結慣例
ls docs/changelogs/ 2>/dev/null        # 有無 per-version 明細層
```

**偵測不到（全新 repo、或第一次寫 CHANGELOG）才問使用者**，用 `AskUserQuestion` 逐項附選項：
單語還是多語？單層（只有 `CHANGELOG.md`）還是兩層（主檔精簡 + per-version 明細）？

## Step 1：定位範圍與 sanity check

並行執行：

```bash
git tag --sort=-creatordate | head -3              # 取最近三個 tag，確認上版
git log <prev_tag>..HEAD --pretty=format:'%h %s'   # 取 subject 概覽
git log <prev_tag>..HEAD --pretty=format:'%h%n%s%n%b%n---END---'  # 取完整訊息（含 body）
git status                                         # 確認沒有 uncommitted changes
```

有 uncommitted changes → 先告知使用者並停下確認（避免漏掉未進版的變更）。
`<prev_tag>..HEAD` 為空 → 明確告訴使用者「無變更，不需發版」並結束。

## Step 2：依 Conventional Commits 分類

| 前綴 | 分類 | 是否進 user-facing CHANGELOG |
|------|------|------------------------------|
| `feat:` / `feat(scope):` | 新增 | ✅ 必入 |
| `feat!:` 或 commit body 含 `BREAKING CHANGE:` | 變更（breaking） | ✅ 必入，且需寫升級指引 |
| `fix:` | 修正 | ✅ 必入 |
| `perf:` | 變更（效能） | ✅ 必入 |
| `refactor:` | 視情況 | ⚠️ 改到公開 API / 預設行為才入；純內部重構 omit |
| `docs:` / `test:` / `chore:` / `build:` / `ci:` / `style:` | 多半 omit | ⚠️ 除非影響使用者（如發版前升級相依版本、改變預設設定值） |

**核心判斷原則**：這個變更會讓**使用者**需要改他們自己的程式碼 / 設定 / 相依宣告嗎？

- 會 → 列入並寫清楚要改什麼
- 不會 → omit（但在最終報告中列出，讓使用者確認沒誤判）

**模糊情境**：

- 同一個 PR 的多個 commits（feat + 後續 fix）→ 合併成一條 user-facing 描述
- `refactor` 改了 internal 但有公開 API 表面變化 → 列入
- 多 commit 串成同一個邏輯改動 → 看 commit message 群組脈絡判斷

## Step 3：版號建議

| Commits 內容 | 建議升版 |
|--------------|---------|
| 任一 breaking change | major |
| 至少一個 feat（無 breaking） | minor |
| 僅 fix / perf / 內部變動 | patch |

> **pre-stable 例外**：專案若**明文**處於 pre-stable（0.x，或宣告過「尚無外部消費者、
> minor 允許含 API 搬遷」），即使依嚴格 SemVer 應為 major 也可建議 minor ——
> 但**必須附理由讓使用者拍板**，且該破壞性變更要在 CHANGELOG 明列，不可靜默。
>
> 這條政策**從既有 CHANGELOG 或該 repo 的發版規範讀出**，不要自行假設。

## Step 4：連結 ADR（該 repo 有 ADR 目錄時才做）

對重大行為改動（breaking / 新模組 / 架構搬遷），掃 ADR 目錄找對應條目：

```bash
ls docs/adr/ 2>/dev/null | grep -i <關鍵字>
```

找到 → 條目末尾連結該 ADR（相對路徑，與既有條目的寫法一致）。
找不到但屬重大改動 → 標註「⚠️ 建議補 ADR」給使用者，**不自動建立**。

## Step 5：產草稿並寫入檔案

**依 Step 0 判定的結構產出。** 以下兩種都常見：

### 單層（只有主 CHANGELOG）

```markdown
## [X.Y.Z]

### 新增
- `<套件/模組>`：<一行 WHAT，含關鍵 API 名>。

### 變更
- `<套件/模組>`：<差異>。重大設計決策連結 ADR。

### 修正
- `<套件/模組>`：<bug fix>。

### 升級指引（僅 breaking 才需要）
（可操作的 diff）
```

### 兩層（主檔精簡 + per-version 明細）

主檔每條 **一行 WHAT**，WHY 進明細檔：

```markdown
## [X.Y.Z]

> 主題引言（1–3 句）＝這版的重點摘要。承載「為什麼這版重要」與整體脈絡，
> 是讀者掃讀時唯一需要看的敘事。版本性質特殊時（如嚴格 SemVer 屬 major、
> 政策下以 minor 發佈）也在此一句帶過。

📄 詳細變更與設計脈絡：[docs/changelogs/X.Y.Z.md](docs/changelogs/X.Y.Z.md)

### 新增
- `<套件/模組>`：<一行 WHAT>。
```

明細檔＝**主檔精簡前的完整版**：每條保留多句 WHY / 設計權衡 / 受影響範圍，
結構與主檔逐節對齊，讓讀者能在一行條目與展開版之間對照。
**以該 repo 最近一版的明細檔為範本**，不要自創格式。

**精簡原則（兩層結構的主檔，最容易失守）**：

- 每條 bullet **一行**，只寫 WHAT + 受影響模組。多句 WHY 一律進明細檔
- 砍掉「這讓我們能夠…」「以符合…的預期」這類解釋性尾句
- 主檔升級指引留可操作的 `diff`，散文說明進明細檔

**多語規則**：

- 各語言版**條目數必須一致**、逐條對齊翻譯
- 主檔與明細檔的連結各自指向同語言版本
- 升級指引的 code block 各語言完全相同，只翻譯說明文字

**寫入位置**：主檔**插在最新版條目之前**（最新版在最上面），不刪除既有內容。

## Step 6：交付 review

完成後給一份簡短報告：

1. **建議版號** + 理由（Step 3 規則 + pre-stable 考量）
2. **條目數量摘要**（X 新增、Y 變更、Z 修正；多語則確認各語言一致）
3. **被 omit 的 commits 清單** —— 讓使用者判斷有無誤判
4. **建議補 ADR 的項目**（若有）
5. **下一步**：review 完依該 repo 的發版流程走（更新版號檔、commit、push tag）

## 不做什麼

- ❌ **不自動 commit / push** CHANGELOG 改動
- ❌ **不改版號檔** —— 版號的單一來源因 repo 而異（`Version.props`、
  `Directory.Build.props`、`package.json`、`pyproject.toml`…），且屬發版流程步驟
- ❌ **不打 git tag**
- ❌ **不回補既有起始版本以前的歷史** —— 除非使用者明說
- ❌ **不為 omit 的 commit 編造 user-facing 描述** —— 誠實標 omit，由使用者決定
- ❌ **不自動建立新 ADR** —— 只標註建議
- ❌ **不把別的 repo 的格式套過來** —— 一律以 Step 0 偵測到的既有慣例為準
