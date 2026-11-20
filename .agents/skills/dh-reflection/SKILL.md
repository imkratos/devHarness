---
name: dh-reflection
description: DevHarness reflection；用于LESSONS.md、改进建议，仅在明确调用或主控派发对应阶段时执行。
---
# reflection
角色：主控。
先读取项目 AGENTS.md 和 .harness/PROTOCOL.md。若当前为子代理，只执行本阶段，不自行推进工作流。
## 输入
提交、失败记录、测试与返工。缺失关键输入时返回 blocked。
## 操作
1. 基于真实证据记录错误模式、根因、日期、来源与避免方式
2. 合并重复条目
3. 多次独立发生的经验建议升级为工程规范
4. 可程序化验证优先测试/CI
5. 不得自行放宽门禁或变更安全政策。
## 输出与完成条件
LESSONS.md、改进建议。核对实际产物、需求引用、版本与证据；未验证的项目必须标记。返回 status、artifacts、evidence、blockers、next_action；主控负责阶段状态。
