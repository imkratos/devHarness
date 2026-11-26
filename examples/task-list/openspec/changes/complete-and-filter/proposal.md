## Why

F1 能记录待办事项。用户还需要标记哪些已经做完，并单独查看剩余工作。

## What Changes

F2 增加完成状态编辑及按状态查看清单，依赖 F1 提供的任务。

## Capabilities

### Modified Capabilities

- `task-list` 增加 REQ-F2-01、REQ-F2-02。

## Impact

任务行、筛选控件、`PATCH /api/tasks/{id}` 及浏览器用例。
