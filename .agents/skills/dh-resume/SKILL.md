---
name: dh-resume
description: DevHarness resume；用于恢复执行或阻塞报告，仅在明确调用或主控派发对应阶段时执行。
---
# resume
主控先读 `AGENTS.md`、`.harness/PROTOCOL.md`、对应 workflow JSON 和 `.harness/workflow-notes.md`。在项目根目录使用 `python3 .harness/scripts/harness.py`，具体用法见 `.harness/cli.md`。

定位未完成 run，多个候选且未指定 ID 时让用户选择。

1. 核对原 workflow 版本、Git 提交、未整合 worktree、输入和产物 SHA256、批准与命令证据。旧 run 或缺少版本时先只读报告差异，按 workflow-notes 显式接管，保留原记录并逐阶段复核。
2. `running` 需核实实际副作用。上游已变化时记录原因，使受影响的下游状态、批准、跳过依据和测试证据失效，从最早需重做的阶段恢复。
3. `awaiting_approval` 展示当前产物等待明确答复。重试前检查已有提交、正式规范和归档，复用已核实的结果；证据冲突或达到重试上限时报告 `blocked` 和下一步。
