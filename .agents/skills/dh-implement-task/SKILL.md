---
name: dh-implement-task
description: DevHarness implement-task；用于代码、测试、commit 或 diff、证据，仅在明确调用或主控派发对应阶段时执行。
---
# implement-task
角色：frontend/backend。
先读取项目 AGENTS.md 和 .harness/PROTOCOL.md。若当前为子代理，只执行本阶段，不自行推进工作流。
## 输入
feature 读取派发任务、契约及适用的 UI 基线。bugfix/refactor 的 implementation 读取 首阶段生成的 `tasks.json` 最小任务包及复现或影响分析证据；reproduce 读取故障描述和预期行为依据。缺失关键输入时返回 blocked。
## 操作
1. 确认 cwd、分支和写范围
2. 读取相关实现与规范
3. implementation 适用时先写失败测试并记录，再最小实现、绿色验证及回归
4. 遵守设计与安全约束
5. reproduce 仅产出复现步骤、失败证据及定位，交由主控据此填写最小 `tasks.json` 和验收条件，在 implementation 才修改实现
6. 按需使用已安装的 Superpowers TDD/debugging
7. 不得改变需求或弱化测试
8. 返回实际差异。
## 输出与完成条件
reproduce 交付复现证据，implementation 交付代码、测试、commit 或 diff 及验证记录。核对实际产物、需求引用、版本与证据；未验证的项目必须标记。返回 status、artifacts、evidence、blockers、next_action；主控负责阶段状态。
