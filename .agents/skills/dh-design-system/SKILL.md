---
name: dh-design-system
description: DevHarness design-system；用于design/DESIGN.md、tokens.json、基础原型，仅在明确调用或主控派发对应阶段时执行。
---
# design-system
角色：designer。
先读取项目 AGENTS.md 和 .harness/PROTOCOL.md。若当前为子代理，只执行本阶段，不自行推进工作流。
## 输入
已确认的产品和 M0 范围、用户场景。有 UI 时执行本阶段；已明确批准无 UI 时主控按 `.harness/workflow-notes.md` 记录跳过依据，复用相同 UI 时核对原批准和基线哈希。缺失关键输入时返回 blocked。
## 操作
1. 先明确视觉方向、导航与信息架构
2. 定义色彩、字体、间距、组件、响应式与无障碍
3. 实现可运行的关键页面原型及截图
4. 至少比较两种有意义的视觉方向，说明选择
5. 人工批准后保存基线。
## 输出与完成条件
design/DESIGN.md、tokens.json、基础原型。核对实际产物、需求引用、版本与证据；未验证的项目必须标记。返回 status、artifacts、evidence、blockers、next_action；主控负责阶段状态。
