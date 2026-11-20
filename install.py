from pathlib import Path
import shutil, sys
src=Path(__file__).resolve().parent
if len(sys.argv)!=2: raise SystemExit('usage: python3 install.py PROJECT_DIR')
dst=Path(sys.argv[1]).expanduser().resolve()
if dst==src or src in dst.parents: raise SystemExit('choose a separate project directory')
roots=['.agents','.codex','.harness','.planning','docs','AGENTS.md','LESSONS.md']
files=[f for x in roots for f in ([src/x] if (src/x).is_file() else (src/x).rglob('*')) if f.is_file()]
conflicts=[]
for f in files:
 t=dst/f.relative_to(src)
 if t.exists() and (not t.is_file() or t.read_bytes()!=f.read_bytes()): conflicts.append(str(t))
 if any(p.is_symlink() for p in [t,*t.parents] if p!=dst.parent): conflicts.append(str(t)+' (symlink)')
if conflicts: raise SystemExit('Conflicts; merge manually, no files copied:\n'+'\n'.join(conflicts))
for f in files:
 t=dst/f.relative_to(src);t.parent.mkdir(parents=True,exist_ok=True)
 if not t.exists(): shutil.copy2(f,t)
print(f'Installed {len(files)} project files into {dst}')
