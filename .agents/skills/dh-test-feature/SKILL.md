---
name: dh-test-feature
description: DevHarness test-feature；用于测试代码、test-report.md、证据，仅在明确调用或主控派发对应阶段时执行。
---
# test-feature
角色：qa。
先读取项目 AGENTS.md 和 .harness/PROTOCOL.md。若当前为子代理，只执行本阶段，不自行推进工作流。
## 输入
原始需求及 AC，修复或重构可使用任务包的行为依据和回归目标。test-plan 在实现前读取任务包。test-feature 读取整合后的运行版本。缺失关键输入时返回 blocked。
## 操作
1. 开发前独立规划需求覆盖和边界场景
2. 开发后运行配置的单元、集成、E2E、权限与异常测试
3. 记录整合 commit、cwd、命令、退出码、报告及缺陷，适用时留截图
4. 只操作隔离测试数据
5. 未执行标记 blocked/not-run
6. 每条 AC 对应证据。
## 输出与完成条件
test-plan 交付测试计划及适用的测试代码。test-feature 交付 test-report.md 与实测证据。核对实际产物、需求引用、版本与证据；未验证的项目必须标记。返回 status、artifacts、evidence、blockers、next_action；主控负责阶段状态。
