---
name: release
description: .NET / NuGet repo 的發版流程 —— 前置條件檢查、版號判定（含 analyzer 擋不到的破壞性變更兩類自檢）、四個步驟（CHANGELOG、版號檔、PublicAPI.Unshipped→Shipped、commit+tag）、以及「push main 與 push tag 分兩次、中間停一下」的不可逆閘門。當使用者要「發版」、「發 vX.Y.Z」、「release」、「準備出版本」、「打 tag 發佈」、「上 NuGet」之類需求時使用。**agent 不自動推送 tag——那步必須由使用者明確同意。**
---

# 發版流程（.NET / NuGet）

適用於以 NuGet 套件發布的 .NET repo。**本 skill 是 .NET 專屬**（`PublicAPI` analyzer、
slnx / sln build、`nuget-publish` workflow），不假裝語言中立。

CHANGELOG 的產出走 **`/dev-workflow:changelog-draft`**（本 plugin 內），它只產草稿、
不 commit、不改版號、不打 tag。

## 前置條件

發版前逐項確認，任一項不成立就先處理：

| 項目 | 檢查方式 |
|------|---------|
| `main` 的 CI 是綠的 | `gh run list --branch main --limit 3` |
| 工作區乾淨 | `git status --short` 無輸出 |
| 距上次 tag 確實有 user-facing 變更 | `git log <last_tag>..HEAD --oneline` |
| 有動到 `src/` | `git diff --stat <last_tag>..HEAD -- src/` |

若只有 `docs:` / `test:` / `chore:` 的異動，**不需發版**。

## 版號判定

| 內容 | 升版 |
|------|------|
| 任一破壞性變更 | major |
| 至少一個 `feat`（無破壞性） | minor |
| 僅 `fix` / `perf` / 內部變動 | patch |

**pre-stable 例外**：專案若**明文**處於 pre-stable（0.x，或宣告過「尚無外部消費者」），
允許在 minor 中包含 API 搬遷與破壞性變更——但**必須在 CHANGELOG 明列**，不可靜默。

### 破壞性變更的判定

`Microsoft.CodeAnalysis.PublicApiAnalyzers` 只擋「**未申報**」，擋不到「**已申報但不相容**」。
發版前自行檢查兩類：

```bash
# 1. Shipped 檔的「移除」＝ source-breaking
git diff <last_tag>..HEAD -- "**/PublicAPI.Shipped.txt" | grep "^-" | grep -v "^---"
```

2. **二進位不相容但語法相容**的變更，需人工判讀：
   - 對既有 public 建構子增加 optional 參數 → **二進位破壞性**，應改為新增多載
   - public 介面新增成員 → 對外部實作者為 source-breaking，需在 CHANGELOG 標明

## 四個步驟

### 1. CHANGELOG

走 **`/dev-workflow:changelog-draft`**。它會偵測該 repo 既有的結構（單語/多語、
單層/兩層明細）並沿用，產出草稿供 review。

重大行為改動連結對應 **ADR**；若無對應 ADR 而屬重大決策，**先補 ADR 再發版** ——
決策理由不該只存在於 plan（plan 是階段性文件，公開文件不得引用）。

### 2. 版號

改該 repo 的**版號單一來源**。.NET repo 常見落點：

- repo 根或 `src/` 的 `Directory.Build.props`
- 獨立的 `Version.props`（由各目錄的 `Directory.Build.props` 顯式 import）

```xml
<Version>x.y.z</Version>
<AssemblyVersion>x.y.z.0</AssemblyVersion>
<FileVersion>x.y.z.0</FileVersion>
```

> **「只有一個來源」是結構要求，不是紀律要求。** repo 內若有**不繼承**該檔的可發布專案
> （典型：位於 `tools/` 卻會上 NuGet 的 dotnet tool），它會自帶一份版號，而「記得一起
> bump」沒有任何機制會發現被違反 —— 實際踩過：那份副本停在某版整整十二個 minor。
> **per-project 的版號一致性閘門擋不到**（它只檢查三個屬性彼此一致，而
> `4.8.0` / `4.8.0.0` / `4.8.0.0` 完全自洽）。
> 正解是抽成共用檔，由每個需要的目錄顯式 import。

bump 完掃一次舊版號殘留（CHANGELOG／逐版明細／plan 是歷史紀錄，故排除）：

```bash
grep -rn "<舊版號>" --include="*.md" . \
  | grep -v CHANGELOG | grep -v "docs/changelogs/" | grep -v "docs/plans/"
```

**命中要逐筆判讀，不可無腦清空。** 判別法與「文件不得複寫版號」的通則見
`~/.claude/rules/single-source.md`（常駐規則）。摘要：這個版號在講「本專案現在是哪一版」
還是「當時量到什麼」？前者是複寫 → 改成指路（**不要改成新版號，那下次還會再漂**）；
後者是紀錄 → 保留。

### 3. `PublicAPI.Unshipped.txt` → `Shipped.txt`

每個有異動的套件，把 Unshipped 併入 Shipped 並清空 Unshipped。**不能單純 append** ——
Unshipped 有兩種語意相反的條目：`Foo.Bar() -> void` 是新增（加進 Shipped），
`*REMOVED*Foo.Bar() -> void` 是移除（從 Shipped **刪掉**該行，標記本身**不進** Shipped）。
直接 append `*REMOVED*` 會 build 失敗於
**`RS0024: The shipped API file can't have removed members`**。

腳本隨本 skill 散佈，位於**本 skill 目錄下的 `scripts/merge-public-api-shipped.sh`**
（skill 載入時會告知其 base directory；`${CLAUDE_PLUGIN_ROOT}` 亦可用）：

```bash
bash <本 skill 目錄>/scripts/merge-public-api-shipped.sh <last_tag>
```

腳本已處理兩種條目、`LC_ALL=C` 排序（`~override` 才排對位置）與空移除清單的兜底，
**細節寫在檔頭**。完成後跑一次 clean Release build —— analyzer 通過即證明申報一致：

```bash
dotnet build <方案檔> -c Release --no-incremental
```

### 4. commit + tag

```bash
git commit -m "chore(release): x.y.z — <一句主題>"
git tag -a vx.y.z -m "x.y.z — <一句主題>"
```

tag 用 **annotated**（`-a`），與既有 tag 一致。

## 推送：分兩次，中間停一下

**`git push origin vx.y.z` 會觸發發佈 workflow，而 NuGet 版本發布後無法刪除**（只能 delist）。

```bash
git push origin main        # 觸發 CI，可逆
# → 等 CI 綠燈，並 review CHANGELOG / ADR 的措辭
git push origin vx.y.z      # 觸發 NuGet 發布，不可逆
```

中間那段停頓的用意：**CI 只驗證程式碼，驗不到文件措辭**。而 CHANGELOG 與 ADR 一旦發布
就是長效紀錄，要改得再發一版。

tag 尚未推送前隨時可重來：

```bash
git tag -d vx.y.z
```

## agent 的行為約束

- **不自動推送 tag** —— 發布是不可逆的對外動作，必須由使用者明確同意。
  （這條同時是常駐規則，見 `~/.claude/rules/releasing.md`，即使沒喚起本 skill 也成立。）
- **不為了讓建置通過而改測試或原始碼** —— 那是 commit 前驗證機制要防的事情本身。
