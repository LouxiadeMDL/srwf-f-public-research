# 复算入口与本轮执行范围

所有命令只对副本或新输出目录运行；原档案、BKR和ROM只读。真实输入不随公共仓库发布，按SOURCE_CATALOG.json核对用户持有的原件。

## 已在本轮执行

完整解压原雷西查询器，使用S08内冻结JP EXEC0及TSR作为参考：

```sh
python3 selftest.py /path/to/reference/EXEC0 /path/to/reference/TSR.dec.bin
```

18项合成集成测试通过。它运行查询器和人工RAM测试，不重跑历史11项原SH-2函数夹具。

完整解压S26，使用已交付CH06—CH09四份ZIP：

```sh
python3 audit_campaign.py --source-dir /path/to/source-zips --out /path/to/new/campaign.json
python3 audit_shared_tail.py --source /path/to/S08.zip --out /path/to/new/shared.json
HVM_DATA_DIR=/path/to/source-zips python3 -m unittest -v test_readonly_audit.py
```

10项审计软件测试通过；实际普通档累计为3/4/4/4；52场景静态复算确认2,163字节归一化与root13=142E。另由独立调用原BKR解析函数核对CH02—CH09累计序列，重读P48提供的寄存器与高/低RAM。没有启动模拟器。

## A–D样本到位后的原查询器命令（本轮未执行）

```sh
python3 lecee_check.py inspect A.json --phase before --out new/A_result.json
python3 lecee_check.py inspect B.json --phase after --out new/B_result.json
python3 lecee_check.py inspect C.json --phase post_scene --out new/C_result.json
python3 lecee_check.py inspect D.json --phase reload --out new/D_result.json
python3 lecee_check.py compare A.json B.json --kind persuasion --out new/A_B.json
python3 lecee_check.py compare B.json C.json --kind continuation --out new/B_C.json
python3 lecee_check.py compare C.json D.json --kind reload --out new/C_D.json
```

每个manifest引用同一暂停时点客体高/低RAM，不可直接引用BKR或压缩即时状态。样本封存不改，报告写新目录。参考代码或D2描述不匹配时保留HOLD；不要改配置强迫通过。

## 未执行或仅历史依据

本轮A–D实测复核0组、自然游戏0次、镜像/存档写入0、F→FF继承0次。源包内原机函数、图像、历史日志只用于限定交叉参照。完整研究工具、原始输入与第三方未知许可代码不直接镜像到公共仓库；该公开包不是一个可不带原件就运行的游戏工程。
