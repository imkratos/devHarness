"""Local orchestration ledger. Only the main session invokes mutating commands."""
import argparse
from contextlib import ExitStack, contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from uuid import uuid4

sys.dont_write_bytecode = True
from gate import (GateError, acceptance, artifact_hash, clean_head, criteria, digest, fingerprint,
                  git, local_file, read_json, require, required_commands, same_product,
                  task_package, verify_evidence)

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / '.harness'
RUNS = BASE / 'runs'
ROUTES = ('project-init', 'feature', 'bugfix', 'refactor')
DONE = ('passed', 'skipped')


def now():
    return datetime.now(timezone.utc).isoformat()


def identifier(value):
    require(isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', value),
            f'无效标识 {value!r}')
    return value


def save(path, data):
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent, delete=False) as f:
        temp = Path(f.name)
        try:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())
        except BaseException:
            temp.unlink(missing_ok=True)
            raise
    try:
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


@contextmanager
def lock(directory):
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / '.lock').open('a+b') as f:
        if os.name == 'nt':
            import msvcrt
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def load(run_id):
    return read_json(RUNS / identifier(run_id) / 'state.json')


def inventory():
    return [read_json(p) for p in sorted(RUNS.glob('*/state.json'))]


def successor(state):
    if state['workflow'] in ('bugfix', 'refactor'):
        return next((s for s in inventory() if s.get('converted_from') == state['run_id']), None)


def definitions(state):
    workflow = state['definition']
    require(fingerprint(workflow) == state['workflow_sha256'], '工作流快照校验失败')
    return workflow['stages']


def current(state):
    return next((s for s in definitions(state) if state['stages'][s['id']]['status'] not in DONE), None)


def fresh(args, workflow, run_id):
    definition = read_json(BASE / 'workflows' / f'{workflow}.json')
    if getattr(args, 'last_feature', False) and workflow == 'feature':
        require(args.milestone, '最后一个功能需要 --milestone')
        definition['stages'].append(dict(id='milestone-review', skill='dh-project-review', agent='main',
                                         depends_on=['reflection'], human_approval=True, optional=False,
                                         max_attempts=3))
    head = git(ROOT, 'rev-parse', '--verify', 'HEAD')
    state = read_json(BASE / 'templates/state.json')
    state.update(schema_version=2, run_id=run_id, workflow=workflow, request=args.request,
                 workflow_version=definition['version'], workflow_sha256=fingerprint(definition),
                 definition=definition, base_commit=head.stdout.strip() or None,
                 stages={s['id']: {'status': 'pending', 'attempts': 0} for s in definition['stages']},
                 feature_id=args.feature_id, change_id=args.change_id, milestone=args.milestone,
                 parent_run=args.parent_run, history=[],
                 max_attempts=read_json(BASE / 'project.json')['max_attempts'])
    return state


def start(args):
    require(args.request.strip(), '请输入原始需求')
    for key in (args.run_id, args.change_id, args.feature_id, args.parent_run, args.milestone):
        if key:
            identifier(key)
    with lock(RUNS), ExitStack() as locks:
        states = inventory()
        inits = [s for s in states if s['workflow'] == 'project-init']
        ready = any(s.get('schema_version') == 2 and not current(s) for s in inits)
        route = args.workflow if ready else 'project-init'
        if route == 'project-init' and inits:
            require(len(inits) == 1, '存在多个初始化记录，请指定 run 恢复')
            return summary(inits[0])
        if args.run_id:
            existing = next((s for s in states if s['run_id'] == args.run_id), None)
            if existing:
                require(existing['workflow'] == route and existing.get('request') == args.request,
                        '该 run ID 已用于不同请求')
                return summary(existing)
        if route == 'feature':
            require(args.change_id and args.feature_id, '功能需要 --feature-id 和 --change-id')
            prior = [s for s in states if s.get('workflow') == 'feature' and
                     (s.get('change_id') == args.change_id or s.get('feature_id') == args.feature_id)]
            if prior:
                require(len(prior) == 1 and prior[0].get('change_id') == args.change_id and
                        prior[0].get('feature_id') == args.feature_id, '功能和变更 ID 关联冲突')
                return summary(prior[0])
        conversion = None
        if args.parent_run:
            parent = load(args.parent_run)
            if route == 'feature' and parent['workflow'] in ('bugfix', 'refactor'):
                locks.enter_context(lock(RUNS / args.parent_run))
                parent = load(args.parent_run)
                require(not successor(parent), '父 run 已转换为另一项功能')
                if current(parent):
                    conversion = args.parent_run
        if route == 'project-init' and not (BASE / 'project.json').exists():
            config = read_json(BASE / 'project.example.json')
            config['project_id'] = ROOT.name
            save(BASE / 'project.json', config)
        subprocess.run([sys.executable, str(BASE / 'scripts/check.py'), '--project'], cwd=ROOT,
                       check=True, stdout=sys.stderr)
        run_id = args.run_id or f'{route}-{uuid4().hex[:12]}'
        state = fresh(args, route, run_id)
        if conversion:
            # Publishing this one child record also closes its parent's dispatch path.
            state['converted_from'] = conversion
        if route == 'project-init':
            state.update(change_id=None, feature_id=None, milestone='M0')
        elif not state['parent_run'] and len(inits) == 1:
            state['parent_run'] = inits[0]['run_id']
        path = RUNS / run_id
        # Publish only a complete initial layout. Interrupted drafts are outside inventory.
        with tempfile.TemporaryDirectory(dir=RUNS) as staging:
            draft = Path(staging) / 'run'
            draft.mkdir()
            save(draft / 'tasks.json', [])
            save(draft / 'acceptance.json', [])
            persist(draft, state)
            draft.rename(path)
        return summary(state)


def summary(state):
    replacement = successor(state)
    if replacement:
        return dict(run_id=state['run_id'], workflow=state['workflow'], status='superseded',
                    next_action=replacement['run_id'], reason=replacement['request'])
    if state.get('schema_version') != 2:
        return dict(run_id=state['run_id'], workflow=state['workflow'], legacy=True,
                    blockers=['缺少 v2 工作流快照；原审批、阶段和证据须逐项复核'],
                    review={'stages': state.get('stages'), 'approvals': state.get('approvals'),
                            'artifacts': state.get('artifacts')})
    stage = current(state)
    return dict(run_id=state['run_id'], workflow=state['workflow'], request=state['request'],
                next_action=stage['id'] if stage else None,
                status=state['stages'][stage['id']] if stage else 'complete',
                blockers=state.get('blockers', []))


def persist(run, state):
    stage = current(state)
    state['next_action'] = stage['id'] if stage else None
    record = state['stages'][stage['id']] if stage else {}
    state['blockers'] = [record['reason']] if record.get('status') == 'blocked' else []
    save(run / 'state.json', state)


def rewind(state, target, reason):
    affected = {target}
    for s in definitions(state):
        key = s['id']
        if key not in affected and not affected.intersection(s['depends_on']):
            continue
        affected.add(key)
        old = state['stages'][key]
        approval = state['approvals'].pop(key, None)
        if old['status'] != 'pending' or old.get('artifacts') or approval:
            state['history'].append(dict(time=now(), stage=key, reason=reason, record=old, approval=approval))
        state['stages'][key] = dict(status='pending', attempts=old['attempts'])
        if old.get('exhausted'):
            state['stages'][key].update(status='blocked', reason=old['reason'], exhausted=old['exhausted'])


def validate_design_source(source, version, visited=None):
    """Check the original approval and its inputs even before its owner resumes."""
    visited = set() if visited is None else visited
    require(source not in visited, 'UI 批准来源循环引用')
    visited.add(source)
    run_id, key = source.split('/', 1)
    state = load(run_id)
    approval = state['approvals'].get(key)
    require(approval and approval['version'] == version, '引用的批准已经失效')
    needed = {key}
    for stage in reversed(definitions(state)):
        if stage['id'] not in needed:
            continue
        needed.update(stage['depends_on'])
        item = state['stages'][stage['id']]
        require(item['status'] in DONE, '原批准的上游阶段待复核')
        for name, sha in item.get('artifacts', {}).items():
            require(artifact_hash(ROOT, name, state.get('change_id')) == sha, f'原批准依据已变化 {name}')
        if 'criteria_hash' in item:
            require(fingerprint(criteria(RUNS / run_id)) == item['criteria_hash'], '原批准的 AC 已变化')
    if approval.get('source'):
        validate_design_source(approval['source'], version, visited)


def reconcile(run, state):
    # Finished runs remain historical records of their integrated version.
    if not current(state):
        return
    for s in definitions(state):
        key = s['id']
        record = state['stages'][key]
        if record['status'] not in (*DONE, 'awaiting_approval', 'running'):
            continue
        try:
            for name, sha in record.get('artifacts', {}).items():
                require(artifact_hash(ROOT, name, state.get('change_id')) == sha, f'产物变更 {name}')
            approval = state['approvals'].get(key, {})
            if approval.get('source'):
                validate_design_source(approval['source'], approval['version'])
            if 'task_hash' in record:
                require(task_package(ROOT, run) == record['task_hash'], '任务范围或验证规则变更')
            if 'criteria_hash' in record:
                require(fingerprint(criteria(run)) == record['criteria_hash'], '验收条件已变化')
            if record.get('commit') and key in ('bootstrap', 'test-feature', 'accept-feature',
                                                'project-review', 'milestone-review'):
                require(same_product(ROOT, record['commit']), '被测产品已变化')
            for ev in record.get('evidence', {}).values():
                require(artifact_hash(ROOT, ev['log']) == ev['sha256'], '测试日志已变化')
        except (ValueError, KeyError, TypeError, FileNotFoundError) as exc:
            rewind(state, key, str(exc))
            persist(run, state)
            return


def files(args):
    result = {}
    for name in args.artifact:
        path = local_file(ROOT, name)
        result[path.relative_to(ROOT).as_posix()] = digest(path.read_bytes())
    return result


def gate(run, state, stage, record):
    key = stage['id']
    artifacts = record['artifacts']
    if state['workflow'] == 'project-init':
        if key in ('product-analysis', 'roadmap-planning'):
            require('docs/product/PROJECT.md' in artifacts, '请绑定产品范围 docs/product/PROJECT.md')
        if key == 'roadmap-planning':
            require(len(artifacts) >= 2, '请同时绑定 M0 路线图草案')
    if key == 'product-analysis' and state['workflow'] == 'feature':
        prefix = f'openspec/changes/{state["change_id"]}/specs/'
        require(any(p.startswith(prefix) and p.endswith('/spec.md') for p in artifacts),
                '请绑定本次变更的 OpenSpec 需求规范')
        record['criteria_hash'] = fingerprint(criteria(run))
        snapshot = run / 'evidence' / f'criteria-{record["criteria_hash"]}.json'
        snapshot.parent.mkdir(exist_ok=True)
        if not snapshot.exists():
            save(snapshot, criteria(run))
        artifacts[snapshot.relative_to(ROOT).as_posix()] = digest(snapshot.read_bytes())
    if key == 'review-change':
        require(any(Path(name).name == 'review.md' for name in artifacts), '请绑定实际 review.md')
    if key in ('plan-tasks', 'impact-analysis', 'reproduce', 'implementation'):
        record['task_hash'] = task_package(ROOT, run)
    checked = ('bootstrap', 'test-feature', 'accept-feature', 'project-review', 'milestone-review')
    if key in checked:
        verify_evidence(ROOT, key, record.get('evidence', {}))
        # Administrative commits may follow the preview. Preserve the displayed version.
        record.setdefault('commit', clean_head(ROOT))
    if key == 'accept-feature':
        require(any(Path(name).name == 'acceptance-report.md' for name in artifacts), '请绑定 acceptance-report.md')
        records = [*state['stages']['test-feature']['evidence'].values(), *record['evidence'].values()]
        acceptance(ROOT, run, records)
        ac_file = (run / 'acceptance.json').relative_to(ROOT).as_posix()
        record['artifacts'][ac_file] = artifact_hash(ROOT, ac_file)
        for ac in read_json(run / 'acceptance.json'):
            for name in ac['evidence']:
                record['artifacts'][name] = artifact_hash(ROOT, name)
    if key == 'archive':
        change = identifier(state['change_id'])
        changes = ROOT / 'openspec/changes'
        require(not (changes / change).exists(), '活动变更仍存在，请核对归档')
        archived = list((changes / 'archive').glob(f'????-??-??-{change}'))
        require(len(archived) == 1 and archived[0].is_dir(), '缺少唯一的 OpenSpec 归档目录')
        require(any(name.startswith('openspec/specs/') for name in record['artifacts']),
                '请绑定归档后正式规范，并核对实际 CLI 结果')
    if key == 'milestone-review':
        for item in inventory():
            if item['run_id'] == state['run_id'] or item.get('milestone') != state['milestone'] or successor(item):
                continue
            require(item.get('schema_version') == 2 and not current(item),
                    f"里程碑成员 {item['run_id']} 尚未完成")
            accepted = item['stages'].get('accept-feature', {}).get('commit')
            if accepted:
                require(git(ROOT, 'merge-base', '--is-ancestor', accepted, record['commit']).returncode == 0,
                        f"里程碑尚未整合 {item['run_id']}")


def verify(run, stage, record, key):
    config = read_json(BASE / 'project.json')
    require(key in required_commands(stage['id'], config), '该命令不属于本阶段验证')
    command = config['commands'].get(key)
    require(isinstance(command, str) and command.strip(), f'缺少配置命令 {key}')
    commit = clean_head(ROOT)
    folder = run / 'evidence'
    folder.mkdir(exist_ok=True)
    path = folder / f'{stage["id"]}-{key}-{uuid4().hex[:12]}.log'
    with path.open('xb') as log:
        proc = subprocess.run(command, cwd=ROOT, shell=True, stdout=log, stderr=subprocess.STDOUT)
    result = dict(command=command, cwd=str(ROOT), exit_code=proc.returncode, log=path.relative_to(ROOT).as_posix(),
                  sha256=digest(path.read_bytes()), commit=commit, time=now())
    record.setdefault('evidence', {})[key] = result
    if proc.returncode:
        record['failed_command'] = key
    return result


def fail(state, stage, args):
    key = stage['id']
    reason = args.reason.strip()
    require(reason, '需要记录失败原因')
    record = state['stages'][key]
    if args.kind == 'environment':
        record.pop('failed_command', None)
        record.update(status='blocked', reason=reason)
        return
    implementation = 'bootstrap' if state['workflow'] == 'project-init' else 'implementation'
    target = {'execution': key, 'code': implementation, 'requirements': 'product-analysis',
              'ui': 'ui-design' if state['workflow'] == 'feature' else 'design-system'}[args.kind]
    order = list(state['stages'])
    require(target in order and order.index(target) <= order.index(key), '回退目标不在已执行阶段')
    if args.kind in ('execution', 'code'):
        record['attempts'] += 1
    exhausted = record['attempts'] >= min(stage['max_attempts'], state.get('max_attempts', stage['max_attempts']))
    rewind(state, target, reason)
    record = state['stages'][target]
    if exhausted:
        record.update(status='blocked', reason=f'重试已达上限：{reason}', exhausted=key)
    elif target == key and args.kind == 'execution':
        record.update(status='failed', reason=reason)


def reuse_design(state, stage, record, source):
    run_id, key = source.split('/', 1)
    other = load(run_id)
    from_scope = (key == 'roadmap-planning' and stage['id'] == 'design-system' and
                  run_id == state['run_id'] and record.get('skip_reason'))
    from_design = key in ('ui-design', 'design-system') and run_id != state['run_id']
    require(other.get('schema_version') == 2 and (from_scope or from_design) and
            stage['id'] in ('ui-design', 'design-system'),
            '仅可引用其他 run 的有效 UI 决定')
    approval = other['approvals'].get(key)
    require(approval and other['stages'][key]['status'] in DONE, '原批准尚未生效')
    validate_design_source(source, approval['version'])
    require(record['artifacts'] == approval['artifacts'] and (from_scope or bool(record.get('skip_reason')) ==
            bool(other['stages'][key].get('skip_reason'))), '复用的产物或适用性与原批准不符')
    state['approvals'][stage['id']] = dict(approval, source=source)
    record['status'] = 'skipped' if record.get('skip_reason') else 'passed'


def operate(args):
    if args.command == 'start':
        return start(args)
    if not args.run:
        states = inventory()
        if args.command == 'status':
            return [summary(s) for s in states]
        active = [s for s in states if not successor(s) and (s.get('schema_version') != 2 or current(s))]
        require(len(active) == 1, f'请指定 run。候选：{[s["run_id"] for s in active]}')
        args.run = active[0]['run_id']
    run = RUNS / identifier(args.run)
    require((run / 'state.json').is_file(), '找不到 run')
    with lock(run):
        state = load(args.run)
        replacement = successor(state)
        if args.command == 'status' or (replacement and args.command == 'resume'):
            return summary(state)
        require(not replacement, '原 run 已转为 feature，请恢复关联的新 run')
        if state.get('schema_version') != 2:
            if args.command != 'resume' or not args.adopt_legacy:
                raise GateError(json.dumps(summary(state), ensure_ascii=False))
            identifier(state['workflow'])
            require(state['workflow'] in ROUTES, '未知旧工作流')
            for key in ('feature_id', 'change_id', 'milestone', 'parent_run'):
                setattr(args, key, getattr(args, key, None) or state.get(key))
                if getattr(args, key):
                    identifier(getattr(args, key))
            if state['workflow'] == 'feature':
                require(args.feature_id and args.change_id, '迁移功能需要 --feature-id 和 --change-id')
            old = state
            args.request = args.request or old.get('request') or f'复核旧 run {args.run}'
            state = fresh(args, old['workflow'], args.run)
            state['history'].append(dict(time=now(), reason='迁移 v1，逐阶段复核', legacy=old))
        reconcile(run, state)
        stage = current(state)
        if args.command == 'resume':
            persist(run, state)
            return summary(state)
        require(stage and stage['id'] == args.stage, f'阶段已变化，当前为 {stage and stage["id"]}')
        key = stage['id']
        record = state['stages'][key]
        require(all(state['stages'][dep]['status'] in DONE for dep in stage['depends_on']), '上游未通过')
        if args.command == 'begin':
            require(not record.get('exhausted'), '重试已达上限，请先复核并显式 reopen')
            require(record['status'] in ('pending', 'failed', 'blocked', 'running'), '不能开始当前阶段')
            record.update(status='running')
            record.pop('reason', None)
        elif args.command == 'reopen':
            require(record.get('exhausted') and args.reason.strip(), '仅在复核重试上限后重开')
            failed_stage = record['exhausted']
            rewind(state, key, args.reason)
            state['stages'][failed_stage]['attempts'] = 0
            state['stages'][key] = dict(status='pending', attempts=state['stages'][key]['attempts'])
        elif args.command == 'fail':
            require(record['status'] in ('running', 'awaiting_approval'), '请先开始阶段')
            fail(state, stage, args)
        elif args.command == 'verify':
            require(record['status'] == 'running', '请先开始阶段')
            require(not record.get('failed_command'), '请先用 fail 对失败分类，再重试')
            result = verify(run, stage, record, args.key)
            persist(run, state)
            print(json.dumps(result, ensure_ascii=False), file=sys.stderr)
            require(result['exit_code'] == 0, '验证命令失败，请核对日志并按失败类型回退')
        elif args.command == 'advance':
            require(record['status'] == 'running', '请先开始阶段')
            record['artifacts'] = files(args)
            require(record['artifacts'], '请绑定实际阶段产物')
            if args.skip_reason is not None:
                require(stage['optional'] and args.skip_reason.strip(), '只有可选阶段可记录不适用')
                record['skip_reason'] = args.skip_reason.strip()
            gate(run, state, stage, record)
            if args.use_approval:
                reuse_design(state, stage, record, args.use_approval)
            elif stage['human_approval']:
                review = [state['run_id'], key, record['artifacts'], record.get('commit'), now()]
                record.update(status='awaiting_approval', review_token=fingerprint(review))
            else:
                record['status'] = 'skipped' if record.get('skip_reason') else 'passed'
        elif args.command == 'approve':
            require(record['status'] == 'awaiting_approval' and record['review_token'] == args.token,
                    '请展示当前产物版本并提供对应确认令牌')
            require(args.reply.strip(), '需要用户实际答复')
            gate(run, state, stage, record)
            state['approvals'][key] = dict(reply=args.reply, time=now(), artifacts=record['artifacts'],
                                          version=args.token, commit=record.get('commit'))
            record['status'] = 'skipped' if record.get('skip_reason') else 'passed'
        persist(run, state)
        return summary(state)


def parser():
    p = argparse.ArgumentParser(description='DevHarness 主控运行记录')
    sub = p.add_subparsers(dest='command', required=True)
    s = sub.add_parser('start')
    s.add_argument('workflow', choices=ROUTES)
    s.add_argument('--request', required=True)
    for key in ('run-id', 'change-id', 'feature-id', 'milestone', 'parent-run'):
        s.add_argument('--' + key)
    s.add_argument('--last-feature', action='store_true')
    for name in ('status', 'resume', 'begin', 'advance', 'verify', 'approve', 'fail', 'reopen'):
        cmd = sub.add_parser(name)
        if name in ('status', 'resume'):
            cmd.add_argument('run', nargs='?')
        else:
            cmd.add_argument('run')
            cmd.add_argument('stage')
        if name == 'resume':
            cmd.add_argument('--adopt-legacy', action='store_true')
            cmd.add_argument('--request')
            cmd.add_argument('--change-id')
            cmd.add_argument('--feature-id')
        if name == 'advance':
            cmd.add_argument('--artifact', action='append', required=True)
            cmd.add_argument('--skip-reason')
            cmd.add_argument('--use-approval', metavar='RUN/STAGE')
        if name == 'verify':
            cmd.add_argument('key')
        if name == 'approve':
            cmd.add_argument('--token', required=True)
            cmd.add_argument('--reply', required=True)
        if name == 'fail':
            cmd.add_argument('kind', choices=('execution', 'environment', 'code', 'requirements', 'ui'))
        if name in ('fail', 'reopen'):
            cmd.add_argument('--reason', required=True)
    return p


if __name__ == '__main__':
    try:
        print(json.dumps(operate(parser().parse_args()), indent=2, ensure_ascii=False))
    except (OSError, ValueError, TypeError, KeyError, subprocess.CalledProcessError) as exc:
        sys.exit(f'DevHarness: {exc}')
