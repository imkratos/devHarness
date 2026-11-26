# task-list Specification

## Purpose

用户在本机浏览器中查看由 SQLite 保存的任务。M0 建立页面到后端的读取路径，后续变更沿用同一份清单。

## Requirements

### Requirement: REQ-M0-01 读取清单

页面 MUST 从本机服务读取清单。服务从 SQLite 返回当前任务，新库的清单为空。

#### Scenario: AC-M0-01 首次打开空清单

- **WHEN** 用户以浏览器打开使用新数据库的服务首页
- **THEN** 页面请求 `GET /api/tasks`，收到空任务数组并显示“暂无任务”
