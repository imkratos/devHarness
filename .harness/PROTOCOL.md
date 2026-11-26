# 执行协议
## 主控
1. 先核对 Git、配置和基线。用 .harness/cli.md 中的 start 创建或接续 run。空项目从原始想法开始，只创建初始化 run。
2. 按 workflow stages 顺序执行；依赖 passed 或有经确认的不适用理由的 optional/skipped 时才启动。按角色名请求 Codex 创建子代理（如果当前客户端不支持则串行执行，独立审查不可宣称为独立）。主控直接处理用户沟通和人工审批。
3. 每次派发提供 task_id、目标、输入路径及版本、允许写入路径、验收编号、命令、输出路径、预算与禁止事项。不要把全部历史注入子代理。
4. 每个子代理结果由主控读取实际文件、检查 git diff 及证据；失败回到责任阶段，默认最多 3 次，超限 blocked。不得自己伪造用户批准。
5. 状态原子写入（临时文件后 rename），一次只允许一个主控写入同一 run；保存当前阶段、产物哈希、命令证据、阻塞与下一步。上游变化使相关下游状态和批准失效，保守地重新验证。
6. 并行开发仅在依赖完成、写范围不重叠时，使用独立 Git worktree/分支，传入绝对路径并要求确认 cwd。不能确认隔离便串行。主控审查后整合，冲突暂停，不强制覆盖。
7. 状态枚举 pending/running/awaiting_approval/passed/failed/blocked/skipped；skipped 必须有适用性理由，不得跳过必需门禁。
## 门禁
人工批准：展示具体产物与版本，等待用户明确确认，记录原文、时间、路径及哈希。需求、用户可见 UI、最终产品默认需确认。生产发布必须另行授权。
程序证据：记录实际命令、cwd、退出码、日志路径、被验证 commit；未配置命令不能宣称通过。验收需逐项 AC 与证据关联；阻断缺陷未解决不得归档。
## 外部技能
检查安装后才调用。OpenSpec explore/propose 用于需求与变更；若 propose 已有 design/tasks，只补必要细节。Superpowers writing-plans 可细化已批准任务，不再 brainstorming 重建需求；TDD、systematic-debugging、review、verification 按需使用。若上游 Skill 强制重走冲突流程，停止并解释，使用本包对应本地流程；不得假装官方兼容。OpenSpec 缺失时可做产品探索但正式变更与归档阻塞，不能假造 CLI 结果。
## 产物约定
项目级：docs/product/PROJECT.md、docs/domain/DOMAIN-MAP.md、docs/domain/GLOSSARY.md、.planning/ROADMAP.md、docs/architecture/ARCHITECTURE.md、design/DESIGN.md。
功能级：openspec/changes/<change>/ 下 proposal/specs/design/tasks（以实际 Schema 为准）；run 下 acceptance.json、tasks.json、test-report.md、review.md、acceptance-report.md、evidence/。正式业务需求只在 OpenSpec specs；验收 JSON 引用需求编号而非复制规范全文。UI 文件按 feature ID 存 design/features/<id>/。
## 风险
不执行生产部署、数据删除、外部费用操作、凭证写入或扩大权限，除非用户明确批准。角色中的只读与路径约束属于提示词约束，非独立沙箱。工作流 JSON 由主控读取并由本地 CLI 校验阶段推进。只由主控调用 CLI，子代理不直接改运行状态。

主控通过 .harness/cli.md 中的命令登记批准、执行命令和恢复状态。失败按环境、执行、代码、需求或 UI 分类回退。

执行前还须读取 .harness/workflow-notes.md，尤其 archive 等特殊节点，禁止递归调用入口。
