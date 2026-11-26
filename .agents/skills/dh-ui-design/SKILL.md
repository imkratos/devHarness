---
name: dh-ui-design
description: DevHarness ui-design；用于原型、交互规范、截图基线，仅在明确调用或主控派发对应阶段时执行。
---
# ui-design
角色：designer。
先读取项目 AGENTS.md 和 .harness/PROTOCOL.md。若当前为子代理，只执行本阶段，不自行推进工作流。
## 输入
已批准 Spec、适用的设计系统及已有 UI 基线。按 workflow-notes 核对已批准无 UI 或完全相同 UI 的复用条件。缺失关键输入时返回 blocked。
## 操作
1. 按用户旅程设计页面及所有关键状态
2. 复用组件与 tokens
3. 用明确标记的模拟数据做可运行原型
4. 通过浏览器检查布局、键盘、响应式与关键操作
5. 记录截图条件
6. 将可运行原型、交互状态及截图提交用户确认后冻结基线。复用时关联可覆盖本次需求的原批准、版本和 SHA256。
## 输出与完成条件
原型、交互规范、截图基线。核对实际产物、需求引用、版本与证据；未验证的项目必须标记。返回 status、artifacts、evidence、blockers、next_action；主控负责阶段状态。
