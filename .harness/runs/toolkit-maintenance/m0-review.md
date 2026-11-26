# 修复前的可运行基线

本地提交 `94ff05fc88743eceb4cec04d778a13bf04592e16` 新增项目验证配置、范围与架构文档。安装器、工作流脚本、测试与浏览器样例均沿用已复现五项缺陷的提交 `7a4eca7`。

- 在一次性项目复验发行包。首次安装 44 个文件，原样重装新增 0 个。`start` 与 `resume` 都指向 `m0-check` 的 `product-analysis` 阶段，项目静态检查成功。见 `evidence/m0-install-resume.log`。
- 在整合提交执行 `python3 -B -m unittest discover -s tests -v`，21 项全部通过。见 `evidence/m0-unit.log`。
- 在整合提交的 bootstrap 和 project-review 分别执行 `python3 -B tests/rehearse_web.py --run`，两次均返回 0，均跑通 M0、F1、F2、OpenSpec 归档及 Chrome 整合验收。浏览器演练中的批准来自测试夹具。见 `evidence/bootstrap-e2e-1e366c4aa761.log` 和 `evidence/project-review-e2e-007e9dd4c6a7.log`。

本次决定是接受以上结果作为修复前基线。五项缺陷的原始观察见 `evidence/reproduce.log`。五项修复与新增回退演练待 M1 实施及验证。
