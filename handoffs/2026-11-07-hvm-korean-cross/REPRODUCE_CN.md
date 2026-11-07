# 复算说明

Python 3.10+，发布脚本仅依赖标准库。全套原函数复算另外依赖未随仓库分发的旧限定SH-2执行器和原版F输入；二者可从复算者已经持有的`HVM04B_H02_Semantics_20261018.zip`读取。哈希与固定成员名写在`prepare_input.py`，不接受同名异版输入。

在本目录运行，以下路径均由复算者替换：

```sh
python -B prepare_input.py --archive /path/to/HVM04B_H02_Semantics_20261018.zip
python -B cross_probe.py --out .local_results/run1.json
python -B cross_probe.py --out .local_results/run2.json
python -B validate_probes.py .local_results/run1.json
python -B validate_probes.py .local_results/run2.json
python -B root11_probe.py --archive /path/to/HVM04B_H02_Semantics_20261018.zip --out .local_results/root11.json
python -B -m unittest -v test_public_tools.py
```

输入准备先检查两项SHA，再写`.local_inputs/EXEC0.bin`及`.local_inputs/vendor/sh2_subset.py`；源ZIP不变，已有不同字节会拒绝覆盖。`cross_probe.py`验证执行器和EXEC身份，原函数写入仅作用于新建合成内存，不连接模拟器、不编辑保存卡。所有探针输出必须放入新文件，且位于被忽略的`.local_results/`。

公开结果不含指令字转储或完整栈写日志。它保留每案指令数、返回值、谓词、数值结果、轨迹摘要和必要的合成低RAM写入事实。`validate_probes.py`既检查19项预定结果，也比较冻结摘要；这只是结果验证，不是另一个独立CPU实现。

`root11_probe.py`对P12/P30/P47核对完整SHA、相对root指针和六个EB.01/F0条件，重算后继Flag查询地址。输出不含场景原字；它不证明这些路径在自然游戏中已全部执行。

旧执行器故意保留为对齐负例。StrictMemory只拒绝word/long未对齐访问，不实现硬件异常向量；CrossCPU只补充本研究需要的三种CPU操作，不用自写游戏callee替代原函数。不能称为完整Saturn模拟器。

不具备私有输入时，可单独运行`validate_probes.py PROBES_SUMMARY.json`及9项工具回归，核对公开结果与工具，但这**不等于重新执行原游戏函数**。

发布版从研究包中删去重复结果副本、场景原字窗口、全量合成栈写入日志与旧执行器源码。报告使用公开可读重述，结论及未验证范围保留。不要上传`.local_inputs/`或`.local_results/`，不要用强制添加绕过忽略规则。
