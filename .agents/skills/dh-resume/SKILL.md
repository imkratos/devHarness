---
name: dh-resume
description: DevHarness resume；用于恢复执行或阻塞报告，仅在明确调用或主控派发对应阶段时执行。
---
# resume
角色：主控。
先读取项目 AGENTS.md 和 .harness/PROTOCOL.md。若当前为子代理，只执行本阶段，不自行推进工作流。
## 输入
run 状态、Git、证据。缺失关键输入时返回 blocked。
## 操作
1. 列出未完成 run，多个时让用户选择
2. 检查当前 Git 与状态记录、产物哈希、未合并 worktree 和审批
3. running 不视为成功
4. 从最早失效或未完成阶段恢复
5. 避免重复提交与重复归档
6. 按原 workflow 继续。
## 输出与完成条件
恢复执行或阻塞报告。核对实际产物、需求引用、版本与证据；未验证的项目必须标记。返回 status、artifacts、evidence、blockers、next_action；主控负责阶段状态。
