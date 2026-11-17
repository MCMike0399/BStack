from pathlib import Path
import hashlib, json, re

root = Path(__file__).resolve().parent
m = json.loads((root / 'source-manifest.json').read_text())
for row in m['source_files']:
    data = (root / row['snapshot']).read_bytes()
    assert hashlib.sha256(data).hexdigest() == row['sha256'], row['source']
mode = (root / 'skills/burbi-mode/SKILL.md').read_text()
source = (root / 'upstream-reference/pstack/skills/poteto-mode/SKILL.md.txt').read_text()
assert 'name: burbi-mode\n' in mode
assert not re.search(r'^## (Subagents|Writing the reply|Playbooks)$', mode, re.M)
assert 'not adopted authorization' in mode
quote = mode.split('## Autonomy\n', 1)[1]
expected = source.split('## Autonomy\n\n', 1)[1].split('\n## Subagents', 1)[0].strip()
assert all(('> ' + line if line else '>') in quote.splitlines() for line in expected.splitlines())
assert len(m['staged_dependencies']) == 30
assert len(list((root / 'skills').glob('*/SKILL.md'))) == 31
for name in m['deferred_skills'] + m['deferred_companions']:
    assert not (root / 'skills' / name).exists(), name
for p in (root / 'skills').glob('*/SKILL.md'):
    s = p.read_text()
    assert 'disable-model-invocation: true' in s, p
    assert not re.search(r'(?im)^.*(?:spawn `?Task|^\s*- Starting any agent|^For a large or contested design, run)', s), p
    for link in re.findall(r'\]\(([^)]+)\)', s):
        if '://' not in link:
            assert (p.parent / link).exists(), (p, link)
for plugin in ['pstack', 'cursor-team-kit']:
    assert 'MIT License' in (root / 'licenses' / (plugin + '-LICENSE.txt')).read_text()
print('PASS: source hashes, 30 candidate dependencies + mode, 7 deferred skills + 2 deferred companions, cutoff, quoted pending autonomy, frontmatter, links, licenses.')
print('NOT TESTED: Claude Code loading, installation, runtime behavior. This remains a local draft.')
