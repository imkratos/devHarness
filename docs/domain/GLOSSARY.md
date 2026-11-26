# DevHarness CLI 术语表

- **安装清单与冲突（AC-01）**　`install-manifest.txt` 列出随包交付的路径，`install.py` 用 `conflicts` 收集妨碍安全复制的路径。缺件须补齐，手工合并的文件由维护者确认保留。
- **运行（AC-05）**　run 是主控推进和恢复一次请求的记录。`request` 保存原始请求，`feature_id`、`change_id` 分别标识功能和规范变更。
- **验收定义（AC-02）**　`acceptance.json` 的 `id`、`requirement_ref`、`scenario`、`expected`、`verification` 分别表示编号、需求引用、场景、预期和验证方法。`status`、`evidence` 记录后续验证结果。
- **任务依据与写范围（AC-03）**　`tasks.json` 的 `inputs` 列出读取路径，`write_scope` 列出授权写入范围。规范和复现记录按内容识别版本，授权源码以修改后的版本接受测试。
- **实施任务（AC-02、AC-04）**　`depends_on` 引用前置任务，`acceptance` 引用验收编号，`status` 为 `done` 表示该任务已完成。阶段推进须检查整份任务清单。
- **命令证据（AC-03、AC-06）**　`command`、`cwd`、`exit_code` 记录怎样执行及其结果，`commit` 标识被测提交，`log` 和 `sha256` 定位并校验日志。
- **恢复与批准（AC-06）**　`resume` 核对当前版本与阶段记录。失效的命令记录保留作历史证据；人工批准绑定产物版本和 SHA256，由用户重新确认、主控登记。
