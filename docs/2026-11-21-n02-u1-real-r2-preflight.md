# N02-U1：2026-11-19 R2 原始来源绑定 → Speed3 正式库预审

**状态：真实 R2 源档已逐条审计，正式本机 SQLite 比对尚未在这次聊天中执行。不得声明 N02-U1 PASS。**

## 1. 原始输入与审计

找回的**原始完整 ZIP**：`SRW_F_FF_最终统一定名_20261119_R2.zip`

- ZIP：97,628 B，SHA-256 `1f4f99dd1271dd64c149d283624cfa6c5404f260372f124267c36c0f6da17eb7`。
- `统一简体中文名称.tsv`：61,734 B，SHA-256 `ea5bdc2a6e1557d149247e1b37a7464f27eb88126d1a91face16933af09de693`。
- `工程来源定名绑定.tsv`：316,877 B，SHA-256 `459bbb24db91e97b313e20ce99a3490dd93f430df78d15208c414046bf1d1c18`。
- **5/5 ZIP 成员 CRC32 通过**；真实 TSV 解析：1,392 个唯一实体、4,857 个唯一来源ID。来源分布 SSF **2,311**，SSFF **2,546**。实体分类：PERSON 333、UNIT 425、WEAPON 634；来源绑定类别 PERSON 1,534、UNIT 780、WEAPON 2,543。
- 原始 TSV 内：重复来源ID 0、缺失实体0、名称不一致0、类别不一致0、坏列0。以上为**同一 R2 包内部核验**，不等同于正式库跨库核验。
- 本次不重复制作原 R2 词典，也不在公开 GitHub 上传其中原文、姓名、绑定明细或私人 DB。

## 2. Speed3 最新版本事实

已查网盘 `N03_N08_正式台账_Speed3合并_v1_20261121`：
- 正式 `UETS_TEXT_CATALOG.sqlite` 报告大小 **1,481,125,888 B**，SHA-256 `09e125aafb44712e91d0110fc0f2aae0dea648562a4ea0097d2d3a9557c8472b`。
- Speed3 `UETS_SPEED3_FORMAL_MERGE.json`：验收记录 1,549→1,556（新增7、冲突0）。新增6条Speed3本轮验收及1条Speed2历史范围登记；不要混为7个新增运行成功场景。
- 原先 N09 R2 P045 的392条技术HOLD仅是历史版本快照。Speed3已有外置中文字形、地图流程、普通存档和BIOS独立冷读的有界验收；仍不能由此认定 P045 426条每一个消费者全部验收。

## 3. 实际本机执行入口

新工具 `tools/n02_u1_real_r2_preflight.py` **直接读取完整原始 R2 ZIP**，在临时目录解出两个 TSV，使用真实 SHA pin 检查，依次调用 PR#6 的独立 staging 与核验工具，再对指定正式数据库运行只读对比。

示例（把第一行原始ZIP路径改为其真实位置；数据库路径来自 Speed3 正式合并回执）：

```powershell
python tools/n02_u1_real_r2_preflight.py `
  --r2-zip "R2原始ZIP的实际路径\SRW_F_FF_最终统一定名_20261119_R2.zip" `
  --formal-db "D:\CodexArchives\20261121_UETS_P045\outputs\UETS\catalog\UETS_TEXT_CATALOG.sqlite" `
  --expected-formal-db-sha256 09e125aafb44712e91d0110fc0f2aae0dea648562a4ea0097d2d3a9557c8472b `
  --speed3-merge-receipt "UETS_SPEED3_FORMAL_MERGE.json的实际路径" `
  --out-dir "D:\SSFFWORD\N02_U1\R2_REAL_PREFLIGHT_NEW"
```

**注意**：这只是可运行的命令示例，不表示助手已连接到 Windows 本机，也不保证示例路径全部存在。真正运行会拒绝覆盖已有输出。生产日志和私人数据库留在本机，不上传公开仓库。

自动定位真实来源表和绑定表需要**唯一且语义适当的表名和字段名**。如正式 DB 存在多个候选，必须从 `REAL_PREFLIGHT_STATUS.json` 查看 `schema_candidates`，然后明确重跑 `--source-table`、`--source-column`、`--binding-table`、`--binding-source-column`，禁止靠行数自行猜测来源。

输出包括 `N02_U1_R2_BINDINGS_STAGING.sqlite`、`R2_INDEPENDENT_AUDIT.json`、`SOURCE_IDS_MISSING.tsv`、`BINDINGS_MISSING.tsv`、`BINDINGS_CONFLICT.tsv`、`BINDINGS_DUPLICATE.tsv`、`FORMAL_BINDINGS_EXTRA.tsv`、`REAL_PREFLIGHT_STATUS.json`。所有输入只读、不改正式正文，也不触碰ISO/BIN/CUE。

## 4. 验收状态解释

- `REAL_R2_TO_FORMAL_BINDING_PASS_PENDING_OTHER_U1`：仅证明R2来源ID→实体ID与选定正式数据库表严格一致，**仍不是N02-U1最终PASS**。
- `REAL_R2_PREFLIGHT_PARTIAL_OR_BLOCKED`：来源表/绑定表缺证、行数不符、身份差异、DB哈希不符或Speed3回执不一致。保留输出清单，不私自更改正式库。
- GitHub Actions 的 90,099／4,857／1,556 **合成数据**测试，只证明代码工作，不证明正式私有数据库已处理。

下一步仍需真实本机回执、实际字段/表名和差异清单，之后才能审定来源绑定与新版本范围。N08／N09最新译文批准与35类文字覆盖不是本工具的自动PASS对象。
