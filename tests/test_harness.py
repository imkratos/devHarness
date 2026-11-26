"""Public CLI regression tests. All replies are synthetic fixtures in disposable repos."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1]
REPLY = '自动化测试夹具，同意所展示的测试样本'


class HarnessTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve() / 'project'
        subprocess.run([sys.executable, SOURCE / 'install.py', self.root], check=True, capture_output=True)
        self.git('init', '-q')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.cli('start', 'feature', '--request', '样例原始需求', '--run-id', 'init')
        self.write('docs/product/PROJECT.md', '无界面工具，读取示例文件')
        self.write('product.txt', 'fixture')
        self.write('smoke.py', 'from pathlib import Path\nassert Path("product.txt").read_text() == "fixture"\n')
        config = self.read('.harness/project.json')
        config['commands']['e2e'] = '"' + sys.executable + '" smoke.py'
        self.write('.harness/project.json', config)
        self.commit()

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.root, check=True, capture_output=True)

    def commit(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture version')

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value if isinstance(value, str) else json.dumps(value))
        return str(path.relative_to(self.root))

    def read(self, name):
        return json.loads((self.root / name).read_text())

    def call(self, *args):
        return subprocess.run([sys.executable, '.harness/scripts/harness.py', *args], cwd=self.root,
                              capture_output=True, text=True)

    def cli(self, *args):
        result = self.call(*args)
        self.assertEqual(result.returncode, 0, msg=f'{args}: {result.stderr}')
        return json.loads(result.stdout)

    def reject(self, *args):
        self.assertNotEqual(self.call(*args).returncode, 0, msg=args)

    def record(self, run, name):
        return self.write(f'.harness/runs/{run}/{name}', name)

    def advance(self, run, stage, *artifacts, options=()):
        args = ['advance', run, stage, *options]
        for name in artifacts:
            args.extend(('--artifact', name))
        return self.cli(*args)

    def approve(self, run, stage, result):
        return self.cli('approve', run, stage, '--token', result['status']['review_token'], '--reply', REPLY)

    def stage(self, run, key, *files, verify=False, options=()):
        self.cli('begin', run, key)
        if verify:
            self.cli('verify', run, key, 'e2e')
        result = self.advance(run, key, *(files or (self.record(run, key + '.md'),)), options=options)
        if result['next_action'] == key:
            result = self.approve(run, key, result)
        return result

    def init_to(self, last='project-review'):
        project = 'docs/product/PROJECT.md'
        roadmap = self.record('init', 'roadmap.md')
        for key in ('product-analysis', 'domain-modeling', 'roadmap-planning', 'design-system',
                    'architecture-design', 'bootstrap', 'project-review'):
            files, options = (), ()
            if key == 'product-analysis':
                files = (project,)
            if key in ('roadmap-planning', 'design-system'):
                files = (project, roadmap)
            if key == 'design-system':
                options = ('--skip-reason', '无 UI', '--use-approval', 'init/roadmap-planning')
            self.stage('init', key, *files, options=options, verify=key in ('bootstrap', 'project-review'))
            if key == last:
                break

    def test_cold_start_pinned_resume_and_stale_approval(self):
        result = self.cli('start', 'feature', '--request', '样例原始需求')
        self.assertEqual(result['run_id'], 'init')
        self.assertIsNone(self.read('.harness/runs/init/state.json')['base_commit'])
        self.init_to('domain-modeling')
        self.cli('begin', 'init', 'roadmap-planning')
        files = ['docs/product/PROJECT.md', self.record('init', 'draft.md')]
        waiting = self.advance('init', 'roadmap-planning', *files)
        self.reject('approve', 'init', 'roadmap-planning', '--token', 'stale', '--reply', REPLY)
        self.approve('init', 'roadmap-planning', waiting)
        self.write(files[0], '需求调整')
        actual = self.cli('resume', 'init')
        self.assertEqual(actual['next_action'], 'product-analysis')
        state = self.read('.harness/runs/init/state.json')
        self.assertFalse(state['approvals'])
        self.assertTrue(any(h['approval'] for h in state['history']))
        self.write('.harness/workflows/project-init.json', {})
        self.assertEqual(self.cli('resume', 'init')['next_action'], 'product-analysis')

    def test_no_ui_branch_verify_drift_and_no_false_success(self):
        self.init_to('architecture-design')
        self.cli('begin', 'init', 'bootstrap')
        proof = self.record('init', 'demo.md')
        self.reject('advance', 'init', 'bootstrap', '--artifact', proof)
        self.cli('verify', 'init', 'bootstrap', 'e2e')
        self.advance('init', 'bootstrap', proof)
        self.write('.planning/ROADMAP.md', '记录验收结果')
        self.commit()
        self.assertEqual(self.cli('resume', 'init')['next_action'], 'project-review')
        self.write('product.txt', '产品变更')
        self.commit()
        self.assertEqual(self.cli('resume', 'init')['next_action'], 'bootstrap')
        self.cli('begin', 'init', 'bootstrap')
        self.reject('verify', 'init', 'bootstrap', 'e2e')
        self.reject('advance', 'init', 'bootstrap', '--artifact', proof)
        self.cli('fail', 'init', 'bootstrap', 'environment', '--reason', '核对测试环境')
        state = self.read('.harness/runs/init/state.json')
        self.assertEqual(state['stages']['bootstrap']['attempts'], 0)
        self.assertEqual(state['stages']['design-system']['status'], 'skipped')
        self.assertEqual(state['approvals']['design-system']['source'], 'init/roadmap-planning')

    def test_retry_limit_and_lock(self):
        for _ in range(3):
            self.cli('begin', 'init', 'product-analysis')
            self.cli('fail', 'init', 'product-analysis', 'execution', '--reason', '实际执行失败')
        self.reject('begin', 'init', 'product-analysis')
        self.cli('reopen', 'init', 'product-analysis', '--reason', '已修复输入')
        self.cli('begin', 'init', 'product-analysis')
        with ThreadPoolExecutor(2) as pool:
            futures = [pool.submit(self.call, 'advance', 'init', 'product-analysis', '--artifact',
                                   'docs/product/PROJECT.md') for _ in range(2)]
            self.assertEqual(sorted(f.result().returncode == 0 for f in futures), [False, True])
        self.assertEqual(self.cli('resume', 'init')['next_action'], 'domain-modeling')

    def test_bugfix_and_refactor_task_packages(self):
        self.init_to()
        for route, first in [('bugfix', 'reproduce'), ('refactor', 'impact-analysis')]:
            self.cli('start', route, '--request', route, '--run-id', route)
            self.cli('begin', route, first)
            report = self.record(route, first + '.md')
            self.reject('advance', route, first, '--artifact', report)
            tasks = self.read('.harness/templates/tasks.json')
            tasks[0].update(write_scope=['product.txt'], verification=['smoke.py'])
            tasks.append(dict(tasks[0], id='TASK-002', status='done'))
            self.write(f'.harness/runs/{route}/tasks.json', tasks)
            if route == 'bugfix':
                self.reject('advance', route, first, '--artifact', report)
                ac = dict(id='AC-002', scenario='读取文件', expected='输出内容',
                          verification='smoke.py', requirement_ref='REQ-001')
                ac_path = f'.harness/runs/{route}/acceptance.json'
                self.write(ac_path, [ac])
                self.reject('advance', route, first, '--artifact', report)
                ac['id'] = 'AC-001'
                self.write(ac_path, [ac])
            self.advance(route, first, report)
            if route == 'refactor':
                self.stage(route, 'test-plan')
            self.cli('begin', route, 'implementation')
            pending = self.call('advance', route, 'implementation', '--artifact', report)
            self.assertNotEqual(pending.returncode, 0)
            self.assertIn(tasks[0]['id'], pending.stderr)
            tasks[0]['status'] = 'done'
            self.write(f'.harness/runs/{route}/tasks.json', tasks)
            self.stage(route, 'implementation')
            self.cli('begin', route, 'test-feature')
            self.cli('fail', route, 'test-feature', 'code', '--reason', '回归测试发现实现错误')
            self.assertEqual(self.cli('resume', route)['next_action'], 'implementation')
            if route == 'bugfix':
                ac.update(status='not-run', evidence=[])
                self.write(ac_path, [ac])
                self.assertEqual(self.cli('resume', route)['next_action'], 'implementation')
                ac['expected'] = '新预期'
                self.write(ac_path, [ac])
                self.assertEqual(self.cli('resume', route)['next_action'], 'reproduce')

    def test_task_inputs_in_and_outside_write_scope(self):
        self.init_to()
        self.cli('start', 'refactor', '--run-id', 'r', '--request', '重构')
        tasks = self.read('.harness/templates/tasks.json')
        contract = self.write('src-spec/contract.md', 'v1')
        code = self.write('src/app.py', 'original')
        tasks[0].update(write_scope=['src/'], inputs=[code, contract], verification=['smoke.py'])
        self.write('.harness/runs/r/tasks.json', tasks)
        self.stage('r', 'impact-analysis')
        self.stage('r', 'test-plan')
        self.write(code, 'modified')
        self.assertEqual(self.cli('resume', 'r')['next_action'], 'implementation')
        self.write(contract, 'v2')
        self.assertEqual(self.cli('resume', 'r')['next_action'], 'impact-analysis')
        self.assertEqual(self.read('.harness/runs/r/state.json')['stages']['test-plan']['status'], 'pending')

    def test_active_v2_run_refreezes_old_task_digest(self):
        self.init_to()
        self.cli('start', 'refactor', '--run-id', 'r', '--request', '升级前的任务')
        tasks = self.read('.harness/templates/tasks.json')
        tasks[0].update(write_scope=['src/'], verification=['smoke.py'])
        self.write('.harness/runs/r/tasks.json', tasks)
        self.stage('r', 'impact-analysis')
        self.stage('r', 'test-plan')
        path = '.harness/runs/r/state.json'
        state = self.read(path)
        old_plan = [{k: v for k, v in task.items() if k != 'status'} for task in tasks]
        old_digest = hashlib.sha256(json.dumps(old_plan, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        state['stages']['impact-analysis']['task_hash'] = old_digest
        self.write(path, state)
        self.assertEqual(self.cli('resume', 'r')['next_action'], 'impact-analysis')
        self.assertTrue(any(h['record'].get('task_hash') == old_digest for h in self.read(path)['history']))
        self.assertEqual(self.stage('r', 'impact-analysis')['next_action'], 'test-plan')

    def test_legacy_is_readable_and_adoption_keeps_original(self):
        old = {'run_id': 'old', 'workflow': 'bugfix', 'stages': {'reproduce': 'passed'},
               'artifacts': {}, 'approvals': {'unknown': 'v1'}}
        self.write('.harness/runs/old/state.json', old)
        self.assertTrue(self.cli('status', 'old')['legacy'])
        self.reject('resume', 'old')
        self.assertEqual(self.read('.harness/runs/old/state.json'), old)
        self.assertEqual(self.cli('resume', 'old', '--adopt-legacy')['next_action'], 'reproduce')
        migrated = self.read('.harness/runs/old/state.json')
        self.assertEqual(migrated['history'][0]['legacy'], old)
        self.assertFalse(migrated['approvals'])

    def test_approval_keeps_the_presented_commit(self):
        self.init_to('bootstrap')
        self.cli('begin', 'init', 'project-review')
        self.cli('verify', 'init', 'project-review', 'e2e')
        waiting = self.advance('init', 'project-review', self.record('init', 'result.md'))
        shown = waiting['status']['commit']
        self.write('.planning/ROADMAP.md', '更新演示安排')
        self.commit()
        self.approve('init', 'project-review', waiting)
        self.assertEqual(self.read('.harness/runs/init/state.json')['approvals']['project-review']['commit'], shown)

    def test_rewind_does_not_clear_retry_limit(self):
        self.init_to('product-analysis')
        for _ in range(3):
            self.cli('begin', 'init', 'domain-modeling')
            self.cli('fail', 'init', 'domain-modeling', 'execution', '--reason', '实际执行失败')
        self.write('docs/product/PROJECT.md', '用户调整范围')
        self.cli('resume', 'init')
        self.stage('init', 'product-analysis', 'docs/product/PROJECT.md')
        self.reject('begin', 'init', 'domain-modeling')
        self.cli('reopen', 'init', 'domain-modeling', '--reason', '已核实新范围')
        self.cli('begin', 'init', 'domain-modeling')

    def test_conversion_replaces_parent_and_validates_source_approval(self):
        self.init_to()
        self.cli('start', 'refactor', '--request', '调整内部结构', '--run-id', 'old')
        feature = ['start', 'feature', '--request', '新增行为', '--feature-id', 'F1', '--change-id',
                   'change', '--parent-run', 'old', '--run-id', 'new']
        self.cli(*feature)
        self.cli(*feature)
        self.assertEqual(self.cli(*feature[:-2])['run_id'], 'new')
        changed_request = feature[:-2].copy()
        changed_request[3] = '另一项需求'
        self.reject(*changed_request)
        self.cli('start', 'bugfix', '--request', '另一个修复', '--run-id', 'other')
        conflicting = [value if value != 'old' else 'other' for value in feature]
        self.reject(*conflicting)
        self.reject(*conflicting[:-2])
        self.assertEqual(self.cli('resume', 'old')['next_action'], 'new')
        self.reject('begin', 'old', 'impact-analysis')
        spec = self.write('openspec/changes/change/specs/tool/spec.md', '新行为规范')
        ac = dict(id='AC1', scenario='读取输入', expected='输出结果', verification='smoke.py',
                  requirement_ref=spec, status='not-run', evidence=[])
        self.write('.harness/runs/new/acceptance.json', [ac])
        self.stage('new', 'product-analysis', spec)
        self.cli('begin', 'new', 'ui-design')
        artifacts = ['--artifact', 'docs/product/PROJECT.md', '--artifact', '.harness/runs/init/roadmap.md']
        opts = ['--skip-reason', '无 UI', '--use-approval', 'init/design-system']
        design = self.root / '.harness/runs/init/domain-modeling.md'
        original = design.read_bytes()
        design.write_text('上游模型已变')
        self.reject('advance', 'new', 'ui-design', *artifacts, *opts)
        design.write_bytes(original)
        self.cli('advance', 'new', 'ui-design', *artifacts, *opts)
        design.write_text('已复用后再修改上游模型')
        self.assertEqual(self.cli('resume', 'new')['next_action'], 'ui-design')

    def test_incomplete_legacy_feature_can_retry_adoption(self):
        old = dict(run_id='old', workflow='feature', stages={}, approvals={}, change_id=None)
        path = '.harness/runs/old/state.json'
        self.write(path, old)
        self.reject('resume', 'old', '--adopt-legacy')
        self.assertEqual(self.read(path), old)
        self.cli('resume', 'old', '--adopt-legacy', '--feature-id', 'F0', '--change-id', 'existing')
        self.assertEqual(self.read(path)['change_id'], 'existing')


if __name__ == '__main__':
    unittest.main()
