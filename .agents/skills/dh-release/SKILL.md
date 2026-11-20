---
name: dh-release
description: DevHarness release；用于构建及发布候选证据，仅在明确调用或主控派发对应阶段时执行。
---
# release
角色：主控。
先读取项目 AGENTS.md 和 .harness/PROTOCOL.md。若当前为子代理，只执行本阶段，不自行推进工作流。
## 输入
已通过验收的 commit。缺失关键输入时返回 blocked。
## 操作
1. 生成版本变更摘要，运行配置构建及冒烟测试
2. 检查迁移、回滚、配置和秘密
3. 只构建本地候选，实际部署/推送/发布须另获授权
4. 记录产物哈希及环境。
## 输出与完成条件
构建及发布候选证据。核对实际产物、需求引用、版本与证据；未验证的项目必须标记。返回 status、artifacts、evidence、blockers、next_action；主控负责阶段状态。
