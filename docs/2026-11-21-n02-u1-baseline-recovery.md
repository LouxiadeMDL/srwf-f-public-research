# N02-U1 — SSF／SSFF 唯一简体中文文本与攻略来源统一（执行记录）

**日期：2026-11-21**  
**状态：输入已恢复；离线基线构建脚本已提交；数据库迁移、语义审校和最终验收尚未通过。**

## 已读取的私有输入及核验边界

| 输入 | 实际确认 |
|---|---|
| SSF／SSFF v1.1r2 静态完整包 | 可定位既有来源主库及审计，已知统计 90,099 个源记录、68,240 条现行 MANUSCRIPT_TEXT |
| N03／N04 2026-11-19 交付 | 包含原关系库、文本来源及调用关系查询源码；既有报告数据库大小为 1,690,554,368 B、SHA-256 为 `f00e3109d9099647f85f7fd73506ab5b1ae00714ba99b9aa65892ce5d136d350`，本次还未对其解包数据库独立复算 |
| R2 定名 TSV | 1,392 个实体正式中文，已找到并取得文件；4,857 条精确工程来源绑定仍须恢复并验证 |
| F 攻略 v0.2 | Google Drive 中已恢复原 SQLite，1,062 页、59,398 行，包含 F／FF／SFC《第四次》多个来源 |
| FF 攻略 v1.0.2 | Google Drive 中已恢复 SQLite，812 页、42,865 行，以及 44 条 QA resolution 和 109 条 crosscheck facts |
| 《机战30》与《机战Y》 | 已有合并研究库 v2；只能作为外部证据，不得覆盖用户锁名或现行主稿 |
| N08／N09／UETS | 有此前工作记录，但本次未形成“所有最新修订完整继承”的可复算结论 |

**已确认的旧证据不是新运行证据。** 尤其 N03 的 128,513 条来源关系不能等同于 128,513 次动态运行，35 类范围没有因登记就自动通过。

## 本次新增的公开安全工具

[tools/n02_u1_baseline_builder.py](../../tools/n02_u1_baseline_builder.py)

该脚本使用 Python 3.10+ 标准库，以输入的 N03 父数据库作为*只读*来源，输出新的 SQLite 副本，建立实体／正式译名／合法形式／攻略来源／页面和行／修订／QA 结构。它只复制已有攻略转录到独立规范化字段，**不做任何未经身份核验的文字替换**。对于重复 FF 攻略版，旧版标记档案用途，v1.0.2 标记为首选核对资料。

本次未能完成真实私有数据库构建和此脚本的运行验证。使用前必须对输入快照做 SHA-256 核验，并用输出 `*.audit.json` 检查实际导入记录数、完整性和外键。不要把这一工具的提交视为 N02-U1 已交付或已冻结。

示例执行：

```bash
python tools/n02_u1_baseline_builder.py \
  --n03 /private/N03_N04_parent.sqlite \
  --guide-f /private/SRWF_F_GUIDE_TEXT_CORPUS_v0.2.sqlite \
  --guide-ff /private/SS35_FF_GUIDE_TEXT_CORPUS_v1.0.2.sqlite \
  --r2 /private/统一简体中文名称.tsv \
  --out /private/SSF_SSFF_CANONICAL_MASTER_STAGING.sqlite
```

## 仍须完成的门槛

- 完整恢复 N08/N09 最新批准文稿、4,857 条定名精确绑定、UETS 来源关系和既有保护规则。
- 对旧 N03 关系主库单独复算版本 SHA、原表身份和 90,099／68,240 源映射，确认没有版本混入。
- 按真实实体身份逐来源修订 F／FF 当前中文；每条修订生成旧文/新文/对应源 ID/理由差分。
- 攻略使用原文不可变 + 独立规范化层 + 来源与页码证据；不能靠全局字符串替换。
- 继承 FF QA44、唯一冲突记录和网页交叉核验；还需逐页、逐行精确身份核对。
- 35 类按政策逐一标记 DATA_PASS、CALLSITE_PASS、RUNTIME_PASS 等不同等级。
- 输出两个正式全文 JSONL、索引 TSV、差分、可复现 SHA、恢复包；只有通过独立复核才能冻结。
- 私有游戏脚本、汉化全文、扫描攻略和原生二进制只能保存于用户授权的非公开备份，不上传到该公开 GitHub 仓库。

## 仓库策略

本仓库为 **public-safe research**，只公开通用脚本、合成测试、哈希及边界说明。私人完整数据库和攻略文字不应进入公开版本。

## 2026-11-21 independent verification update

- Added `tools/n02_u1_independent_verify.py`: independent read-only SHA-256, full-table typed-row digest, original-table schema comparison, R2 1,392-name exact match, guide source counts and FF 44-QA inheritance checks. Fails closed on changed source records.
- Added `tests/test_n02_u1_offline_pipeline.py` and `.github/workflows/n02-u1-regression.yml`. Tests generate synthetic source/guide tables and 1,392 dummy names, build a candidate, verify that original data is unchanged, then deliberately modify an original row and confirm the independent checker marks the candidate BLOCKED.
- GitHub Actions synthetic test: [run 44864614704](https://github.com/LouxiadeMDL/srwf-f-public-research/actions/runs/44864614704) — conclusion SUCCESS. The job's explicit synthetic verification step also returned SUCCESS.
- **This proves only the public-safe sample pipeline, not private production migration.** The full 1.69 GB N03 database and both real guide SQLite databases still need the same checks in a working file-execution runtime. Actual latest N08/N09 revisions, 4,857 R2 source bindings, term occurrences, 35-category signoff and real guide normalization remain OPEN.
- Current outcome: `N02_U1_PARTIAL`. Do not freeze the candidate as the unique N08/UETS source or claim completed game/run-time verification.


## 2026-11-21 real-input recovery and audit hardening (follow-up)

- Read-only opened the **real** F guide SQLite (50,843,648 B) and FF guide SQLite (65,470,464 B). Both returned SQLite integrity_check=ok. Actual counts: F 1,062 pages / 59,398 lines; FF 812 pages / 42,865 lines / 44 QA resolutions / 109 crosschecks.
- Located the actual N03/N04 2026-11-19 delivery ZIP (343,039,408 B), v1.1r2 full static delivery ZIP (159,001,857 B), N08 R1 MasterData ZIP (223,913,748 B), and final R2 TSV (61,734 B) in the user's private file library. The 1,690,554,368-B parent SQLite has not yet been extracted and freshly hashed in this follow-up.
- Read all 1,392 R2 TSV data rows; each entity ID is unique. Category distribution: 333 PERSON, 425 UNIT, 634 WEAPON. One numeric-looking canonical name was flagged for manual identity review, not edited and not copied into this public report.
- Improved independent verifier: source guide page/line original text, IDs, positions, and FF QA/crosscheck raw records now have independent full-record digests, in addition to legacy-table and R2 checks. Synthetic regression now alters an imported guide line and FF QA record; both must be rejected.
- **Execution blocker:** after the large private archives were staged, the container/code-execution interface returned system-level errors, including on simple commands. No production N03-to-U1 migration, original N03 SHA verification, or 68,240-manuscript review was completed. Earlier successful synthetic-file stress tests do not prove the private-archive execution path is healthy.
- Safety gate remains **N02_U1_PARTIAL**. Do not publish private records, treat synthetic CI as formal acceptance, freeze a canonical master, or feed an unverified candidate to N08/UETS. Code changes are committed; independently confirm their GitHub Actions outcome before treating the new regression as passing.


## 2026-11-21 OCR 原始层与校对层分离（独立分支）

- **发现并修复**：旧构建器曾把 FF v1.0.2 的 `canonical_text`（已校对）作为 `GUIDE_PAGE.original_transcript`，使原始 OCR 转录与校对层身份混淆。新版本要求来源存在 `transcript_text`，原样保留在 `original_transcript`；校对后的 `canonical_text` 独立存入 `GUIDE_PAGE_CORRECTION_SOURCE.corrected_source_text`，同时作为尚未做实体替换的规范化起点。
- **拒绝自我认证**：基线构建阶段 `U1_ORIGINAL_PRESERVED` 状态由未获独立核验的 `PASS` 改成 `PENDING_INDEPENDENT_AUDIT`；N02-U1 仍不得转为最终 PASS。
- **增加独立证据检查**：逐条检查 FF 原始 OCR 与单独保存的校对来源，核对构建输入清单中的 SHA-256/文件大小/名称；来源区分采用精确前缀，而不是把下划线作为 SQL LIKE 通配符。
- **负向测试**：模拟数据上，篡改旧主表、攻略原始行、FF 44项 QA、FF 校对来源和输入回执，应全部拒绝通过；同时确认 F v0.2 中重复的旧 FF 812页标记为仅归档，FF v1.0.2 为首选。
- **GitHub Actions synthetic-only PASS**：[run 44876385373](https://github.com/LouxiadeMDL/srwf-f-public-research/actions/runs/44876385373)，提交 `5a7266c9cfbff29d2b7c505741a01f617a644dc8`。早期运行失败并通过日志修复测试语法与不确定行号问题；不隐瞒失败历史。
- **边界**：上述通过仅证明模拟数据和独立检查器的行为；尚未在实际 1.69GB N03、真实 F/FF 攻略库、4,857项 R2 来源绑定或 N08/N09 最新主稿上运行。状态保持 `N02_U1_PARTIAL`；没有生成或批准正式数据库，没有改写 ISO/BIN/CUE，未公开游戏或攻略正文。
