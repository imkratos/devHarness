---
name: dh-project-review
description: DevHarness project-review；用于里程碑评估与风险报告，仅在明确调用或主控派发对应阶段时执行。
---
# project-review
角色：主控。
先读取项目 AGENTS.md 和 .harness/PROTOCOL.md。若当前为子代理，只执行本阶段，不自行推进工作流。
## 输入
路线图、规范、Git、各 run。缺失关键输入时返回 blocked。
## 操作
1. 核对 Feature 状态和实证，不依据勾选数量判断完成
2. 运行或检查最新集成验收
3. 列缺口、风险、技术债、下一阶段建议
4. 复盘
5. 更新 ROADMAP 前核实实际交付。
## 输出与完成条件
里程碑评估与风险报告。核对实际产物、需求引用、版本与证据；未验证的项目必须标记。返回 status、artifacts、evidence、blockers、next_action；主控负责阶段状态。
