---
name: dh-roadmap-planning
description: DevHarness roadmap-planning；用于ROADMAP.md，仅在明确调用或主控派发对应阶段时执行。
---
# roadmap-planning
角色：architect。
先读取项目 AGENTS.md 和 .harness/PROTOCOL.md。若当前为子代理，只执行本阶段，不自行推进工作流。
## 输入
原始需求、产品草案、业务域。缺失关键输入时返回 blocked。
## 操作
1. 按可交付业务能力拆 M0/M1 等里程碑，每个含目标、非目标、依赖、Feature ID、真实验收条件
2. 只详细规划当前里程碑
3. 记录风险与验证性技术 spike
4. 逐项关联原始需求、业务能力和里程碑。向主控交付路线图草稿，由主控展示产品草案和 M0 规划（含 UI 范围），请求一次明确确认并分别绑定两份产物的哈希。
## 输出与完成条件
路线图草稿供主控更新 `.planning/ROADMAP.md`。核对实际产物、需求引用、版本与证据；未验证的项目必须标记。返回 status、artifacts、evidence、blockers、next_action；主控负责阶段状态。
