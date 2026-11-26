---
name: dh-project-review
description: DevHarness project-review；用于里程碑评估与风险报告，仅在明确调用或主控派发对应阶段时执行。
---
# project-review
主控先读 `AGENTS.md`、`.harness/PROTOCOL.md`、对应 workflow JSON 和 `.harness/workflow-notes.md`。在项目根目录使用 `python3 .harness/scripts/harness.py`，具体用法见 `.harness/cli.md`。

读取原始目标、已确认路线图、规范、各 run 的批准和证据，定位实际整合提交。

1. M0 的 project-review 检查真实启动、端到端路径与测试，向用户展示逐项结果、证据和版本，取得最终批准。
2. 评估功能里程碑时核对依赖、归档与各 feature 的交付，在最终 milestone 提交重新验证集成旅程、回归和里程碑验收条件。记录命令、提交、退出码及证据。最后一个功能 run 的 milestone-review 需展示整合结果并取得用户最终批准。
3. 报告缺口、风险和下一步。失败项回退至责任阶段，重新整合验证；主控仅在对应门禁和证据齐备后更新路线图。
