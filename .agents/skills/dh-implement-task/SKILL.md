---
name: dh-implement-task
description: DevHarness implement-task；用于代码、测试、commit 或 diff、证据，仅在明确调用或主控派发对应阶段时执行。
---
# implement-task
角色：frontend/backend。
先读取项目 AGENTS.md 和 .harness/PROTOCOL.md。若当前为子代理，只执行本阶段，不自行推进工作流。
## 输入
任务包、契约、设计基线。缺失关键输入时返回 blocked。
## 操作
1. 确认 cwd、分支和写范围
2. 读取相关实现与规范
3. 适用时先写失败测试并记录，再最小实现、绿色验证及回归
4. 遵守设计与安全约束
5. Bug 先复现根因
6. 调用已安装的 Superpowers TDD/debugging
7. 不得改变需求或弱化测试
8. 返回实际差异。
## 输出与完成条件
代码、测试、commit 或 diff、证据。核对实际产物、需求引用、版本与证据；未验证的项目必须标记。返回 status、artifacts、evidence、blockers、next_action；主控负责阶段状态。
