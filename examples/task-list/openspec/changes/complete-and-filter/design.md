## Decisions

以 SQLite 中的任务 ID 标识行。复选框向 `PATCH /api/tasks/{id}` 发送布尔字段 `done`，服务提交后响应。网页对已读取的清单按状态筛选，切换视图无需改写数据库。
