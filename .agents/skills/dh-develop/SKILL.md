---
name: dh-develop
description: DevHarness develop；用于完整功能交付及状态，仅在明确调用或主控派发对应阶段时执行。
---
# develop
角色：主控。
先读取项目 AGENTS.md 和 .harness/PROTOCOL.md。若当前为子代理，只执行本阶段，不自行推进工作流。
## 输入
功能描述或里程碑 ID。缺失关键输入时返回 blocked。
## 操作
1. 选择 feature/bugfix/refactor 路由
2. 里程碑按依赖逐个运行 Feature
3. 初始化 run
4. 按 workflow 分派角色与技能，读 PROTOCOL
5. 缺少项目基线先执行 project-init
6. UI 无关时记录不适用
7. 验收失败定向回退修复
8. 通过后同步归档 OpenSpec，再更新路线图与复盘。
## 输出与完成条件
完整功能交付及状态。核对实际产物、需求引用、版本与证据；未验证的项目必须标记。返回 status、artifacts、evidence、blockers、next_action；主控负责阶段状态。
