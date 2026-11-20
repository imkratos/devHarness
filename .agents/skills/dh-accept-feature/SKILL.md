---
name: dh-accept-feature
description: DevHarness accept-feature；用于acceptance-report.md，仅在明确调用或主控派发对应阶段时执行。
---
# accept-feature
角色：acceptance。
先读取项目 AGENTS.md 和 .harness/PROTOCOL.md。若当前为子代理，只执行本阶段，不自行推进工作流。
## 输入
批准 Spec、UI基线、运行产品、测试报告。缺失关键输入时返回 blocked。
## 操作
1. 使用实际软件执行关键用户旅程
2. 逐条验证 AC，检查 UI 与基线、数据真实性及操作反馈
3. 记录截图、运行版本、结果 passed/failed/not-run
4. 不能启动产品则阻塞
5. 不修改测试或基线
6. 主控收集报告并等待用户最终确认。
## 输出与完成条件
acceptance-report.md。核对实际产物、需求引用、版本与证据；未验证的项目必须标记。返回 status、artifacts、evidence、blockers、next_action；主控负责阶段状态。
