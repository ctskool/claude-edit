"""Shared contracts; content hashes, atomic writes and selection freshness."""
import hashlib
import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MOVES = ROOT / 'templates/moves'
_hash_cache = {}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def file_hash(path):
    path = Path(path)
    if not path.is_file():
        return 'MISSING'
    stat = path.stat()
    key = (str(path.resolve()), stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
    if key not in _hash_cache:
        h = hashlib.sha256()
        with path.open('rb') as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b''):
                h.update(chunk)
        _hash_cache[key] = h.hexdigest()
    return _hash_cache[key]


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf8', newline='\n') as f:
            json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def move_dir(move_id):
    index = read(MOVES / 'index.json')
    row = next((m for m in index['moves'] if m['id'] == move_id), None)
    if not row:
        raise ValueError(f'unknown move {move_id}')
    path = (MOVES / row['path']).resolve()
    if not path.is_relative_to(MOVES.resolve()):
        raise ValueError('move path escapes templates/moves')
    return path


def move_of(option):
    move = read(move_dir(option['move_id']) / 'move.json')
    if move['revision'] != option['move_rev']:
        raise ValueError(f"move revision changed: {option['move_id']}")
    return move


def dependencies(project, options=None):
    project = Path(project).resolve()
    options = options or read(project / 'options.json')
    # Source files outside the project are workspace-relative, explicitly listed.
    paths = [ROOT / name for name in options['dependency_files']]
    paths += [project / 'options.json', MOVES / 'index.json']
    for decision in options['decisions']:
        for option in decision['options']:
            if option.get('move_id'):
                folder = move_dir(option['move_id'])
                paths += [folder / 'move.json', folder / 'snippet.js']
    # Include the actual frozen kit, template shell and captions used by this build.
    paths += list((project / 'kit').rglob('*')) + [project / 'caps.js', project / 'index.html']
    paths += list((project / 'assets/fonts').glob('*')) + list((project / 'assets/vendor').glob('*'))
    paths += [project / 'assets/face_half.mp4', project / 'assets/voice.m4a']
    return {os.path.relpath(p, ROOT).replace('\\', '/'): file_hash(p)
            for p in sorted(set(paths)) if not p.is_dir()}


def inherited(options):
    return {d['id']: {'option_id': d['pick'], 'provenance': 'inherited', 'note': ''}
            for d in options['decisions']}


def stale_reasons(project, picks, options=None):
    options = options or read(Path(project) / 'options.json')
    reasons = []
    if picks.get('options_rev') != options['options_rev']:
        reasons.append('options_rev changed')
    now, old = dependencies(project, options), picks.get('dependencies', {})
    reasons += [f'changed dependency: {p}' for p in sorted(set(now) | set(old)) if now.get(p) != old.get(p)]
    return reasons


def selection_inputs(project):
    project = Path(project)
    return {'options_sha256': file_hash(project / 'options.json'),
            'picks_sha256': file_hash(project / 'plan-picks.json'),
            'dependencies': dependencies(project)}


def current_selection(project, selection=None):
    project = Path(project)
    selection = selection or read(project / 'selection.json')
    if selection.get('selection_rev') != digest({k: v for k, v in selection.items() if k != 'selection_rev'}):
        raise ValueError('selection.json content changed after resolve; resolve again')
    if selection.get('inputs') != selection_inputs(project):
        raise ValueError('stale selection.json: options, picks or dependencies changed; resolve again')
    return selection
