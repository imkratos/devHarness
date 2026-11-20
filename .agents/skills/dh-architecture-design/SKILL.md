---
name: dh-architecture-design
description: DevHarness architecture-design；用于架构/变更 design、ADR、必要契约，仅在明确调用或主控派发对应阶段时执行。
---
# architecture-design
角色：architect。
先读取项目 AGENTS.md 和 .harness/PROTOCOL.md。若当前为子代理，只执行本阶段，不自行推进工作流。
## 输入
需求、领域模型、UI约束。缺失关键输入时返回 blocked。
## 操作
1. 检查技术栈、依赖及风险
2. 比较可行方案
3. 明确模块边界、API、数据模型、迁移、权限、安全、可观测性、失败恢复
4. 复杂不确定点先 spike
5. 全局 ADR 记录长期决策，功能设计引用它
6. 避免预设计未来全部字段。
## 输出与完成条件
架构/变更 design、ADR、必要契约。核对实际产物、需求引用、版本与证据；未验证的项目必须标记。返回 status、artifacts、evidence、blockers、next_action；主控负责阶段状态。
