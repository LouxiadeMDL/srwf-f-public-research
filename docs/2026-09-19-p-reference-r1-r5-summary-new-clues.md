# SRWF F — P-R1→P-R5 总结分析与新线索发现报告

日期：2026-09-19  
项目：SS-ROM清理分析 / SRWF F  
范围：**F ONLY**  
P 线定位：**PS F 参考实验室**；Saturn F RevB 仍是 A 主线最终目标。

## 1. 总结结论

P-R1→P-R5 已按既定计划完成并整体冻结。P 线的核心价值不是制作 PS 版补丁，而是建立一套可机器验证、可复用到 Saturn 研究的方法与语义参考：

`record/storage → token/control grammar → handler/state effect → runtime trace → variable-length owner/repack → stable record ID`

最终总状态：

`P_REFERENCE_RESEARCH_PROGRAM_R1_R5 = CLOSED_THROUGH_PLANNED_P_R5_WITH_SCOPED_RESERVATIONS`

P 线不阻断 A 主线：`P_BLOCKS_A = false`。

## 2. 节点结果

| 节点 | 主要功能 | 最终状态 | 关键结果 |
| --- | --- | --- | --- |
| P-R1 | PSF token/control semantic reference | CLOSED_FOR_DECLARED_SCOPE | 建立 profile-aware token/control contract；确认 handler、operand width、terminator、dynamic injection 等；UNKNOWN 明确保留 |
| P-R2 | PSF↔SSF semantic homolog matrix | CLOSED_FOR_DECLARED_SCOPE_WITH_EXPLICIT_UNKNOWNS | 只按“语义事件↔平台实现”对照，明确禁止 opcode 数字继承 |
| P-R3 | PSF runtime token/control tracer | CLOSED_FOR_REAL_RUNTIME_TRACE_SCOPE | 真实 DuckStation CPU trace：2 完整 session、59 token、299 events、0 anomaly |
| P-R4 | PSF variable-length relocation/repack research | CLOSED_FOR_BMESS0_STRUCTURAL_VARLEN_REPACK_SCOPE_WITH_RESOURCE_RESERVATIONS | canonical BMESS0 上完成结构级变长重排算法验证；100/100 actual-source fuzz |
| P-R5 | runtime record→consumer stable-ID completion | CLOSED_FOR_DECLARED_RUNTIME_STABLE_ID_SCOPE_WITH_EVIDENCE_CLASSES | runtime source 指针反绑到 canonical SLPS 文件偏移；persistent/ephemeral ID 分层 |

最终包 SHA-256：

- P-R1: `3f3777a3367c68cc7a880c44c6ff5442e02dfb811fb073d26910a23b1a1a5262`
- P-R2: `a1b73a0b4438bba1c83c6301b92e2466250ae40768101501e3729925ee62b837`
- P-R3: `cf6ced8b9bb4073e7a5758dc8db4c8872ca866cd2466ba16a162ef659113347c`
- P-R4: `f8781b46c017518508b271548ef5eff12b0dde87cafc006576772f5ee002f3d8`
- P-R5: `fa5b7e1ab318d83288b2e84367c78016bbcb670c7683984241e49a6adf7371e6`
- P-R1→P-R5 总封板: `24ab06eb4ca69d9ee68052bf69717ee7fbe5e2e9c2be24a1162ac76a1627a77b`

## 3. 新线索发现

### 3.1 parser 不是单一全局 grammar，而是 runtime profile-aware

P-R1 最重要的新发现之一是：同一个原始字节区间在不同 parser 状态下不能用一张“全局 opcode 表”解释。

PSF token parser anchor：`0x8006FDB4`。实际 parser core 中存在 state bit3 分支：

- bit3-set / later-text profile：`00..EA` 单字节 glyph，`EB..F5` 双字节 glyph，`F6..FE` controls，`FF` terminator；
- bit3-clear profile：`F0..FF` 进入 control dispatch，而 `<F0` 走另一条 state/data path。

因此 **F0..F5 不能被全局标成 controls，也不能被全局标成 glyph leads**。这直接说明后续 SSF 研究必须先证明 parser profile/state，再解释字节语义。

### 3.2 PSF F8 是真实 runtime dynamic text injection

P-R3 实机 trace 证明 F8 不是静态猜测：F8 handler 会切换文本 source 到内部动态字符串，再重新进入正常 token/glyph 路径。

核心 runtime chain：

`F8 handler → internal source switch → normal token parser → normal glyph renderer`

真实 trace 中观察到 F8 source-switch 4 次。

这为 Saturn A 主线提供了一个重要研究模板：如果 SSF 也存在剧情变量名、数值、临时组合文本，必须寻找“动态字符串生成/切换/回到普通 renderer”的证据，而不能只扫描 SCEDATA 静态记录。

### 3.3 PSF FE 的 renderer consequence 已被真实运行闭合

P-R3 实际命中：

`FE handler → upload helper → PSYQ LoadImage 0x80109924`

真实 trace 中 upload helper 2 次，LoadImage 2 次。

这证明“control token → renderer/GPU consequence”可以通过 CPU trace 直接闭合，而不是只靠静态 call graph。

### 3.4 FF terminator 是 handler return contract，不只是字节边界

P-R3 的两个完整 session 都实际观察到：

`FF → handler → return 0xFFFFFFFF → parser exit`

因此 terminator 的机器语义是 handler-return contract，而不只是离线 parser 看到 FF 就停止。

### 3.5 真实 runtime source 可以反绑回文件偏移

P-R5 将 P-R3 的真实 parser source 指针反绑到 canonical `SLPS_017.27` 文件坐标，静态 token source 逐字节比对 22/22 一致、0 mismatch。

两个实机 session 的 source 起点分别落到：

- SLPS file offset `0x2570B`
- SLPS file offset `0x25729`

这证明“RAM pointer → executable/file offset → stable record identity”是一条可实际执行的路径。

对 A 主线的启示：未来 SSF stable ID 应优先使用 `resource + file offset/range + owner + runtime consumer + evidence class`，而不是仅保存一个瞬时 RAM 地址。

### 3.6 runtime-generated text 必须与 persistent record 分离

P-R5 将 F8 切换后的内部动态字符串标为 **ephemeral runtime ID**，没有冒充成磁盘 record。

这解决了一个长期容易混淆的问题：

- persistent record：有文件/容器/owner，可长期定位；
- ephemeral runtime record：只在某次运行中生成，必须以 session/source-switch/consumer 等信息标识。

这套分类非常适合后续 SSF 动态文本研究。

### 3.7 BMESS0 的 variable-length 问题已经从“同长度覆盖”升级为结构重排

P-R4 在 canonical PSF `BMESS0.BIN` 上重新机械解析得到：

- 384 logical slots
- 383 unique CPE spans
- 18,640 leaf references
- 15,972 referenced text records
- 55 unreferenced quoted candidates

并在真实源结构上完成：

- identity rebuild byte-identical；
- 5/5 正向 variable-length tests；
- 100/100 actual-source block-level fuzz；
- 7/7 fail-closed negative tests；
- 独立实现再次验证 pointer/alias/structure。

这说明 variable-length 不是简单“把后面的字节往后推”，而是 owner-aware：需要同时更新 leaf pointer、CPE payload size、outer relative pointer，并保持 graph、alias 和 opaque bytes 的结构约束。

但这一结论**只闭合 BMESS0 结构级研究范围**，不能自动推广到 SCEDATA、M_DEAD 或 Saturn。

### 3.8 PSF↔SSF 的有效继承单位是 semantic event，不是 opcode number

P-R2 最重要的跨平台纪律仍然有效：

`semantic event ↔ PSF implementation ↔ SSF implementation`

而不是：

`PS opcode X = SS opcode X`

目前可以跨平台借鉴的是：terminator、glyph decode、dynamic injection、renderer upload、unknown-preservation、owner/repack 等“事件模型”和验证方法；不能继承 PS 地址、MIPS handler、token number、glyph slot 或 disc layout。

## 4. 对 Saturn F RevB A 主线的直接影响

### 高优先级

1. **A runtime parser 必须 profile-aware**：任何 control schema 在升级前都要绑定 parser state/profile。
2. **动态文本必须单独追**：静态 SCEDATA/SSF 记录不代表全部屏幕文本来源。
3. **runtime gate 必须用真实执行证据**：static reachability/call graph 不能替代实机 trace。
4. **建立 SSF stable-ID registry**：从现在开始记录 resource、file range、owner、runtime consumer、evidence class。
5. **unknown controls 默认 preserve，不做语义猜测**：编码器必须允许在已声明 scope 中 roundtrip opaque/unknown data。

### 中优先级

6. **SSF variable-length 研究应按资源逐个闭合**：先证明 owner/pointer/container，再研究 reallocation；不能从 BMESS0 方法直接推断 SCEDATA。
7. **renderer consequence 要端到端验证**：token/control → state mutation → raster/work buffer → VDP2/VRAM，避免只停在函数命中。

## 5. 仍然明确保留的边界

- P-R4 没有证明 PSF 所有资源的 variable-length relocation；SCEDATA 全局变长仍未闭合。
- 没有把 P-R4 结构实验升级成“变长游戏镜像 runtime PASS”。
- PSF 的 MIPS 地址、opcode、pointer/CPE 布局、scenario ID、glyph slot、disc layout 不得继承给 Saturn。
- P-R3/P-R5 的 PS runtime closure 不会自动提升 SSF runtime status。
- P 线不进行 Unicode promotion，也不触发 WGF×YZZL alignment。

## 6. 后续使用方式

P 参考线应整体冻结，后续作为只读技术参考库使用。A 主线遇到以下问题时再回查 P：

- control width / parser profile；
- dynamic text injection；
- terminator/runtime handler contract；
- runtime tracer 设计；
- variable-length owner/repack；
- stable record ID；
- unknown-preservation 与 fail-closed validator。

不建议继续扩展新的 P-R6。下一研究资源应回到 Saturn F RevB A 主线。

## 7. 公开发布说明

本报告的 public-safe 版本只包含：结构观察、地址域、统计、哈希、状态和方法论。不会公开：

- ROM/ISO/BIN/disc track；
- CPU raw trace；
- 字体/图形资产；
- 对白 dump 或可还原商业内容；
- 旧未知 EXE/DLL；
- 私有路径、账号信息或内部工作区材料。
