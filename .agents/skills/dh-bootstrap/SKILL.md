---
name: dh-bootstrap
description: DevHarness bootstrap；用于可运行 M0、工程规范，仅在明确调用或主控派发对应阶段时执行。
---
# bootstrap
角色：主控/开发。
先读取项目 AGENTS.md 和 .harness/PROTOCOL.md。若当前为子代理，只执行本阶段，不自行推进工作流。
## 输入
已批准的产品和 M0 规划、经主控核查的架构，以及已批准的设计系统或无 UI 依据。缺失关键输入时返回 blocked。
## 操作
1. 按批准技术栈建立最小前后端或目标应用骨架
2. 配置启动、构建、测试、迁移与 CI
3. 跑通 M0 业务路径；有 UI 时建立设计组件
4. 记录本地命令到 project.json
5. 从干净环境实际启动并运行测试，交付命令、提交和日志供 M0 最终验收
6. 未满足 M0 阻塞。
## 输出与完成条件
可运行 M0、工程规范。核对实际产物、需求引用、版本与证据；未验证的项目必须标记。返回 status、artifacts、evidence、blockers、next_action；主控负责阶段状态。
