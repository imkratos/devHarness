---
name: dh-review-change
description: DevHarness review-change；用于review.md，仅在明确调用或主控派发对应阶段时执行。
---
# review-change
角色：reviewer。
先读取项目 AGENTS.md 和 .harness/PROTOCOL.md。若当前为子代理，只执行本阶段，不自行推进工作流。
## 输入
需求、diff、测试证据。缺失关键输入时返回 blocked。
## 操作
1. 沿调用链审查实际实现与契约
2. 关注回归、权限、数据隔离、并发、迁移、异常及测试有效性
3. 按 P0/P1/P2/P3 输出位置、触发条件、影响、修复建议
4. 不要编辑业务代码
5. 阻断问题修复后重审。
## 输出与完成条件
review.md。核对实际产物、需求引用、版本与证据；未验证的项目必须标记。返回 status、artifacts、evidence、blockers、next_action；主控负责阶段状态。
