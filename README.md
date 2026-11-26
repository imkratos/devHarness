# DevHarness v2 中文手册
项目级技能、专业角色和本地 Python CLI 共同管理开发流程。`dh-` 前缀避免与其他框架冲突。
## 安装

需要 Git、Python 3.11+（安装、检查和运行状态 CLI）以及支持自定义 Agent 的 Codex。

### 1. 安装 DevHarness

将示例路径替换为 DevHarness 所在目录和目标项目目录，在终端运行。

```bash
python3 /path/to/devHarness/install.py /path/to/project
cd /path/to/project
git init # 仅新仓库需要
```

已有同名文件且内容不同时，安装器会在复制前列出冲突。手工合并后，用 `--merged` 指明要保留的清单相对路径，其余缺失文件会正常安装。例如：

```bash
python3 /path/to/devHarness/install.py /path/to/project --merged AGENTS.md
```

每个已合并文件各写一个 `--merged`，重复安装时沿用相同参数。

### 2. 安装并初始化 OpenSpec

npm 安装方式需要 Node.js 22.20.0 或更高版本。CLI 全局安装一次。

```bash
npm install -g @fission-ai/openspec@latest
openspec --version
```

在每个目标项目根目录初始化。这里使用 `--scope project`，将 Codex 技能放在项目的 `.agents/skills/` 下。

```bash
cd /path/to/project
openspec init --tools codex --scope project
openspec list
```

初始化后会生成 `openspec/`。新项目运行 `openspec list` 时通常还没有变更。详见 [OpenSpec 安装文档](https://github.com/Fission-AI/OpenSpec#quick-start)。

### 3. 安装 Superpowers

在支持 `codex plugin add` 的 Codex CLI 中，可以直接在终端安装。先查询当前插件市场返回的插件 ID，再用它安装。下面以 `superpowers@openai-api-curated` 为例。

```bash
codex plugin list --available --json | grep '"pluginId".*superpowers@'
codex plugin add superpowers@openai-api-curated
codex plugin list
```

也可以在终端运行 `codex`，进入会话后输入 `/plugins`，搜索 `superpowers` 并选择 **Install Plugin**。Codex 桌面端可在侧边栏的 **Plugins** 中搜索并安装。详见 [Superpowers 安装文档](https://github.com/obra/superpowers#codex-cli)。

安装完成后，在目标项目根目录启动新的 Codex 会话。在 CLI 中输入 `$` 打开技能列表，确认能找到 `openspec-propose` 和 Superpowers 的 `test-driven-development`。

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
主控读工作流、与用户讨论并派工。本地 CLI 保存 run、检查依赖、执行配置的测试并记录批准。首次从 `$dh-develop` 进入会先建立初始化 run；恢复时继续使用同一份请求和工作流快照。产品范围与 M0 路线图一次展示，可见 UI 和可运行结果分别确认。

```bash
python3 .harness/scripts/check.py
python3 .harness/scripts/harness.py start project-init --request '做一个团队任务清单'
python3 .harness/scripts/harness.py status
python3 .harness/scripts/check.py --project
```

主控操作和升级规则见 [.harness/cli.md](.harness/cli.md)。仓库中的 [全栈任务清单样例](examples/task-list/) 可单独运行，包含 M0、创建任务和完成筛选三段浏览器验证。安装器只分发清单列出的工具包文件。

## 与外部框架的边界
OpenSpec 维护业务规范；Superpowers 提供工程方法。不要重复启动两套完整流程；如 Skill 约束冲突，报告并采用本地对应流程。外部框架未打包，需自行安装。没有可运行浏览器或测试环境则相应验证阻塞。
## 示例任务包
```json
{"task_id":"TASK-001","skill":"dh-implement-task","agent":"dh_backend","inputs":["openspec/changes/example/design.md"],"write_scope":["backend/src/"],"requirements":["REQ-001"],"acceptance":["AC-001"],"verification":["项目实际测试命令"],"worktree":"主控填写实际绝对路径"}
```
## 验证 DevHarness 本身

在工具包仓库根目录执行 `python3 -B -m unittest discover -s tests -v`。需要验证整条交付路径时，在有 Chrome、Node.js 和 npm 的机器执行 `python3 tests/rehearse_web.py --run --keep`。演练从临时目录安装发行清单，用真实浏览器和 OpenSpec 验证 M0 与两个 Feature，保留命令、日志和最终状态。自动输入的批准只存在于标有 `synthetic-test` 的测试夹具中。真人演练按 [样例说明](examples/task-list/README.md) 操作。

## 来源
- https://developers.openai.com/codex/subagents
- https://developers.openai.com/codex/skills
- https://github.com/Fission-AI/OpenSpec
- https://github.com/obra/superpowers
## 限制
CLI 在本地文件系统上串行写入同一 run。主控负责判断需求和用户答复、核实证据内容、调用实际工具并整合工作。可执行命令来自目标项目配置，运行前由主控核实。生产发布单独授权。
