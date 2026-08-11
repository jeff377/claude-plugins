# claude-plugins

可跨 repo / 跨團隊共用的 [Claude Code plugin](https://code.claude.com/docs/en/plugins) 目錄（marketplace）。
把「與特定專案無關的工作慣例」集中在此一處維護，各 repo 安裝後即同步，避免每個 repo 各留一份副本而 drift。

## 目前收錄的 plugin

| Plugin | 用途 | 內含 skill |
|--------|------|-----------|
| **dev-workflow** | 開發流程慣例（計畫撰寫 / 交接 / 執行閘門，後續擴及 CI、源掃、發佈），與語言 / 框架無關 | `plan-write`、`session-handoff`、`plan-execute` |

## 安裝（在要使用的 repo 內）

於該 repo 的 `.claude/settings.json` 宣告本 marketplace：

```json
{
  "extraKnownMarketplaces": {
    "jeff377-plugins": {
      "source": { "source": "github", "repo": "jeff377/claude-plugins" }
    }
  },
  "enabledPlugins": {
    "dev-workflow@jeff377-plugins": true
  }
}
```

`enabledPlugins` 直接寫進版控的 `.claude/settings.json`，plugin 即跟著 repo 走，
團隊成員信任資料夾後會被提示安裝。也可用 CLI 安裝：

```bash
claude plugin install dev-workflow@jeff377-plugins
```

> **用 CLI，不要用斜線指令。** `/plugin`、`/reload-plugins` 需要互動式終端機面板，
> 在 Claude Code 桌面版 / 網頁版等環境**不存在**——貼進 shell 只會得到 command not found。
> `claude plugin` CLI 在所有環境都可用，且可非互動執行。

安裝或改名後**須完全重開 session** 才會生效（熱更新不可靠）。
skill 帶命名空間，呼叫為 `/dev-workflow:plan-write`。

驗證是否真的裝上：

```bash
claude plugin list
```

> **名稱不一致（刻意）**：repo 名為 `claude-plugins`（`source.repo` 用），marketplace 識別名為
> `jeff377-plugins`（key 與 `install ...@` 用）。官方保留 `claude-*` 字樣、不可作 marketplace 名
> （`claude plugin validate` 會擋），故兩者無法對齊；repo 名不受此限，取其 URL 乾淨。

## 本機開發 / 測試（免建 marketplace）

```bash
claude --plugin-dir ./plugins/dev-workflow
```

提交前用 `claude plugin validate` 檢查結構。

## 目錄結構

```
claude-plugins/
├── .claude-plugin/
│   └── marketplace.json        # marketplace 索引（列出本 repo 有哪些 plugin）
└── plugins/
    └── dev-workflow/
        ├── .claude-plugin/
        │   └── plugin.json     # plugin manifest（僅此檔放 .claude-plugin/）
        └── skills/
            ├── plan-write/
            │   └── SKILL.md
            ├── session-handoff/
            │   └── SKILL.md
            └── plan-execute/
                └── SKILL.md
```

> **結構鐵則**：`skills/`、`agents/`、`hooks/` 一律放 plugin 根層；`.claude-plugin/` 內**只**放 manifest。

## 新增 plugin

1. 於 `plugins/<name>/` 建 `.claude-plugin/plugin.json` 與內容（`skills/` 等）
2. 在 `.claude-plugin/marketplace.json` 的 `plugins` 陣列補一筆，`source` 用相對路徑 `./plugins/<name>`
3. 本 README 的「目前收錄的 plugin」表格補一列
4. `claude plugin validate` 驗證後提交

## 改名 plugin

plugin 改名對消費端是破壞性變更（skill 前綴與 `enabledPlugins` key 都會變），
`plugin.json` 的 `version` 應進 major：

1. `git mv plugins/<old> plugins/<new>`
2. 更新 `plugin.json` 的 `name` 與 `version`、`marketplace.json` 的 `name` 與 `source`
3. 更新兩份 README（含目錄結構圖與 skill 前綴範例）
4. 掃描消費端 repo 的宣告：`grep -rl "<old>" ~/…/*/.claude/settings*.json`
5. 各消費端更新 `enabledPlugins` key，重裝後**完全重開 session**
