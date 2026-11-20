---
name: dh-domain-modeling
description: DevHarness domain-modeling；用于DOMAIN-MAP.md、GLOSSARY.md，仅在明确调用或主控派发对应阶段时执行。
---
# domain-modeling
角色：product + architect。
先读取项目 AGENTS.md 和 .harness/PROTOCOL.md。若当前为子代理，只执行本阶段，不自行推进工作流。
## 输入
已确认产品目标。缺失关键输入时返回 blocked。
## 操作
1. 梳理业务能力、术语、核心实体及生命周期
2. 标注职责和依赖、跨域一致性
3. 区分业务域与部署单元
4. 列未决规则
5. 以用户旅程检查领域覆盖。
## 输出与完成条件
DOMAIN-MAP.md、GLOSSARY.md。核对实际产物、需求引用、版本与证据；未验证的项目必须标记。返回 status、artifacts、evidence、blockers、next_action；主控负责阶段状态。
