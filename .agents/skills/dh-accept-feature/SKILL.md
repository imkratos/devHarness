---
name: dh-accept-feature
description: DevHarness accept-feature；用于acceptance-report.md，仅在明确调用或主控派发对应阶段时执行。
---
# accept-feature
角色：acceptance。
先读取项目 AGENTS.md 和 .harness/PROTOCOL.md。若当前为子代理，只执行本阶段，不自行推进工作流。
## 输入
原始需求、已批准 Spec（修复时用既有行为及复现依据）、AC、适用的 UI 基线或无 UI 批准依据、整合版本的运行产品和测试报告。缺失关键输入时返回 blocked。
## 操作
1. 使用实际软件执行关键用户旅程
2. 逐条验证 AC，检查 UI 与基线、数据真实性及操作反馈
3. 记录截图、运行版本、结果 passed/failed/not-run
4. 不能启动产品则阻塞
5. 不修改测试或基线
6. 主控展示验收报告、整合版本及证据，等待用户最终确认；失败列出 AC 和责任阶段供回退。
## 输出与完成条件
acceptance-report.md。核对实际产物、需求引用、版本与证据；未验证的项目必须标记。返回 status、artifacts、evidence、blockers、next_action；主控负责阶段状态。
