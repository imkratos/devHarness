# DevHarness 项目规则
主会话担任 Orchestrator。入口：$dh-project-init、$dh-develop、$dh-resume、$dh-project-review。
先读 .harness/PROTOCOL.md 和对应 workflow JSON；项目配置缺失时先初始化，不能猜测。
OpenSpec 是正式功能行为及变更的权威来源；Superpowers 仅按需承担计划、TDD、调试、审查等环节。避免重复设计及双重任务账本。
只有主控可更新运行状态、批准记录（依据用户明确答复）与路线图。子代理不得批准自己产物。所有人工批准绑定产物版本及 SHA256。
不得把测试未运行写成通过；不得改弱测试、覆盖用户变更或自动发布。并行写任务必须隔离 worktree，合并后重新验证。
读取最小必要上下文；保留现有项目技术栈与规则。遇到冲突先报告。用户明确要求的非研发任务无需启动完整工作流。
