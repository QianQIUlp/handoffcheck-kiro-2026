# HandoffCheck — 固定产品需求与验收规格


### 用途

接手AI任务时，不再只读上一位agent的“已完成”，而是快速检查交接清单是否附带需要的本地证据材料，并给出第一个需要补齐的任务。

灵感来自用户长期维护的canonical-state、任务交接和验证流程。**不复制任何现有项目源码、私有规范、真实聊天或数据。** 参赛版本是从零独立实现、只用合成示例的小工具。

### 非目标

不判断文件内容真假，不审计所有代码，不证明测试成功，不执行证据里写的命令，不接入真实agent聊天，不调用LLM，不修改交接数据，不联网，不做项目管理平台。不做云部署、数据库、账号系统、UI框架、监控守护进程或自动修复系统配置。

### 输入契约

UTF-8 JSON文件，schema_version=1，project为非空字符串，tasks为非空数组。每个task含唯一非空id、非空title、status（pending或done）和evidence（相对路径字符串数组）。不接受其他status；不依靠隐式类型转换。

例子（仅作为合成数据结构，不代表已通过）：

```json
{
  "schema_version": 1,
  "project": "synthetic-demo",
  "tasks": [
    {"id": "T1", "title": "Prepare a test report", "status": "done", "evidence": ["proofs/test-report.txt"]},
    {"id": "T2", "title": "Prepare usage notes", "status": "pending", "evidence": []}
  ]
}
```

`--root`指定证据根目录；缺省为manifest所在目录。仅检查列明的文件，不递归扫描整盘。路径使用相对POSIX写法；拒绝绝对路径、Windows盘符/UNC路径、反斜杠与..段。解析后不得越出根目录。证据必须是根目录内的非空普通文件；不要读取文件正文。根目录内符号链接可由实现明确选择全部拒绝，简单一致优先，不为兼容增加复杂机制。

### 结果契约

| 结果 | 条件 | 退出码 |
|---|---|---:|
| READY_TO_REVIEW | 输入有效、所有任务done且每项至少一个证据，所有列明证据文件均非空可访问 | 0 |
| NEEDS_WORK | 输入结构有效，但存在pending、done无证据、缺失/空证据文件 | 1 |
| INVALID_MANIFEST | JSON/结构不合法、重复ID、无任务、非法状态/路径或证据根无效 | 2 |

未列明的运行时IO错误归入清晰报错，不输出假READY。输出对每个任务解释原因，并按输入顺序给出第一个未准备好任务；READY时next_task=null。不得把pending与证据文件存在等同done。

提供人类可读默认输出和`--format json`；机器格式包含schema_version、project、result、task_results和next_task，排序稳定、不包含当前时间等非确定性字段。诊断去stderr；JSON stdout不混入进度文字。

参考调用（由Kiro实现并验证，不是已经存在的命令）：

```text
python handoffcheck.py examples/ready/manifest.json
python handoffcheck.py examples/missing/manifest.json --format json
python handoffcheck.py examples/invalid/manifest.json
```

### 最小交付

标准库核心、薄CLI入口、三个合成场景、普通测试与属性测试、可复用Power、所需真实 .kiro 功能配置、简短README和课程证据索引。开发依赖采用项目隔离环境中的pytest/Hypothesis。只锁实际安装验证过的版本，不在指令中猜版本号。

将核心放进可独立分发的Power脚本目录、根CLI调用同一核心，是默认最小方案。Power 在本工作区内的独立干净示例目录应无需原开发仓库和密钥即可执行自身携带的核心。

### 验收矩阵

| 检查 | 预期 |
|---|---|
| 一项done，非空证据文件存在 | READY_TO_REVIEW，退出0 |
| 任意pending | NEEDS_WORK；next_task指向首个未准备好项 |
| done但evidence为空 | NEEDS_WORK，不可错误地通过 |
| 所列证据缺失/为空 | NEEDS_WORK并指出具体项 |
| 非法JSON、重复ID、空tasks、非法status | INVALID_MANIFEST，退出2 |
| 越界/绝对/盘符/UNC/符号链接逃逸 | 拒绝，不跟随读取范围外数据 |
| 相同输入两次运行 | JSON语义相同、退出码相同 |
| 运行前后输入文件 | 字节不变；无隐式写入 |
| 从Power包独立运行 | 不依赖本机绝对路径或另一套源码 |
| 所有说明 | 都不把材料存在当作事实正确 |

### 属性测试的明确性质

确定性；符合前提的done任务没有任何证据时不可能READY；从原本READY且只有唯一证据的任务删除该证据后不可能仍READY；非法路径不成为被接受的证据。每条性质都有生成器前提，不能写成对所有任意JSON都不加条件的错误定理。

## 功能覆盖设计（不是已经得分）

| 能力 | 在本项目中真正使用的方式 | 证据 |
|---|---|---|
| Spec | 原生需求→设计→任务→核心实现 | 原生工作流、Spec和对应实现 |
| Steering | 约束只读、证据语义与简单依赖 | 实际加载及代码符合规则 |
| Hooks | 保存核心源码后触发快速测试 | 真实Hook触发结果 |
| PBT | IDE原生Correctness将性质变成测试 | 原生任务和真实执行 |
| MCP | 读取合成示例并据此检查/开发 | 实际MCP调用和结果用途 |
| Custom Agent | 专用handoff-reviewer执行一次审查 | 非默认agent的激活与真实输出 |
| Power | 安装并激活可复用检查工作流 | 实际激活，运行新示例 |
| Bonus2 | 必须按官方原题单列补齐 | 对应原题要求的全部证据 |

不按这张表猜L5–L7编号；以 docs/challenge-map.md 中已核验的官方映射计分。
