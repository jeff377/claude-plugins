# plan-workflow

計畫文件工作流慣例，與程式語言 / 框架無關，適用任何以 `docs/plans/` 管理計畫的 repo。

## 內含 skill

| Skill | 用途 |
|-------|------|
| `plan-write` | 計畫文件的狀態列格式、多階段階段表格、連結慣例（含「公開文件不得連結 plan」）、封存流程規範 |
| `plan-handoff` | plan 定案後交接給新 session 實作：交接 prompt 的必備內容與範本 |

## 搭配 gate 使用（建議）

本 plugin 只提供**格式規範**（按需載入），不含「必須先擬計畫才執行」這類 always-on 紀律。
後者屬於各 repo 的 `CLAUDE.md` gate，因為 skill 靠 description 觸發、無法保證擋下
「該擬計畫卻直接動手」的情況。建議在使用本 plugin 的 repo 的 `CLAUDE.md` 加一段：

```markdown
### 執行前先擬計畫

任何需要事先規劃的任務，必須：
1. 將計畫寫成 md 存至 `docs/plans/`，檔名 `plan-<主題>.md`
2. 每次建立 / 修改後，回覆附上該 plan 連結
3. 等使用者確認後才執行
4. 執行完畢立刻在文件頂部標記完成狀態
5. 由使用者要求時才移至封存目錄（慣例 `docs/plans/archive/`）
6. 公開文件（README / CHANGELOG / ADR / 對外指引）一律不得連結或引用 plan

> 狀態列格式、階段表格、連結慣例、封存細節 → 見 `/plan-workflow:plan-write`。
```

gate（常駐、擋關）與 skill（按需、給格式）分工，是本 plugin 的設計前提。
