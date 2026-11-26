# M0 工具包架构

源码基线 `7a4eca7`。本次维护本地 Python CLI，无 UI。M0 复验现有工具包，M1 范围见 [产品草案](../product/PROJECT.md) 与 [已确认的规划快照](../../.harness/runs/toolkit-maintenance/roadmap-draft.md)。

- **安装器 `install.py`** 以 `install-manifest.txt` 界定发行文件，复制前检查目标冲突和符号链接。相同文件可重装，内容不同则停止；复制异常时仅清理本次创建的文件和目录。
- **静态检查 `check.py`** 校验技能、角色、工作流依赖、模板及项目配置。`--require-command` 检查指定命令是否已配置，实际执行由 `harness.py verify` 负责。
- **主控 CLI `harness.py`** 创建 run 时固定工作流快照，在 `.harness/runs/<id>/state.json` 保存原始请求、阶段、批准和历史。文件锁协调写入，临时文件经 `os.replace` 替换状态文件。
- **门禁 `gate.py`** 读取 `tasks.json` 和 `acceptance.json`，计算任务与验收定义摘要。验证证据时核对配置命令、退出码、日志 SHA256 与被测 Git 版本；逐项验收还须关联当前测试或验收日志。
- **信任边界** 主控核实 `.harness/project.json` 的命令后，`verify` 在项目根目录以当前用户权限调用 shell。代理的 `write_scope` 属于派工约束。产物哈希绑定文件内容，人工批准由主控依据用户答复登记。

## M1 兼容与恢复核对

- 对 v1 或缺版本的 run，保留 `status` 只读查看和 `resume --adopt-legacy` 显式接管。旧状态进入 `history`，阶段从头复核；旧 feature 缺关联标识时应允许补齐后重试。
- 对升级前已开始的 v2 run，现有 `task_hash` 只覆盖任务字段，`bugfix` 也可能缺少验收摘要。M1 应用旧样本核对：缺少新基线时回到最早能重新冻结依据的阶段，保留旧证据、批准与重试次数，重新取证并确认；禁止用当前文件反推历史哈希。
- 用两个样本分别修改冻结的规范和 `write_scope` 内的源码，核对前者触发重新规划、后者触发重新测试。另验已完成 run 保留历史结果、已转换 run 恢复时仍指向后继 run。

已有测试：`tests/test_checks.py` 覆盖安装冲突、复制回滚和配置检查；`tests/test_harness.py` 覆盖锁、审批失效、旧 run 接管与转换；`tests/rehearse_web.py` 在隔离样例演练集成交付。本阶段仅核对源码，未运行测试或迁移演练。
