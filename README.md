# DevHarness v1.0 中文手册
这是项目级 Codex Skills 工具包，非独立运行时或官方插件。`dh-` 前缀避免与其他框架冲突。
## 安装
需要 Git、Python 3.11+（安装和检查脚本）、支持自定义 Agent 的 Codex。新建或进入项目后执行：
```bash
python3 /path/to/DevHarness-v1/install.py /path/to/project
cd /path/to/project
git init # 仅新仓库需要
npm install -g @fission-ai/openspec@latest
openspec init --tools codex
```
Codex 内输入 `/plugins` 安装 Superpowers；重启会话并确认 Skills 可发现，项目级自定义 Agent 可用。已有 AGENTS.md 或同名配置时安装器会拒绝覆盖，先人工合并再重新运行。不会自动安装依赖、修改全局配置或部署。
## 使用
在项目根目录启动 Codex：
- `$dh-project-init 我要开发……，先与我讨论产品定位和 MVP。` 新项目从产品探索开始，确认后建立全局架构、设计系统与 M0。
- `$dh-develop M1` 依赖顺序开发里程碑内 Feature；每个 Feature 单独有 run 与变更。
- `$dh-develop 新增模板版本管理` 新功能；`$dh-develop 修复模板上传失败` 自动判断是否改变已有行为。
- `$dh-resume` 恢复，多个未完 run 时指定 ID。
- `$dh-project-review` 检查里程碑。
- `$dh-ui-design` 等可单独人工调用；单独调用不意味着其他阶段自动完成。
## Agent / Skill
主会话是主控，不需要专门启动主控子代理。八个 `.codex/agents/dh_*.toml` 是专业角色。主控明确要求按对应角色执行某 Skill，传入任务包；无需手工打开八个终端。角色配置不是安全边界，继承父会话权限。若客户端不支持自定义子代理，串行降级且不得冒充独立审查。
## 状态与工作流
`.harness/workflows/*.json` 为自然语言主控读取的声明式约定，不会自动执行。`.harness/workflow-notes.md` 定义特殊节点。主控从 example 复制 project.json，实际项目命令必须经验证；从 templates 初始化 run 文件。`python3 .harness/scripts/check.py` 检查配置格式及工作流依赖，不证明业务测试通过。
## 与外部框架的边界
OpenSpec 维护业务规范；Superpowers 提供工程方法。不要重复启动两套完整流程；如 Skill 约束冲突，报告并采用本地对应流程。外部框架未打包，需自行安装。没有可运行浏览器或测试环境则相应验证阻塞。
## 示例任务包
```json
{"task_id":"TASK-001","skill":"dh-implement-task","agent":"dh_backend","inputs":["openspec/changes/example/design.md"],"write_scope":["backend/src/"],"requirements":["REQ-001"],"acceptance":["AC-001"],"verification":["项目实际测试命令"],"worktree":"主控填写实际绝对路径"}
```
## 来源
- https://developers.openai.com/codex/subagents
- https://developers.openai.com/codex/skills
- https://github.com/Fission-AI/OpenSpec
- https://github.com/obra/superpowers
## 限制
本版本为可安装的指令型工具包，未提供确定性状态机、强制文件权限隔离、自动持续执行、生产发布或现成业务代码。需以真实项目验证 Codex 执行效果。
