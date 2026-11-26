## Why

M0 已经可以读取任务。用户需要把待办事项录入清单并在下次打开时找回。

## What Changes

F1 增加输入框、提交按钮及持久化写入，详见本变更的规范增量。

## Capabilities

### Modified Capabilities

- `task-list` 增加 REQ-F1-01。

## Impact

网页表单、`POST /api/tasks`、SQLite 及浏览器用例。
