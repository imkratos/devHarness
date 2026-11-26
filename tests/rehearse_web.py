"""在一次性 synthetic-test 项目中演练 DevHarness CLI、OpenSpec 及 Chrome。

整合后的仓库：python3 tests/rehearse_web.py --run --keep
需要 Git、Python 3.11+、npm 和 Chrome。OpenSpec 默认使用样例固定的 npx 版本，
也可用 --openspec FILE 指定已安装的 CLI。失败保留临时项目与命令日志。
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile


REPO = Path(__file__).resolve().parents[1]
BASELINE = 'openspec/specs/task-list/spec.md'
PRODUCT = 'docs/product/PROJECT.md'
MARKER = 'synthetic-test'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def check(condition, message):
    if not condition:
        raise RuntimeError(message)


class Rehearsal:
    def __init__(self, root, openspec):
        self.root = root
        self.openspec = [openspec] if openspec else ['npx', '--yes', '--package=@fission-ai/openspec@1.2.0', 'openspec']

    def command(self, *args):
        result = subprocess.run(args, cwd=self.root, encoding='utf-8', capture_output=True)
        line = shlex.join(map(str, args))
        with (self.root.parent / 'commands.log').open('a', encoding='utf-8') as log:
            log.write(f'$ {line}\n{result.stdout}{result.stderr}\nexit={result.returncode}\n')
        check(result.returncode == 0, f'{line}\n{result.stdout}{result.stderr}')
        return result.stdout

    def cli(self, *args):
        return json.loads(self.command(sys.executable, '.harness/scripts/harness.py', *args))

    def setup(self):
        subprocess.run([sys.executable, REPO / 'install.py', self.root], check=True)
        skip = shutil.ignore_patterns('node_modules', 'data', '__pycache__', '.DS_Store', '.git')
        shutil.copytree(REPO / 'examples/task-list', self.root, dirs_exist_ok=True, ignore=skip)
        (self.root / PRODUCT).parent.mkdir(parents=True)
        (self.root / PRODUCT).write_text('# synthetic-test 任务清单范围\n\n' +
                                         (self.root / '.planning/ROADMAP.md').read_text(encoding='utf-8'), encoding='utf-8')
        self.command('git', 'init', '-q')
        for key, value in [('user.name', MARKER), ('user.email', 'fixture@example.invalid'), ('commit.gpgsign', 'false')]:
            self.command('git', 'config', key, value)
        with (self.root / '.git/info/exclude').open('a') as f:
            f.write('\n/.harness/runs/\n')
        self.command('npm', 'ci')
        self.command(*self.openspec, 'validate', '--all', '--strict', '--no-interactive')

    def commit(self, message):
        self.command('git', 'add', '-A')
        self.command('git', 'commit', '-qm', f'{MARKER} {message}')

    def configure(self, phase):
        path = self.root / '.harness/project.json'
        config = read(path if path.exists() else self.root / '.harness/project.example.json')
        config['project_id'] = MARKER
        config['commands']['e2e'] = f'npm run e2e -- {phase}'
        save(path, config)
        self.commit(f'{phase} 验证配置')

    def verify(self, run, stage, rows):
        self.cli('verify', run.name, stage, 'e2e')
        evidence = read(run / 'state.json')['stages'][stage]['evidence']['e2e']
        log = (self.root / evidence['log']).read_bytes()
        check(evidence['exit_code'] == 0 and evidence['commit'] == self.command('git', 'rev-parse', 'HEAD').strip()
              and evidence['sha256'] == hashlib.sha256(log).hexdigest(), f'{stage} 的版本或证据不匹配')
        passed = set(re.findall(r'^PASS (AC-\S+) ', log.decode(), re.M))
        check(all(row['id'] in passed for row in rows), f'{stage} 日志缺少 AC：{passed}')
        return evidence['log']

    def criteria(self, phase):
        rows = []
        for item in read(self.root / 'acceptance.json'):
            if not item['id'].startswith(f'AC-{phase}-'):
                continue
            spec = (self.root / item['requirement_ref'].split('#')[0]).read_text(encoding='utf-8')
            scenario = re.search(r'^#### Scenario: ' + re.escape(item['id']) +
                                 r' ([^\n]+)\n\s*- \*\*WHEN\*\* ([^\n]+)\n- \*\*THEN\*\* ([^\n]+)', spec, re.M)
            check(scenario, f"规范缺少场景 {item['id']}")
            rows.append(dict(item, scenario=scenario[2], expected=scenario[3]))
        check(rows, f'缺少 {phase} 验收项')
        return rows

    def archive(self, run, change):
        changes = self.root / 'openspec/changes'
        delta = (changes / change / 'specs/task-list/spec.md').read_text(encoding='utf-8')
        args = ['archive', change, '--yes']
        output = self.command(*self.openspec, *args)
        archived, = (changes / 'archive').glob('????-??-??-' + change)
        check(not (changes / change).exists() and (archived / 'specs/task-list/spec.md').read_text(encoding='utf-8') == delta,
              f'{change} 的归档内容不匹配')
        spec = (self.root / BASELINE).read_text(encoding='utf-8')
        for requirement in delta.split('### Requirement: ')[1:]:
            check(requirement.strip() in spec, f'正式规范缺少 {requirement.splitlines()[0]}')
        output += self.command(*self.openspec, 'validate', '--all', '--strict', '--no-interactive')
        report = run / 'archive.log'
        report.write_text(shlex.join([*self.openspec, *args]) + '\n' + output + '\n' + str(archived) + '\n', encoding='utf-8')
        self.commit(f'归档 {change}')
        return [BASELINE, report]

    def run_phase(self, phase, change=None):
        self.configure(phase)
        run_id = f'{MARKER}-{phase}'
        run = self.root / '.harness/runs' / run_id
        args = ['--run-id', run_id, '--request', f'{MARKER} 任务清单 {phase} 集成演练']
        if change:
            args += ['--parent-run', f'{MARKER}-M0', '--milestone', 'M1', '--feature-id', phase, '--change-id', change]
        if phase == 'F2':
            args.append('--last-feature')
        self.cli('start', 'feature' if change else 'project-init', *args)
        state = read(run / 'state.json')
        check(state['base_commit'] == self.command('git', 'rev-parse', 'HEAD').strip(), 'run 未绑定配置提交')
        rows = self.criteria(phase)
        save(run / 'acceptance.json', [dict(row, status='not-run', evidence=[]) for row in rows])
        prefix = f'openspec/changes/{change}'
        draft = run / 'roadmap-draft.md'
        shutil.copyfile(self.root / '.planning/ROADMAP.md', draft)
        artifacts = {
            'product-analysis': [f'{prefix}/proposal.md', f'{prefix}/specs/task-list/spec.md'] if change else [PRODUCT],
            'domain-modeling': [BASELINE], 'roadmap-planning': [PRODUCT, draft], 'design-system': ['index.html'],
            'architecture-design': [f'{prefix}/design.md'] if change else ['server.py', 'README.md'],
            'ui-design': ['index.html', f'{prefix}/specs/task-list/spec.md'], 'plan-tasks': [f'{prefix}/tasks.md'],
            'test-plan': ['e2e.mjs'], 'implementation': ['index.html', 'server.py'],
        }
        for stage in state['definition']['stages']:
            key = stage['id']
            print(f'{run_id} {key}', flush=True)
            self.cli('begin', run_id, key)
            if key == 'plan-tasks':
                save(run / 'tasks.json', [dict(id=f'TASK-{phase}', agent='dh_backend', depends_on=[],
                     requirements=[row['id'].replace('AC-', 'REQ-') for row in rows], acceptance=[row['id'] for row in rows],
                     inputs=artifacts['product-analysis'], write_scope=['server.py', 'index.html'],
                     verification=[rows[0]['verification']], status='pending')])
            if key == 'implementation':
                tasks = read(run / 'tasks.json')
                tasks[0]['status'] = 'done'
                save(run / 'tasks.json', tasks)
            if key in ('bootstrap', 'project-review', 'test-feature', 'accept-feature', 'milestone-review'):
                expected = rows if key != 'milestone-review' else read(self.root / 'acceptance.json')
                log = self.verify(run, key, expected)
                artifacts[key] = [log]
                if key in ('accept-feature', 'project-review'):
                    if change:
                        record = read(run / 'state.json')['stages']['product-analysis']
                        snapshot, = [p for p in record['artifacts'] if Path(p).name.startswith('criteria-')]
                        check(read(self.root / snapshot) == rows, '需求快照与 AC 不一致')
                    save(run / 'acceptance.json', [dict(row, status='passed', evidence=[log]) for row in rows])
                    report = run / 'acceptance-report.md'
                    report.write_text(f'# {MARKER} 自动验收\n\n' + '\n'.join(f"- {row['id']} `{log}`" for row in rows) + '\n', encoding='utf-8')
                    artifacts[key].append(report)
            if key == 'review-change':
                report = run / 'review.md'
                tested = read(run / 'state.json')['stages']['test-feature']['evidence']['e2e']
                report.write_text(f'# {MARKER} 自动核对\n\n被测样例 `{tested["commit"]}`。浏览器证据 `{tested["log"]}`。真人审查待主控执行。\n', encoding='utf-8')
                artifacts[key] = [report]
            if key == 'archive':
                artifacts[key] = self.archive(run, change)
                recovered = self.cli('resume', run_id)
                check(recovered['next_action'] == key and recovered['status']['status'] == 'running',
                      '恢复应能识别已完成的外部归档操作')
            if key == 'reflection':
                artifacts[key] = [run / 'archive.log', run / 'acceptance-report.md']
            flags = []
            for artifact in artifacts[key]:
                flags += ['--artifact', str((self.root / artifact).relative_to(self.root))]
            result = self.cli('advance', run_id, key, *flags)
            if stage['human_approval']:
                record = result['status']
                check(record['status'] == 'awaiting_approval' and record['artifacts'], f'缺少 {key} 门禁')
                self.cli('approve', run_id, key, '--token', record['review_token'], '--reply',
                         f'{MARKER} 临时 fixture 自动输入 {phase}/{key}，仅验证令牌及产物绑定。')
        check(self.cli('resume', run_id)['status'] == 'complete', f'{run_id} 尚未完成')
        return read(run / 'state.json')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--run', action='store_true', help='显式执行独立集成演练')
    parser.add_argument('--keep', action='store_true', help='成功时也保留临时项目和证据')
    parser.add_argument('--openspec', help='已安装的 OpenSpec CLI 路径或命令名')
    args = parser.parse_args()
    if not args.run:
        parser.print_help()
        return
    temp = Path(tempfile.mkdtemp(prefix='devharness-synthetic-test-')).resolve()
    print(f'synthetic-test 临时目录 {temp}', flush=True)
    app = Rehearsal(temp / MARKER, args.openspec)
    app.setup()
    app.run_phase('M0')
    app.run_phase('F1', 'add-task')
    last = app.run_phase('F2', 'complete-and-filter')
    check(last['stages']['milestone-review']['status'] == 'passed', 'M1 整合门禁未完成')
    print('PASS synthetic-test M0、M1/F1、M1/F2、OpenSpec 归档、Chrome 整合验收')
    if not args.keep:
        shutil.rmtree(temp)


if __name__ == '__main__':
    main()
