# WP/YZZL F — SCEDATA[71] 提取工具

用途：为“逆向 WP 第二阶段 / 第28话 C-D-E”提取当前缺少的目标剧情块。

- C：两个塞蒂的互斥 guard
- D：塞蒂1的等级/困难模式门槛
- E：塞蒂1 → 法提玛3 的具体掉落记录/字段

## 使用

1. 下载本目录的 extract_wp_scedata71.py 和 01_EXTRACT_WP_SCEDATA71.cmd，放在同一目录。
2. 双击 01_EXTRACT_WP_SCEDATA71.cmd。
3. 选择 WP/YZZL F 的 SRWF.BIN、对应 CUE，或者已经提取好的 SCEDATA.BIN。
4. 等待窗口显示 PASS_WP_TARGET_SCEDATA71。
5. 把 OUTPUT 目录中生成的 WP_F_SCEDATA71_EXTRACTION_PASS_*.zip 上传回 ChatGPT。

也可以把 BIN/CUE/SCEDATA.BIN 直接拖到 CMD 上。

## 自动验证的目标身份

WP/YZZL F SCEDATA.BIN：

- size = 579071
- directory entries = 80

SCEDATA[71]：

- compressed range = [524800, 532910)
- decompressed size = 13236
- SHA-256 = bf35b4e83f5608993e4b8ad8c46792c6dfc12dbb82ee186b308134537bb602ec

只有全部满足时才输出 PASS 文件名。

## 输出

ZIP 内包含：

- SCEDATA.BIN
- SCEDATA_071_COMPRESSED.bin
- SCEDATA_071_DECOMP.bin
- YZZL_71.bin
- SCEDATA_071_HEADER112.bin
- SCEDATA_071_HEADER_POINTERS.json
- EXTRACTION_REPORT.json
- SHA256SUMS.txt

## 安全边界

- 纯 Python 源码，无 EXE。
- 不运行历史 WP/YZZL 补丁 EXE。
- 不修改输入 ROM/BIN。
- 不生成或应用游戏补丁。
- 只读提取。
- DIC 解码器修正了历史 dic-dec.c 的 extended length 256 -> uint8_t 0 问题。

如果显示 CHECK_REQUIRED_NOT_EXACT_WP_TARGET，不要修改文件；把生成的 CHECK_REQUIRED ZIP 和命令窗口截图一起发回来即可。
