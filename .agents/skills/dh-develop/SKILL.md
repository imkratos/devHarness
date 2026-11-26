---
name: dh-develop
description: DevHarness develop；用于完整功能交付及状态，仅在明确调用或主控派发对应阶段时执行。
---
# develop
主控先读 `AGENTS.md`、`.harness/PROTOCOL.md`、对应 workflow JSON 和 `.harness/workflow-notes.md`。在项目根目录使用 `python3 .harness/scripts/harness.py`，具体用法见 `.harness/cli.md`。

接收原始需求、Feature 或里程碑 ID，核对项目基线；缺失时以原始请求开始或恢复 project-init，M0 获批后衔接同一请求。按业务行为变化选择 feature，恢复既有行为走 bugfix，保持外部行为的结构调整走 refactor。

1. 为每项功能关联原始需求、路线图 ID、独立 run 和 OpenSpec change；里程碑内按依赖推进。修复和重构按 workflow-notes 准备最小任务包。
2. 按 workflow 顺序分派并核实产物。feature 保留需求、适用的 UI 和最终产品人工确认。依据已批准范围处理无 UI 或相同 UI 复用，记录原批准与哈希。
3. 实施后在整合提交测试、审查及适用的验收；失败退回责任阶段并重新验证。feature 验收获批后按 archive 节点核对正式规范与归档，仅执行待完成的操作，再复盘。
4. 创建里程碑最后一个功能的 run 时声明其归属和最后功能标记，按 milestone-review 对全部功能的最终整合提交重跑里程碑验收和跨功能回归；用户确认该版本后更新路线图。
