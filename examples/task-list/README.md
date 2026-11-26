# 任务清单

用一个页面、一个 Python 标准库 HTTP 服务和一个 SQLite 文件演示 M0 → F1 → F2。默认启动 F2，包含新增、完成与筛选。运行服务只需 Python 3.11+，在本目录执行：

```sh
python3 server.py
```

浏览器打开终端打印的地址，默认是 `http://127.0.0.1:8000`。任务保存在当前目录的 `data/tasks.sqlite3`。按 Ctrl-C 停止，使用同一路径重新启动即可延续清单。端口被占用时用 `--port 0` 让系统分配端口。

## 自动化验证

在本目录准备 Node.js 22.20+、npm 和 Google Chrome，并使 `python3` 可用。首次安装测试依赖需要访问 npm 仓库。Playwright 默认启动本机 Chrome。若使用其他 Chromium 安装位置，将 `CHROME_BIN` 设为浏览器可执行文件的绝对路径。

```sh
npm ci
npm run e2e -- M0
npm run e2e -- F1
npm run e2e -- F2
```

每条命令创建独立临时数据库、分配本机端口并启动无头浏览器，退出时关闭服务并清理数据库。测试通过页面操作，也检查实际 HTTP 响应。后续阶段会重跑前序 AC；F1、F2 均在测试中重启 Python 服务。终端逐项输出 `PASS AC-…`，断言失败会以非零码退出。需求编号、规范位置和命令见 [acceptance.json](acceptance.json)。

以下命令在样例根目录用固定版本的 OpenSpec CLI 校验正式基线和两个待演练变更。预期列出 `spec/task-list`、`change/add-task` 和 `change/complete-and-filter` 三项。

```sh
npx --yes --package=@fission-ai/openspec@1.2.0 openspec validate --all --strict --no-interactive
```

## 在临时副本分阶段演练

从包含本样例的仓库根目录导出已提交版本。副本从空库开始，三个阶段均在同一目录启动。`--stage` 同时控制页面功能与后端写接口。

```sh
demo=$(mktemp -d)
git archive HEAD examples/task-list | tar -x -C "$demo"
cd "$demo/examples/task-list"
python3 server.py --stage M0
```

1. **M0**　打开终端打印的地址。应看到“暂无任务”，开发者工具的网络面板中应有成功的 `GET /api/tasks`。按 Ctrl-C 停止服务。
2. **F1**　运行 `python3 server.py --stage F1`，刷新页面。新增“购买牛奶”和“整理书架”，刷新并确认两条都在。按 Ctrl-C 停止服务，保留数据库。
3. **F2**　运行 `python3 server.py --stage F2`，刷新页面。勾选“购买牛奶”并刷新。“已完成”应只显示牛奶，“未完成”应只显示书架，“全部”应显示两条。结束时按 Ctrl-C。

[演示路线图](.planning/ROADMAP.md) 给出阶段依赖。以上浏览器操作供真人演练；`--stage` 运行的是随样例交付的代码。若同时演练 DevHarness 的需求、界面和最终产品确认，由主控在临时副本中展示相应产物，等参与者逐项明确答复后记录原文、时间、产物路径、版本和 SHA256。自动测试日志只作为程序证据。样例保留 F1、F2 的 OpenSpec 变更，供参与者检查或在完成相应门禁后在副本中归档。
