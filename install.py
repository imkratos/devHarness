"""Install the DevHarness distribution without replacing project files."""
import argparse
import os
from pathlib import Path
import shutil
import sys
import tempfile


SOURCE = Path(__file__).resolve().parent


def release_files():
    manifest = SOURCE / 'install-manifest.txt'
    if manifest.is_symlink():
        raise ValueError(f'symlink: {manifest}')
    names = manifest.read_text(encoding='utf-8').splitlines()
    if not names or len(set(names)) != len(names):
        raise ValueError('empty or duplicate release manifest entries')
    for name in names:
        path = Path(name)
        if not path.parts or path.is_absolute() or '..' in path.parts or name != path.as_posix():
            raise ValueError(f'invalid manifest entry: {name!r}')
        source = SOURCE / path
        if source.resolve() != source or not source.is_file():
            raise ValueError(f'missing or symlinked release file: {source}')
        yield path


def destination(directory):
    path = directory.expanduser().absolute()
    # On macOS /tmp and /var are standard aliases for /private/tmp and /private/var.
    for ancestor in (*reversed(path.parents), path):
        if sys.platform == 'darwin' and ancestor in (Path('/tmp'), Path('/var')):
            if ancestor.resolve() == Path('/private') / ancestor.name:
                continue
        if ancestor.is_symlink():
            raise ValueError(f'symlink in destination: {ancestor}')
    target = path.resolve()
    if target == SOURCE or SOURCE in target.parents:
        raise ValueError('choose a separate project directory')
    return target


def install(directory, merged=()):
    target = destination(directory)
    missing = []
    conflicts = set()
    paths = list(release_files())
    merged = set(merged)
    unknown = merged.difference(path.as_posix() for path in paths)
    if unknown:
        raise ValueError('Not in release manifest: ' + ', '.join(sorted(unknown)))
    for path in paths:
        dest = target / path
        for parent in (dest.parent, *dest.parent.parents):
            if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
                conflicts.add(str(parent))
                break
        else:
            if path.as_posix() in merged:
                if dest.is_symlink() or not dest.is_file():
                    conflicts.add(str(dest))
            elif dest.is_symlink() or (dest.exists() and
                    (not dest.is_file() or dest.read_bytes() != (SOURCE / path).read_bytes())):
                conflicts.add(str(dest))
            elif not dest.exists():
                missing.append(path)
    if conflicts:
        raise ValueError('Conflicts; merge manually, no files copied:\n' + '\n'.join(sorted(conflicts)))

    created_files = []
    created_dirs = []
    try:
        for path in missing:
            dest = target / path
            absent = []
            for parent in dest.parents:
                if parent.exists():
                    break
                absent.append(parent)
            for parent in reversed(absent):
                try:
                    parent.mkdir()
                except FileExistsError:
                    if parent.is_symlink() or not parent.is_dir():
                        raise
                else:
                    created_dirs.append(parent)
            # Publish complete files exclusively, including on a concurrent retry.
            with tempfile.NamedTemporaryFile(dir=dest.parent, delete=False) as staged:
                staged_path = Path(staged.name)
            try:
                shutil.copy2(SOURCE / path, staged_path)
                try:
                    os.link(staged_path, dest)
                except FileExistsError:
                    if dest.is_symlink() or not dest.is_file() or dest.read_bytes() != staged_path.read_bytes():
                        raise
                else:
                    created_files.append(dest)
            finally:
                staged_path.unlink()
    except BaseException:
        for dest in reversed(created_files):
            dest.unlink(missing_ok=True)
        for parent in reversed(created_dirs):
            if not any(parent.iterdir()):
                parent.rmdir()
        raise
    return len(created_files)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project_dir', type=Path, metavar='PROJECT_DIR')
    parser.add_argument('--merged', action='append', default=[], metavar='PATH',
                        help='保留已手工合并的清单内文件，填写清单相对路径，可重复')
    args = parser.parse_args()
    try:
        count = install(args.project_dir, args.merged)
    except (ValueError, OSError, RuntimeError) as error:
        parser.exit(1, f'{error}\n')
    print(f'Installed {count} new project files into {args.project_dir}')
