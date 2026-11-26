"""从工具包根目录运行，仅在测试创建的一次性项目中操作。"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / 'tests'))
from test_harness import HarnessTests, SOURCE

fixture = HarnessTests()
fixture.setUp()
try:
    merged = fixture.root / 'AGENTS.md'
    merged.write_text(merged.read_text() + '\n团队约定\n')
    result = subprocess.run([sys.executable, SOURCE / 'install.py', fixture.root], capture_output=True, text=True)
    print('AC1 安装已合并 AGENTS.md', result.returncode, result.stderr.strip())
    fixture.commit()
    fixture.init_to()
    run = 'repro'
    fixture.cli('start', 'bugfix', '--run-id', run, '--request', '恢复已记录行为')
    fixture.write('contract.md', '原契约')
    tasks = fixture.read('.harness/templates/tasks.json')
    tasks[0].update(inputs=['contract.md'], write_scope=['product.txt'], verification=['smoke.py'])
    fixture.write(f'.harness/runs/{run}/tasks.json', tasks)
    print('AC2 空验收清单结束复现，下一阶段', fixture.stage(run, 'reproduce')['next_action'])
    fixture.write('contract.md', '新契约')
    print('AC3 契约变更后恢复，下一阶段', fixture.cli('resume', run)['next_action'])
    print('AC4 唯一任务 pending 时结束实施，下一阶段', fixture.stage(run, 'implementation')['next_action'])
    ids = ['--feature-id','F1','--change-id','review']
    fixture.cli('start','feature','--request','第一个需求',*ids)
    print('AC5 同编号不同需求成功返回', fixture.cli('start','feature','--request','第二个需求',*ids)['request'])
finally:
    fixture.doCleanups()
