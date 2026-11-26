# 任务清单演示路线图

按 M0 → F1 → F2 顺序演示，每一阶段复用上一阶段的读取路径及数据文件。

- **M0 · 打通读路径**　使用 [基线规范](../openspec/specs/task-list/spec.md)。启动空库，验证 AC-M0-01 后进入 F1。
- **F1 · 录入任务**　使用 [add-task 变更](../openspec/changes/add-task/proposal.md)。验证 AC-F1-01 的刷新及重启场景后进入 F2。
- **F2 · 管理完成状态**　使用 [complete-and-filter 变更](../openspec/changes/complete-and-filter/proposal.md)。用一条已完成和一条未完成任务验证 AC-F2-01、AC-F2-02。

各阶段的浏览器命令见 [AC 映射](../acceptance.json)。演示步骤与人工确认方式见 [样例说明](../README.md)。
