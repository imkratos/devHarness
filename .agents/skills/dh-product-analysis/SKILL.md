---
name: dh-product-analysis
description: DevHarness product-analysis；用于产品基线或 OpenSpec 变更、验收编号，仅在明确调用或主控派发对应阶段时执行。
---
# product-analysis
角色：product。
先读取项目 AGENTS.md 和 .harness/PROTOCOL.md。若当前为子代理，只执行本阶段，不自行推进工作流。
## 输入
用户原始需求或来源、路线图条目（如有）、已有规范。缺失关键输入时返回 blocked。
## 操作
1. 识别目标用户、价值、场景、范围与非目标
2. 逐批提出影响行为的决策问题
3. 列正常、异常、权限与边界场景
4. 标出假设
5. 初始化时写 `docs/product/PROJECT.md` 草案，保留原始来源、范围和 UI 适用性，交给领域建模与 M0 规划一起评估；主控在 roadmap-planning 合并请求确认。
6. 功能变更关联原始诉求、Feature ID、OpenSpec 需求与可验证 AC，提交用户确认后再进入设计或实施。
## 输出与完成条件
产品基线或 OpenSpec 变更、验收编号。核对实际产物、需求引用、版本与证据；未验证的项目必须标记。返回 status、artifacts、evidence、blockers、next_action；主控负责阶段状态。
