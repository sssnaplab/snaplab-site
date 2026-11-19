#!/usr/bin/env python3
"""Pull each app's current Play version into apps.json.

Runs android-signing-keys/play/play_publish.py status for every package and
writes the newest version on the alpha / production tracks. An app with a
completed production release becomes status "live". Review states (in review,
testers full) cannot be read from the API, so edit "status" by hand.

    python3 tools/sync_play.py          # update apps.json
    python3 tools/sync_play.py --dry    # show changes only
"""
import datetime, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLISH = os.path.expanduser('~/git/android-signing-keys/play/play_publish.py')
dry = '--dry' in sys.argv

path = os.path.join(ROOT, 'apps.json')
data = json.load(open(path, encoding='utf-8'))
changed = False
for app in data['apps']:
    out = subprocess.run([sys.executable, PUBLISH, '--package', app['package'], 'status'],
                         capture_output=True, text=True).stdout
    tracks = {}
    for line in out.splitlines():
        m = re.match(r'(\w+)\s+(\w+)\s+.*?\(?(\d+\.\d+(?:\.\d+)*)\)?\s*$', line.strip())
        if m:
            tracks[m.group(1)] = (m.group(2), m.group(3))
    if not tracks:
        print(f'{app["id"]}: no track info, skipped'); continue
    prod = tracks.get('production')
    ver = (prod or tracks.get('alpha') or next(iter(tracks.values())))[1]
    if ver != app['version']:
        print(f'{app["id"]}: version {app["version"]} -> {ver}'); app['version'] = ver; changed = True
    if prod and prod[0] == 'completed' and app['status'] != 'live':
        print(f'{app["id"]}: status {app["status"]} -> live'); app['status'] = 'live'; changed = True

if changed and not dry:
    data['updated'] = datetime.date.today().isoformat()
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2); f.write('\n')
    print('apps.json updated')
elif not changed:
    print('no changes')
