import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
CHECK = Path('.harness/scripts/check.py')
NEW_FILES = ('.harness/scripts/harness.py', '.harness/scripts/gate.py', '.harness/cli.md')


def read_json(path):
    return json.loads(path.read_text())


def write_json(path, value):
    path.write_text(json.dumps(value))


class ChecksTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.temp = Path(temp.name)
        self.kit = self.temp / 'kit'
        self.project = self.temp / 'project'
        manifest = ROOT / 'install-manifest.txt'
        for name in (*manifest.read_text().splitlines(), manifest.name, 'install.py'):
            path = ROOT / name
            dest = self.kit / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, dest)

    def cli(self, script, *args, ok=True):
        result = subprocess.run([sys.executable, '-B', '-O', self.kit / script, *args],
                                cwd=self.temp, text=True, capture_output=True)
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertNotIn('Traceback', result.stderr)
        return result

    def test_install_manifest_and_repeat(self):
        private = ('.harness/runs/x/state.json', '.harness/project.json', '.agents/skills/dh-secret/SKILL.md',
                   '.codex/agents/dh_private.toml', 'docs/local.md', 'examples/x.txt', '.harness/scripts/__pycache__/x.pyc')
        for name in private:
            path = self.kit / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('private')
        self.cli('install.py', self.project)
        for name in private:
            self.assertFalse((self.project / name).exists(), name)
        for name in (*NEW_FILES, str(CHECK), '.harness/project.example.json'):
            self.assertEqual((self.project / name).read_bytes(), (self.kit / name).read_bytes())
        before = (self.project / 'AGENTS.md').stat().st_mtime_ns
        self.cli('install.py', self.project)
        self.assertEqual(before, (self.project / 'AGENTS.md').stat().st_mtime_ns)
        self.cli(self.project / CHECK)

    def test_install_preflight_conflicts(self):
        self.project.mkdir()
        path = self.project / 'docs'
        path.write_text('preserve')
        self.cli('install.py', self.project, ok=False)
        self.assertEqual(list(self.project.iterdir()), [path])
        self.assertEqual(path.read_text(), 'preserve')

    def test_conflicting_file_and_nested_symlink(self):
        self.project.mkdir()
        existing = self.project / 'AGENTS.md'
        existing.write_text('project rules')
        self.cli('install.py', self.project, ok=False)
        self.assertEqual(existing.read_text(), 'project rules')
        existing.unlink()
        scripts = self.project / '.harness'
        scripts.symlink_to(self.temp / 'missing', target_is_directory=True)
        self.cli('install.py', self.project, ok=False)
        self.assertEqual(list(self.project.iterdir()), [scripts])

    def test_copy_failure_rolls_back_only_new_files(self):
        self.project.mkdir()
        existing = self.project / 'AGENTS.md'
        shutil.copyfile(self.kit / existing.name, existing)
        spec = importlib.util.spec_from_file_location('installer', self.kit / 'install.py')
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        copy = shutil.copy2

        def fail_in_middle(src, dst):
            if src.name == 'dh_architect.toml':
                raise OSError('copy interrupted')
            return copy(src, dst)

        with patch.object(installer.shutil, 'copy2', fail_in_middle):
            with self.assertRaisesRegex(OSError, 'copy interrupted'):
                installer.install(self.project)
        self.assertEqual(list(self.project.iterdir()), [existing])

    def test_destination_symlink(self):
        outside = self.temp / 'outside'
        outside.mkdir()
        self.project.symlink_to(outside, target_is_directory=True)
        self.cli('install.py', self.project, ok=False)
        self.assertEqual(list(outside.iterdir()), [])

    def test_missing_release_file(self):
        (self.kit / NEW_FILES[0]).unlink()
        self.cli('install.py', self.project, ok=False)
        self.assertFalse(self.project.exists())

    def test_source_symlink(self):
        source = self.kit / NEW_FILES[0]
        source.unlink()
        source.symlink_to(self.kit / 'AGENTS.md')
        self.cli('install.py', self.project, ok=False)
        self.assertFalse(self.project.exists())

    def test_role_skills_from_instructions(self):
        self.cli(CHECK)
        path = self.kit / '.codex/agents/dh_architect.toml'
        text = path.read_text().replace('domain-modeling', 'implement-task')
        path.write_text(text + '\n# 适用技能：domain-modeling。\n')
        result = self.cli(CHECK, ok=False)
        self.assertIn('domain-modeling', result.stderr)

    def test_workflow_contract(self):
        path = self.kit / '.harness/workflows/refactor.json'
        for change in ('version', 'name', 'empty', 'forward dependency', 'duplicate id', 'attempts', 'flag', 'missing'):
            with self.subTest(change=change):
                doc = read_json(path)
                if change == 'empty':
                    doc['stages'] = []
                if change == 'version':
                    doc['version'] = 1
                if change == 'name':
                    doc['name'] = 'feature'
                if change == 'forward dependency':
                    doc['stages'][0]['depends_on'] = [doc['stages'][-1]['id']]
                if change == 'duplicate id':
                    doc['stages'][-1]['id'] = doc['stages'][0]['id']
                if change == 'attempts':
                    doc['stages'][0]['max_attempts'] = True
                if change == 'flag':
                    doc['stages'][0]['optional'] = 'false'
                original = path.read_bytes()
                if change == 'missing':
                    path.unlink()
                else:
                    write_json(path, doc)
                self.cli(CHECK, ok=False)
                path.write_bytes(original)

    def test_state_template(self):
        path = self.kit / '.harness/templates/state.json'
        write_json(path, {**read_json(path), 'workflow': 'feature'})
        self.cli(CHECK, ok=False)

    def test_malformed_templates(self):
        for name, key, value in [('acceptance', 'evidence', {}), ('tasks', 'depends_on', 'TASK-001'),
                                 ('tasks', 'requirements', None), ('state', 'stages', [])]:
            with self.subTest(template=name, field=key):
                path = self.kit / f'.harness/templates/{name}.json'
                original = path.read_bytes()
                data = read_json(path)
                row = data if name == 'state' else data[0]
                row[key] = value
                write_json(path, data)
                self.cli(CHECK, ok=False)
                path.write_bytes(original)

    def test_project_commands(self):
        self.cli('install.py', self.project)
        self.cli(CHECK, '--project', self.project, ok=False)
        path = self.project / '.harness/project.json'
        path.write_text('{')
        self.cli(CHECK, '--project', self.project, ok=False)
        config = read_json(self.project / '.harness/project.example.json')
        config['project_id'] = 'demo'
        write_json(path, config)
        self.cli(self.project / CHECK, '--project')
        self.cli(CHECK, '--project', self.project, '--require-command', 'unit', ok=False)
        config['commands']['unit'] = 'touch should-never-run'
        write_json(path, config)
        self.cli(CHECK, '--project', self.project, '--require-command', 'unit')
        self.assertFalse((self.temp / 'should-never-run').exists())
        for key, value in [('max_parallel', False), ('max_parallel', 4), ('max_attempts', 0),
                           ('production_release_requires_approval', False), ('project_id', 'replace-me'),
                           ('commands', {'unit': []})]:
            with self.subTest(field=key, value=value):
                write_json(path, {**config, key: value})
                self.cli(CHECK, '--project', self.project, ok=False)


if __name__ == '__main__':
    unittest.main()
