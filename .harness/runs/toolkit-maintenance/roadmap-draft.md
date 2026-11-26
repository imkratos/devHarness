# DevHarness CLI 维护路线图草稿

原始请求见本 run 的 `state.json` 中的 `request`，五项问题见 `evidence/reproduce.log`。范围依据 `docs/product/PROJECT.md` 的 AC-01 至 AC-06 及 `docs/domain/` 两份领域文档。M0、M1 均无 UI，交付对象为安装器、主控 CLI 与验证记录。

## M0 · F00 复验现有工具包

主控将产品草案与本稿一并提交确认，分别绑定 SHA256。确认后，从基线 `7a4eca7` 的仓库根目录执行下列命令，在临时项目复验安装、启动、检查与恢复。五项修复留在 M1。

```sh
(
  set -ex
  git rev-parse HEAD
  sample=$(mktemp -d)
  python3 -B install.py "$sample"
  python3 -B install.py "$sample"
  cd "$sample"
  git init -q
  python3 -B .harness/scripts/harness.py start project-init --run-id m0-check --request '复验现有工具包'
  python3 -B .harness/scripts/check.py --project
  python3 -B .harness/scripts/harness.py resume m0-check
)
```

通过条件：命令均返回 0，首次安装有新增文件，第二次新增数为 0，项目检查通过，`start` 与 `resume` 均指向 `m0-check` 的 `product-analysis`。主控留存基线提交、cwd、命令、退出码及输出日志，并按项目配置运行 `python3 -B -m unittest discover -s tests -v` 和 `python3 -B tests/rehearse_web.py --run`，均须成功。浏览器演练使用已有样例，依赖 Chrome、Node.js、npm 和 OpenSpec。

## M1 · 修复与回退演练

依赖 M0 验收。以下为拟定 Feature ID 与通过条件，每项沿用产品草案的同号 AC。

- **F01 / AC-01 安装合并**　提议用可重复的 `--merged <清单相对路径>` 逐项确认，仅接受清单内的普通文件。仍有冲突时列出路径并在复制前停止；全部解决后保留合并内容、补齐缺件，以相同声明重跑新增数为 0。
- **F02 / AC-02 验收冻结**　`reproduce` 阻止空清单或任务引用缺项；补齐后冻结编号、需求引用、场景、预期与验证方法。可追加状态与证据，删项或改预期须回退复现。
- **F03 / AC-03 输入变化**　提议冻结 `inputs` 中规范与复现记录的内容哈希；授权实现源码同时出现在 `inputs` 与 `write_scope` 时，编辑后须重新测试，无须重排任务。用同路径改规范、改源码两例核对回退边界，旧依据关联的下游证据须失效。
- **F04 / AC-04 实施完成**　两项任务仅一项 `done` 时停在 `implementation` 并指出另一项；全部 `done` 且其余门禁满足后推进。
- **F05 / AC-05 请求重试**　同一请求及同一对 Feature、change 标识重试返回原 run；仅换请求应报冲突，原请求、进度及 run 数量均保持原值。
- **F06 / AC-06 回退演练**　依赖 F01–F05 整合。在隔离样例留存通过记录，提交真实源码回归，运行 `resume` 核对最早回退阶段及下游证据、批准失效；用原命令复现失败，修正后重跑通过，人工门禁重新确认。以提交差异、阶段记录及前后日志逐项验收。

本文为待确认计划。所列命令与 AC 验收均待执行。
