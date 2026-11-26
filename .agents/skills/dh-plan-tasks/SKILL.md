---
name: dh-plan-tasks
description: DevHarness plan-tasks；用于tasks.json 与必要实施步骤，仅在明确调用或主控派发对应阶段时执行。
---
# plan-tasks
角色：architect。
先读取项目 AGENTS.md 和 .harness/PROTOCOL.md。若当前为子代理，只执行本阶段，不自行推进工作流。
## 输入
已批准需求、适用的已确认或复用 UI 基线（无 UI 时引用批准依据）、经核查的技术设计。缺失关键输入时返回 blocked。
## 操作
1. 用稳定 ID、依赖、需求引用、写范围、验收命令拆任务
2. 检查无环与路径冲突，明确集成任务
3. 不要重复维护两份进度，OpenSpec tasks 与 run 任务 ID 映射
4. 简单任务合并实施，复杂任务可调用 Superpowers writing-plans 细化。
## 输出与完成条件
tasks.json 与必要实施步骤。核对实际产物、需求引用、版本与证据；未验证的项目必须标记。返回 status、artifacts、evidence、blockers、next_action；主控负责阶段状态。
