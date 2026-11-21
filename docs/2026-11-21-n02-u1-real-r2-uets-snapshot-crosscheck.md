# N02-U1 — R2 与 UETS 双真实归档定名绑定交叉核查

日期：2026-11-21。**已完成两个真实归档快照的独立读取比对；尚未对 Speed3 正式 SQLite 文件作本机 SQL 读取。**

## 1. 源文件身份

| 证据 | 文件 | 精确 SHA-256 |
|---|---|---|
| R2 原始交付 ZIP | `SRW_F_FF_最终统一定名_20261119_R2.zip` | `1f4f99dd1271dd64c149d283624cfa6c5404f260372f124267c36c0f6da17eb7` |
| R2 映射 TSV | `工程来源定名绑定.tsv` | `459bbb24db91e97b313e20ce99a3490dd93f430df78d15208c414046bf1d1c18` |
| UETS 设计源档 ZIP | `UETS_设计源码汇总_20261121.zip` | `f799d05d290fcd7313a4f0dd1824d7f4f43956cd804df74d72b9b60db825ca34` |
| UETS 实际绑定 TSV | `UETS/catalog/N08_R2定名绑定.tsv` | 按上述归档内文件抽取，原文不公开 |

本轮直接在连接器读取的原始 ZIP 数据上，以独立的 JS ZIP 解压/UTF-8 解析进行逐行对照；这不是 GitHub 合成测试生成的4,857行。

## 2. 实际逐行核查结果

| 项目 | 数值 |
|---|---:|
| R2 原始绑定行数 | 4,857 |
| UETS N08 归档绑定行数 | 4,857 |
| 来源 ID 精确一一相同 | 4,857 |
| 实体 ID 一致 | 4,857 |
| PERSON / UNIT / WEAPON 类别一致 | 4,857 |
| 唯一简体中文定名一致 | 4,857 |
| 缺少、额外或不同定名 | **0** |
| UETS 对 v1.1r2 作者稿的目标名称变化 | 1,265 |
| 当前镜像字形/排版检查配置 | 4,461 |
| 短名消费者/排版检查配置 | 396 |
| `NOT_INSTALLED_BY_THIS_CATALOG_IMPORT` 字段 | 4,857 |

最后一行表示该次**目录导入本身没有安装镜像**，绝不等于4,857处当前游戏全部未安装、也不等于所有名称窗口已经运行通过。

字段映射：`原始来源ID ↔ source_id`、`实体ID ↔ entity_id`、`类别 ↔ name_kind`、`简体中文定名 ↔ approved_cn`。单凭中文字符串相同不能认定不同源 ID 属于同一人物/机体。

## 3. 正式数据库结构已经以原始 schema 核对

归档 `UETS/catalog/schema.sql` 记录：
- `TEXT_SOURCE(source_id,cn_final,authoring_revision,freeze_status,...)`：旧 UETS 回读90,099条。
- `n08_name_binding(source_id,entity_id,name_kind,approved_cn,...)`：4,857条正式目标绑定。
- `TEXT_CALLSITE(callsite_id,...)`：128,513条登记的调用/存储关系，**不是128,513次运行触发**。
- `TEXT_ACCEPTANCE(acceptance_id,...)`：Speed3合并前1,549条，Speed3正式回执1,556条（新增7；6项本轮、1项历史Speed2）。

正式 Speed3 备份 `catalog/UETS_TEXT_CATALOG.sqlite` 按已保存的外部回执：
- 字节数：1,481,125,888。
- SHA-256：`09e125aafb44712e91d0110fc0f2aae0dea648562a4ea0097d2d3a9557c8472b`。
- 合并正式记录数：1,556，历史1,549完整继承（以合并回执为证据，**尚未本轮独立重算SQLite**）。

## 4. 新增工具与未完成门槛

`tools/n02_u1_r2_uets_archive_compare.py`：可在本机对上述两份原始ZIP进行 SHA/CRC校验、逐行4字段对比，不读取或更改游戏镜像和数据库。

`tools/n02_u1_real_r2_preflight.py`：从恢复的原始R2 ZIP生成 sidecar，独立核对，然后以**准确的** `TEXT_SOURCE` / `n08_name_binding` / `TEXT_CALLSITE` / `TEXT_ACCEPTANCE` 四张表为门禁读取本机正式SQLite，分别导出：
- 来源缺失、实体ID冲突、类别冲突、唯一中文名冲突。
- `cn_final` 与批准名称不同的**合法字段形式待审**清单；不能自动修改正文或把所有不同都视为错误。
- 保留 Speed3 7 条有界验收以及历史N09 R2 392条HOLD的版本区分。

如某条源ID在两真实归档中一致，但在最新正式 SQLite 中不同，需以正式库版本、冻结规则及当事证据追查差异，**不能由这个工具自动覆盖正式库**。

**N02_U1_PARTIAL。** 本轮真实跨源快照4,857条通过≠Speed3最新SQLite独立SQL通过≠全35类文字或游戏运行验收完成。原始私人TSV、攻略、镜像和大型数据库不得上传公开仓库。

恢复归档：Google Drive 中的原始 R2 ZIP（97,628字节）、UETS设计工程 ZIP（1,924,678字节）以及 Speed3 3卷归档。正式库在用户私有本机或私有网盘恢复后才能进一步完成真实SQL核验。
