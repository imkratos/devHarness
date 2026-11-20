from pathlib import Path
import json,tomllib
root=Path(__file__).resolve().parents[2]
roles={tomllib.loads(p.read_text())['name'] for p in (root/'.codex/agents').glob('dh_*.toml')}
skills={p.parent.name for p in (root/'.agents/skills').glob('dh-*/SKILL.md')}
for p in (root/'.harness/workflows').glob('*.json'):
 d=json.loads(p.read_text()); seen=set()
 for s in d['stages']:
  assert s['id'] not in seen and set(s['depends_on'])<=seen,(p,s)
  assert s['skill'] in skills and (s['agent']=='main' or s['agent'] in roles),(p,s)
  seen.add(s['id'])
 print(p.name,'OK')
print(len(skills),'skills;',len(roles),'roles; static checks passed')
