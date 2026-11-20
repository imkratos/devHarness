---
name: dh-bootstrap
description: DevHarness bootstrap；用于可运行 M0、工程规范，仅在明确调用或主控派发对应阶段时执行。
---
# bootstrap
角色：主控/开发。
先读取项目 AGENTS.md 和 .harness/PROTOCOL.md。若当前为子代理，只执行本阶段，不自行推进工作流。
## 输入
批准架构和设计系统。缺失关键输入时返回 blocked。
## 操作
1. 按批准技术栈建立最小前后端或目标应用骨架
2. 配置启动、构建、测试、迁移与 CI
3. 建立设计组件及演示业务路径
4. 记录本地命令到 project.json
5. 从干净环境验证，不创建占位通过的测试
6. 未满足 M0 阻塞。
## 输出与完成条件
可运行 M0、工程规范。核对实际产物、需求引用、版本与证据；未验证的项目必须标记。返回 status、artifacts、evidence、blockers、next_action；主控负责阶段状态。
