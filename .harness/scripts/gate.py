"""Run evidence, read-only checks, and artifact fingerprints for DevHarness."""
import hashlib
import json
import subprocess


class GateError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise GateError(message)


def read_json(path):
    with path.open(encoding='utf-8') as stream:
        return json.load(stream)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fingerprint(value):
    return digest(json.dumps(value, sort_keys=True, ensure_ascii=False).encode())


def local_file(root, name):
    path = (root / name).resolve()
    require(path.is_relative_to(root) and path.is_file(), f'缺少项目内文件 {name}')
    return path


def artifact_hash(root, name, change=None):
    # OpenSpec archive moves the proposal tree. Accept exactly one identical successor.
    path = root / name
    if change and not path.exists():
        changes = root / 'openspec/changes'
        if path.is_relative_to(changes / change):
            relative = path.relative_to(changes / change)
            matches = [p / relative for p in (changes / 'archive').glob(f'????-??-??-{change}')
                       if (p / relative).is_file()]
            if len(matches) == 1:
                path = matches[0]
    return digest(local_file(root, path).read_bytes())


def git(root, *args):
    return subprocess.run(['git', *args], cwd=root, capture_output=True, text=True)


# These files change when a run records evidence, updates the roadmap or archives specs.
PRODUCT = ['.', ':(exclude).harness/runs', ':(exclude).planning/ROADMAP.md',
           ':(exclude)openspec/changes', ':(exclude)openspec/specs', ':(exclude)LESSONS.md']


def clean_head(root):
    head = git(root, 'rev-parse', '--verify', 'HEAD')
    require(head.returncode == 0, '正式验证需要已提交的集成版本')
    status = git(root, 'status', '--porcelain', '--untracked-files=all', '--', *PRODUCT)
    require(status.returncode == 0 and not status.stdout.strip(),
            f'正式验证需要干净的产品工作区\n{status.stdout.strip()}')
    return head.stdout.strip()


def same_product(root, commit):
    current = clean_head(root)
    ancestor = git(root, 'merge-base', '--is-ancestor', commit, current)
    changes = git(root, 'diff', '--quiet', commit, current, '--', *PRODUCT)
    return ancestor.returncode == 0 and changes.returncode == 0


def required_commands(stage, config):
    commands = config['commands']
    if stage in ('bootstrap', 'project-review', 'accept-feature', 'milestone-review'):
        return ['e2e']
    if stage == 'test-feature':
        selected = [key for key in ('unit', 'integration', 'e2e') if commands.get(key)]
        require(selected, '至少配置一条适用的正式测试命令')
        return selected
    return []


def verify_evidence(root, stage, records):
    config = read_json(root / '.harness/project.json')
    for key in required_commands(stage, config):
        command = config['commands'].get(key)
        require(isinstance(command, str) and command.strip(), f'缺少验证命令 {key}')
        record = records.get(key)
        require(record and record['exit_code'] == 0 and record['command'] == command,
                f'{key} 缺少成功的当前命令证据')
        require(artifact_hash(root, record['log']) == record['sha256'], f'{key} 日志已变更')
        require(same_product(root, record['commit']), f'{key} 被测版本与当前产品不同')


def task_package(root, run, change=None, *, completed=False):
    rows = read_json(run / 'tasks.json')
    require(isinstance(rows, list) and rows, '缺少可实施任务')
    seen = set()
    inputs = set()
    writable = set()
    for row in rows:
        key = row['id']
        require(key and key not in seen and set(row['depends_on']) <= seen, f'任务依赖无效 {key}')
        require(row.get('agent') in ('dh_backend', 'dh_frontend'), f'任务角色无效 {key}')
        for field in ('write_scope', 'verification', 'requirements', 'acceptance'):
            require(isinstance(row.get(field), list) and all(isinstance(x, str) and x.strip()
                    for x in row[field]) and row[field], f'{key} 缺少 {field}')
        names = row.get('inputs', [])
        require(isinstance(names, list) and all(isinstance(p, str) and p.strip() for p in names),
                f'{key} 的 inputs 应为项目文件路径列表')
        inputs.update(names)
        writable.update((root / p).resolve() for p in row['write_scope'])
        seen.add(key)
    if completed:
        pending = [row['id'] for row in rows if row.get('status') != 'done']
        require(not pending, f'实施任务未完成：{", ".join(map(str, pending))}')
    frozen = {}
    for name in sorted(inputs):
        path = (root / name).resolve()
        require(path.is_relative_to(root), f'任务输入必须在项目内 {name}')
        if not any(path.is_relative_to(scope) for scope in writable):
            frozen[name] = artifact_hash(root, name, change)
    plan = [{k: v for k, v in row.items() if k != 'status'} for row in rows]
    # Legacy digests covered only the plan. An active run must establish its input baseline.
    return fingerprint({'tasks': plan, 'inputs': frozen})


def criteria(run):
    rows = read_json(run / 'acceptance.json')
    require(isinstance(rows, list) and rows, '验收清单为空')
    seen = set()
    for ac in rows:
        key = ac['id']
        require(key and key not in seen, f'重复验收项 {key}')
        require(ac['requirement_ref'] and 'replace' not in ac['requirement_ref'], f'{key} 缺少需求引用')
        for field in ('scenario', 'expected', 'verification'):
            require(isinstance(ac.get(field), str) and ac[field].strip() not in ('', 'replace'),
                    f'{key} 缺少 {field}')
        seen.add(key)
    return [{k: v for k, v in ac.items() if k not in ('status', 'evidence')} for ac in rows]


def acceptance(root, run, records):
    seen = {ac['id'] for ac in criteria(run)}
    for ac in read_json(run / 'acceptance.json'):
        key = ac['id']
        require(ac['status'] == 'passed', f'{key} 尚未通过验收')
        require(isinstance(ac['evidence'], list) and ac['evidence'], f'{key} 缺少证据')
        require(any(ev['log'] in ac['evidence'] for ev in records),
                f'{key} 需要关联本集成版本的测试或验收日志')
        for name in ac['evidence']:
            local_file(root, name)
    check_task_criteria(run, seen)


def check_task_criteria(run, ids):
    for task in read_json(run / 'tasks.json'):
        require(set(task['acceptance']) <= ids, f'{task["id"]} 引用了验收清单以外的 AC')
