---
name: dh-project-init
description: DevHarness project-init；用于项目基线、M0计划、路线图，仅在明确调用或主控派发对应阶段时执行。
---
# project-init
角色：主控。
先读取项目 AGENTS.md 和 .harness/PROTOCOL.md。若当前为子代理，只执行本阶段，不自行推进工作流。
## 输入
产品想法、现有仓库。缺失关键输入时返回 blocked。
## 操作
1. 检查仓库和工具
2. 初始化项目配置及 run
3. 按 project-init workflow 调用产品、领域、路线图、设计系统、架构、基础工程等阶段
4. 在关键决策处暂停
5. M0 必须端到端启动与测试
6. 最后更新当前里程碑。
## 输出与完成条件
项目基线、M0计划、路线图。核对实际产物、需求引用、版本与证据；未验证的项目必须标记。返回 status、artifacts、evidence、blockers、next_action；主控负责阶段状态。
