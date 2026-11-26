"""Statically validate DevHarness definitions and project command configuration."""
import argparse
import json
from pathlib import Path
import re
import tomllib


ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = {'project-init', 'feature', 'bugfix', 'refactor'}


def require(condition, path, message):
    if not condition:
        raise ValueError(f'{path}: {message}')


def text(value):
    return isinstance(value, str) and bool(value.strip())


def positive_integer(value):
    return type(value) is int and value > 0


def load(path, parse=json.loads):
    try:
        return parse(path.read_text(encoding='utf-8'))
    except ValueError as error:
        raise ValueError(f'{path}: {error}') from error


def check_skills(root):
    skills = set()
    for path in sorted(root.glob('.agents/skills/dh-*/SKILL.md')):
        parts = path.read_text(encoding='utf-8').splitlines()
        require(parts and parts[0] == '---' and '---' in parts[1:], path, 'missing front matter')
        header = parts[1:parts.index('---', 1)]
        for key in ('name', 'description'):
            values = [line.split(':', 1)[1].strip() for line in header if line.startswith(key + ':')]
            require(len(values) == 1 and text(values[0]), path, f'invalid {key}')
            if key == 'name':
                require(values[0] == path.parent.name, path, 'name must match skill directory')
        skills.add(path.parent.name)
    return skills


def check_roles(root, skills):
    roles = {}
    for path in sorted(root.glob('.codex/agents/dh_*.toml')):
        role = load(path, tomllib.loads)
        require(role.get('name') == path.stem and text(role.get('description')), path, 'invalid role metadata')
        instructions = role.get('developer_instructions')
        require(text(instructions), path, 'missing developer_instructions')
        lines = re.findall(r'^适用技能[：:]\s*([^。\n]+)', instructions, re.MULTILINE)
        require(len(lines) == 1, path, 'expected one 适用技能 line')
        declared = {'dh-' + item.strip().removeprefix('dh-') for item in re.split('[,，、]', lines[0])}
        require(declared <= skills, path, f'unknown skills {sorted(declared - skills)}')
        roles[path.stem] = declared
    return roles


def check_workflows(root, skills, roles):
    folder = root / '.harness/workflows'
    names = {path.stem for path in folder.glob('*.json')}
    require(names == WORKFLOWS, folder, f'unexpected or missing workflows {sorted(names ^ WORKFLOWS)}')
    for name in sorted(WORKFLOWS):
        path = folder / (name + '.json')
        data = load(path)
        require(isinstance(data, dict) and data.get('name') == name, path, 'invalid workflow name')
        require(type(data.get('version')) is int and data['version'] == 2, path, 'expected version 2')
        stages = data.get('stages')
        require(isinstance(stages, list) and stages, path, 'expected nonempty stages')
        seen = set()
        for stage in stages:
            require(isinstance(stage, dict), path, 'invalid stage')
            ident = stage.get('id')
            location = f'{path} [{ident}]'
            require(text(ident) and ident not in seen, location, 'invalid or duplicate id')
            deps = stage.get('depends_on')
            require(isinstance(deps, list) and all(text(dep) and dep in seen for dep in deps)
                    and len(deps) == len(set(deps)), location, 'expected unique preceding dependencies')
            agent, skill = stage.get('agent'), stage.get('skill')
            require(text(skill) and skill in skills, location, f'unknown skill {skill}')
            require(text(agent) and (agent == 'main' or skill in roles.get(agent, set())),
                    location, f'{agent} does not declare {skill}')
            for key in ('human_approval', 'optional'):
                require(type(stage.get(key)) is bool, location, f'{key} must be boolean')
            require(positive_integer(stage.get('max_attempts')), location, 'invalid max_attempts')
            seen.add(ident)


def check_templates(root):
    folder = root / '.harness/templates'
    path = folder / 'state.json'
    state = load(path)
    require(isinstance(state, dict) and 'workflow' in state and state['workflow'] is None,
            path, 'workflow must be null until a run is initialized')
    for key in ('stages', 'artifacts', 'approvals'):
        require(isinstance(state.get(key), dict), path, f'{key} must be an object')
    require(isinstance(state.get('blockers'), list), path, 'blockers must be a list')
    templates = {
        'acceptance': (('id', 'requirement_ref', 'scenario', 'expected', 'verification', 'status'), ('evidence',)),
        'tasks': (('id', 'agent', 'status'), ('depends_on', 'requirements', 'acceptance',
                                              'inputs', 'write_scope', 'verification')),
    }
    for name, (strings, lists) in templates.items():
        path = folder / (name + '.json')
        rows = load(path)
        require(isinstance(rows, list) and rows, path, 'expected nonempty template array')
        for row in rows:
            require(isinstance(row, dict), path, 'invalid template entry')
            for key in strings:
                require(text(row.get(key)), path, f'{key} must be nonempty text')
            for key in lists:
                require(isinstance(row.get(key), list) and all(text(item) for item in row[key]),
                        path, f'{key} must be a list of strings')


def check_project(path, example, required):
    config = load(path)
    require(isinstance(config, dict), path, 'expected project object')
    project_id = config.get('project_id')
    require(text(project_id) and (example or project_id.strip() != 'replace-me'), path, 'invalid project_id')
    require(isinstance(config.get('stack'), dict), path, 'stack must be an object')
    require(config.get('production_release_requires_approval') is True, path, 'production approval must be enabled')
    for key in ('max_parallel', 'max_attempts'):
        require(positive_integer(config.get(key)), path, f'{key} must be a positive integer')
    require(config['max_parallel'] <= 3, path, 'max_parallel exceeds protocol limit of 3')
    require(config.get('app_url') is None or text(config['app_url']), path, 'invalid app_url')
    commands = config.get('commands')
    require(isinstance(commands, dict), path, 'commands must be an object')
    for name, command in commands.items():
        require(text(name) and (command is None or text(command)), path, f'invalid command {name!r}')
    for name in required:
        require(text(commands.get(name)), path, f'missing required command {name!r}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', nargs='?', type=Path, const=ROOT, metavar='DIR',
                        help='validate the installed project (default directory: script installation root)')
    parser.add_argument('--require-command', action='append', default=[], metavar='NAME',
                        help='require a configured command for this stage; repeat for additional commands')
    args = parser.parse_args()
    root = args.project.resolve() if args.project else ROOT
    config = root / '.harness/project.json'
    project_mode = args.project is not None or config.exists() or bool(args.require_command)
    try:
        skills = check_skills(root)
        roles = check_roles(root, skills)
        check_workflows(root, skills, roles)
        check_templates(root)
        check_project(root / '.harness/project.example.json', True, [])
        if project_mode:
            check_project(config, False, args.require_command)
    except (ValueError, OSError) as error:
        parser.exit(1, f'{error}\n')
    print(f'{len(WORKFLOWS)} workflows, {len(skills)} skills, {len(roles)} roles; '
          f'{"project" if project_mode else "toolkit"} static checks passed')


if __name__ == '__main__':
    main()
