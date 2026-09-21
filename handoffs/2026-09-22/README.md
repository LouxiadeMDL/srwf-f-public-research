# 2026-09-22 研究交接数据

先读[交接报告](../../docs/2026-09-22-cross-game-research-handoff.md)。本目录只包含重新整理的研究元数据，不含游戏数据、第三方全文或私人路径。

文件用途：

- `claims.json`：已有成果、证据等级和限制。
- `leads.json`：仍有价值的线索、历史查询时间及下一步检查。
- `sources.json`：来源 ID、文件名、大小、哈希。完整原路径只保留在本地索引。
- `database_catalog.json`：本次只读检查的数据库及表计数；不是数据库内容转储。
- `inventory_summary.json`：10,816 文件的分类统计与扫描边界。
- `verification.json`：本次核验范围及基线遗留告警。
- `MANIFEST.json`：本目录与对应报告/生成工具的精确 SHA-256 清单；不包含清单自身。

在仓库根目录执行（仅 Python 标准库，不安装依赖）：

```sh
python tools/build_handoff_catalog.py --input handoffs/2026-09-22 --output ../research_handoff.sqlite
```

工具先验证清单并拒绝覆盖现有数据库；然后生成独立的交接索引 SQLite。可查询 `claims`、`leads`、`sources`、`databases`、`table_counts`。来源文档不是本次重新完成的实验；请保留 `evidence_class`、`limitations` 和日期字段。

```sql
SELECT id, domain, title, evidence_class, limitations FROM claims;
SELECT id, priority, status, next_check FROM leads ORDER BY priority, id;
SELECT database_id, table_name, rows FROM table_counts;
```

这不是 ROM 包、字库包、完整脚本库或冻结研究数据库全量镜像。分发权限不随来源哈希转移。
