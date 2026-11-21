# N02-U1 R2 来源绑定预审（不写回原主库）

日期：2026-11-21。当前正式 N02-U1 状态：`PARTIAL`。

## 解决的问题

R2 唯一定名已登记 **1,392 个实体**，后续 N08 有 **4,857 条工程来源绑定**。旧 N02-U1 基线工具只导入 1,392 条实体定名；缺少 4,857 条精确来源对应关系的独立可复核输入。

本批新增：
- [tools/n02_u1_r2_binding_stage.py](../tools/n02_u1_r2_binding_stage.py) — 从两份原始 TSV 创建新的、独立的私有 SQLite sidecar，保留源文件行号和每行原始字段。**不会打开或修改** N03 父数据库、SSF/SSFF 镜像。
- [tools/n02_u1_r2_binding_verify.py](../tools/n02_u1_r2_binding_verify.py) — 完全独立于构建模块，对两份 TSV 的 **1,392 / 4,857** 行逐条复核，并检查数据库外键、输入 SHA-256、主键及原始行信息。
- [tests/test_n02_u1_r2_binding_stage.py](../tests/test_n02_u1_r2_binding_stage.py) — 仅合成数据；模拟修改表内来源绑定、原始文件、未知实体、重号、错误中文、非法来源键和错误哈希。

## 私有数据执行示例

原始 TSV 不上传公开仓库。先核对手头源文件的真实标题行，若与默认字段名不同，使用显式字段参数，不允许程序猜测。

```bash
python tools/n02_u1_r2_binding_stage.py \
  --names "/private/统一简体中文名称.tsv" \
  --bindings "/private/工程来源定名绑定.tsv" \
  --out "/private/N02_U1_R2_BINDINGS_STAGING.sqlite" \
  --receipt "/private/N02_U1_R2_BINDINGS_RECEIPT.json"

python tools/n02_u1_r2_binding_verify.py \
  --names "/private/统一简体中文名称.tsv" \
  --bindings "/private/工程来源定名绑定.tsv" \
  --stage "/private/N02_U1_R2_BINDINGS_STAGING.sqlite" \
  --report "/private/N02_U1_R2_BINDINGS_INDEPENDENT_AUDIT.json"
```

如果绑定表的字段不同，可同时给两条命令加 `--source-column` / `--entity-column` / `--binding-name-column` 指定**真实**字段；缺少定名字段时通过实体 ID 从 R2 主表取唯一正式名称，并保留“原文件未提供名称字段”的事实。

有旧版可信 SHA-256 时，首次导入应加 `--expected-names-sha256` 和 `--expected-bindings-sha256`。输出数据库和报告都不得覆盖已有版本。输出的 `STAGED_NOT_N02_U1_PASS` 与 `VERIFIED_STAGING_NOT_N02_U1_PASS` 只证明 TSV 映射一致，**不等于 N03 原生调用关系或游戏显示已确认**。

## 必须维护的版本边界

- 用户锁定的正式定名、Guest／EVA／INCOM 字段及已批准的正文与标题不受此工具修改。
- 只有确切身份与来源 ID 的记录能绑定，不能把同名或同中文字符串自动视为同实体。
- 《机战30》《机战Y》只作外部对照证据，不能直接覆盖正式主稿。
- N08 R4 在 2026-11-20 的已登记安装来源总数为 13,526；**此数字不等于现行 68,240 条主稿全覆盖**。
- N09 R2 的 F P045 作者稿有额外修订和技术 HOLD，应与 N08 R4 的批准更正分层继承，不可因为 R2 定名早于 N09 而覆盖后续修订。
- R2 的 4,857 条属于“来源 ID → 实体”绑定，不是 4,857 个原生窗口调用或用户实测。

## 后续闭合门槛

1. 从既有私人 N08 R1 MasterData／R2 定名原包取回**真正的** `工程来源定名绑定.tsv`，验证来源身份和 SHA。
2. 在可执行的私人 SQLite 环境对 4,857 条实际绑定运行本工具，生成 `STAGING` 和独立审计。
3. 另行把 staged 映射与 N03 的 90,099 条原始 source ID 和最新 N08/N09 正文建立外键／差分关系，找出不一致、旧地址与未确认消费方。
4. 不得把当前 GitHub 合成测试等同于真实库的 `N02_U1_PASS`。

公开 GitHub 只保存通用 Python 工具、合成测试和非机密方法说明。