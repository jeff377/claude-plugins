# claude-plugins

可跨 repo / 跨團隊共用的 [Claude Code plugin](https://code.claude.com/docs/en/plugins) 目錄（marketplace）。
把「與特定專案無關的工作慣例」集中在此一處維護，各 repo 安裝後即同步，避免每個 repo 各留一份副本而 drift。

## 目前收錄的 plugin

| Plugin | 用途 | 內含 skill |
|--------|------|-----------|
| **plan-workflow** | 計畫文件（`docs/plans/`）撰寫慣例，與語言 / 框架無關 | `plan-write` |

## 安裝（在要使用的 repo 內）

於該 repo 的 `.claude/settings.json` 宣告本 marketplace，團隊成員信任資料夾後會被提示安裝：

```json
{
  "extraKnownMarketplaces": {
    "jeff377-plugins": {
      "source": { "source": "github", "repo": "jeff377/claude-plugins" }
    }
  }
}
```

再以互動指令安裝（`--scope project` 會寫入 `.claude/settings.json`，規則跟著 repo 走）：

```
/plugin install plan-workflow@jeff377-plugins
```

安裝後 `/reload-plugins` 生效；skill 帶命名空間，呼叫為 `/plan-workflow:plan-write`。

> **名稱不一致（刻意）**：repo 名為 `claude-plugins`（`source.repo` 用），marketplace 識別名為
> `jeff377-plugins`（key 與 `install ...@` 用）。官方保留 `claude-*` 字樣、不可作 marketplace 名
> （`claude plugin validate` 會擋），故兩者無法對齊；repo 名不受此限，取其 URL 乾淨。

## 本機開發 / 測試（免建 marketplace）

```bash
claude --plugin-dir ./plugins/plan-workflow
```

改動後 `/reload-plugins` 熱更新；提交前用 `claude plugin validate` 檢查結構。

## 目錄結構

```
claude-plugins/
├── .claude-plugin/
│   └── marketplace.json        # marketplace 索引（列出本 repo 有哪些 plugin）
└── plugins/
    └── plan-workflow/
        ├── .claude-plugin/
        │   └── plugin.json     # plugin manifest（僅此檔放 .claude-plugin/）
        └── skills/
            └── plan-write/
                └── SKILL.md
```

> **結構鐵則**：`skills/`、`agents/`、`hooks/` 一律放 plugin 根層；`.claude-plugin/` 內**只**放 manifest。

## 新增 plugin

1. 於 `plugins/<name>/` 建 `.claude-plugin/plugin.json` 與內容（`skills/` 等）
2. 在 `.claude-plugin/marketplace.json` 的 `plugins` 陣列補一筆，`source` 用相對路徑 `./plugins/<name>`
3. 本 README 的「目前收錄的 plugin」表格補一列
4. `claude plugin validate` 驗證後提交
