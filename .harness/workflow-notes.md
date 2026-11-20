# 特殊节点语义
- test-plan：dh-test-feature 仅生成独立测试计划/测试代码，不要求此时全部通过；之后 test-feature 才执行正式验证。
- implementation：主控读取 tasks.json，选择 dh_frontend/dh_backend，执行 dh-implement-task；串行默认，隔离确认后最多 3 并发。
- archive：主控调用已安装的 OpenSpec sync/archive，检查正式规范实际更新，禁止递归执行 dh-develop；记录归档路径和实际 CLI 结果。
- reproduce：仅复现与定位，不实施；若改变原业务行为转 feature。
- impact-analysis：仅分析保持不变的行为与风险，不创建无必要的业务规范。
- project-init 若无 UI，主控记录不适用的设计系统并经用户同意；项目级设计确定后仍可在功能级迭代。
- 所有阶段均依赖 PROTOCOL，人工批准必须绑定选定产物哈希。测试计划与设计可以在未来执行器中并行，v1 默认顺序执行。
