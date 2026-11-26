---
name: dh-project-init
description: DevHarness project-init；用于项目基线、M0计划、路线图，仅在明确调用或主控派发对应阶段时执行。
---
# project-init
主控先读 `AGENTS.md`、`.harness/PROTOCOL.md`、对应 workflow JSON 和 `.harness/workflow-notes.md`。在项目根目录使用 `python3 .harness/scripts/harness.py`，具体用法见 `.harness/cli.md`。

从用户的原始需求和现有仓库开始，检查技术栈、工具与项目配置，初始化 project-init run。

1. 保存需求来源，派发产品草案、领域模型和路线图。将产品范围和 M0 目标、Feature ID、可运行路径及验收条件一起提交用户确认。
2. 按确认范围执行设计系统门禁，只有明确批准的无 UI 依据可用于跳过。核对架构及风险后进入 bootstrap。
3. 在整合版本实际启动 M0，运行约定测试，逐项核对 M0 验收条件。向用户展示运行方式、结果、提交与证据，经最终批准后登记交付和当前里程碑。由开发请求触发的初始化须继续处理原始需求，将后续功能 run 关联到本 run。
