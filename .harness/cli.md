# 主控操作手册

在目标项目根目录运行。下面用 `dh` 代表已安装的 CLI。CLI 输出 JSON，错误返回非零退出码。它执行 `project.json` 中由主控核对过的本地验证命令，运行前需检查命令内容与适用性。

```sh
dh() { python3 .harness/scripts/harness.py "$@"; }
dh start project-init --request '做一个团队任务清单' --run-id init-01
dh status init-01
dh begin init-01 product-analysis
dh advance init-01 product-analysis --artifact docs/product/PROJECT.md
```

## 建档及衔接

`start` 在首次运行创建项目配置、空任务和验收清单并保存原始请求。先配置已确定的项目命令，尚未建成的命令留空，到正式验证前补全。初始化未完成时从其他路线进入会返回同一个初始化 run。`status` 列出 run，`resume [RUN]` 核对产物并显示最早待处理阶段。如果存在多个未完成 run，需要明确选择。工作流快照、版本和摘要保存在 run 内，新版本工作流用于新 run。

M0 的 `roadmap-planning` 阶段一起提交产品范围、路线图草案和演示条件。主控只在用户确认后写入正式路线图。各阶段应绑定可复核的版本文件；路线图采用当次规划草案，后续进度记入正式路线图。不要把整个持续更新的路线图、共享 LESSONS.md 或运行中的 state.json 当作冻结的阶段产物。

M0 完成后主控读取原始请求，从已批准路线图取得第一个 Feature ID，关联真实 OpenSpec change。同一请求使用相同 Feature 和变更编号重试时返回原记录；换用不同请求文本会报告冲突并指出原 run。

```sh
dh start feature --request '新增任务并持久化' --feature-id F1 --change-id add-task --milestone M1 --parent-run init-01
dh start feature --request '完成并筛选任务' --feature-id F2 --change-id filter-tasks --milestone M1 --last-feature
```

按依赖执行，上例第二条用于启动最后一个功能。`--last-feature` 在工作流末尾加入整合验收。主控对照路线图核实 M1 所有 Feature 已登记。在同一整合提交验证跨功能旅程后更新里程碑。若将活动 bugfix/refactor 转为 feature，用 `--parent-run` 指向原记录，在 `--request` 中写明行为变化原因。发布子 run 后，原 run 的状态显示 `superseded`，恢复指向新 run。

## 阶段与批准

`begin RUN STAGE` 把当前阶段置为 running。每次 `advance RUN STAGE --artifact 文件` 都需要实际文件，可重复使用 `--artifact` 绑定多个产物。对于普通阶段，该命令推进到下一阶段；人工门禁会返回 `awaiting_approval`、各文件 SHA256 和 `review_token`。主控向用户展示确切产物、版本和决定，得到明确答复后执行下列命令。

```sh
dh approve RUN STAGE --token '展示时的 review_token' --reply '用户实际确认原文'
```

CLI 核对字节、令牌、时间和执行证据；用户答复是否代表同意由主控判断。一条答复涉及多个决定时，展示每个决定的文件及版本，分别登记。不同产物或提交需要相应的确认。如果路线图批准已明确覆盖无 UI 决定，可在设计阶段绑定完全相同的一组产物，提供 `--skip-reason` 并使用 `--use-approval init-01/roadmap-planning`。需要初次单独确认无 UI 时，设计阶段使用 `advance ... --skip-reason '项目通过 API 提供服务' --artifact 已展示的不适用决定文件`，然后登记用户批准。以后沿用同一决定，仍提供相同证据和理由，并传 `--use-approval init-01/design-system`。完全复用可见 UI 时同样引用原记录并提交同一批批准的文件。新的可见交互需重新展示。

## 命令证据、失败和中断

- `verify RUN STAGE KEY` 从项目根目录执行 `commands.KEY`，生成唯一日志，记录提交、命令、cwd、退出码和 SHA256。bootstrap、project-review、accept-feature、milestone-review 使用 `e2e`；test-feature 执行已配置的 `unit`、`integration`、`e2e`。CLI 与 API 的 `e2e` 可以是实际命令行或接口旅程。构建和启动步骤按项目需要放入这些验证命令。验证时需要干净的集成版本。run、路线图、OpenSpec 规范归档和复盘记录按管理资料处理，审批过的输入还会单独核验哈希。
- `plan-tasks`、`reproduce`、`impact-analysis` 结束前填写本 run 的 `tasks.json`。`inputs` 填项目内的文件路径，`write_scope` 填允许修改的文件或目录。CLI 冻结任务定义和写范围以外的输入文件内容。修改冻结依据时，恢复到最早受影响的阶段。任务 `status` 可随进展更新，结束 `implementation` 时每项均须为 `done`。升级前只记录过旧任务摘要的活动 run 会在恢复时回到任务规划、复现或影响分析阶段重新取证。
- feature 在需求确认前、bugfix 在结束复现前填写 `acceptance.json`。CLI 冻结验收编号、需求引用、场景、预期及验证方法。bugfix 清单须覆盖任务引用的全部 AC。最终验收时每个 AC 还要填写 `passed` 状态和项目相对证据路径，并至少关联一个本次 `test-feature` 或 `accept-feature` 实际生成的日志。
- `fail RUN STAGE environment --reason 原因` 保留当前阶段与次数，排除阻塞后用 `begin` 继续。代码缺陷使用 `code` 回到实施，实际阶段执行失败用 `execution`，需求、UI 范围修订分别用 `requirements`、`ui`。仅实际执行失败计数。超限后需要复核并执行 `reopen RUN STAGE --reason 处置依据`。旧证据与批准进入历史记录。
- 中断后先 `resume`。running 表示上次执行尚待核实。若已有部分产物或外部操作已完成，先检查实际文件和日志。归档时核对活动目录、唯一归档目录和正式规范；已归档时直接从归档结果恢复并绑定规范和操作证据。`resume` 从不调用外部归档。已结束的 run 作为当时集成版本的记录保存。
- v1 run 先 `status RUN` 查看需复核的旧阶段、产物和批准。主控核对原始需求、关联和现存文件后调用 `resume RUN --adopt-legacy`，必要时补 `--change-id`、`--feature-id`。旧状态完整保存在 history，迁移后的每个阶段重新取证。已有项目升级安装时，先按安装器列出的冲突手动合并，再运行工具包检查及项目检查。
