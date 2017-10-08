import os
import re
from glob import glob
import json


def get_path(path):
    if not os.path.isabs(path):
        path = os.path.join(os.path.dirname(__file__), path)
    return path

name_pattern = re.compile("(?<=\[)([^]]+)(?=\])")
coor_patter = re.compile("[-+]?[0-9]*\.?[0-9]*" + "[ \t]*,[ \t]*" +
                         "[-+]?[0-9]*\.?[0-9]*")
with open(get_path('geofences/geofence_stl.txt')) as f:
    lines = f.read().splitlines()
name = ''
content = ''
for line in lines:
    line = line.strip()
    match_name = name_pattern.search(line)
    if match_name:
        if name != '':
            with open(get_path('geofences/') + 'stl_' + name + '_geofence.txt', 'w') as f:
                f.write(content)
            content = ''
        name = match_name.group(0).lower()
    content += line + '\n'
with open(get_path('geofences/') + name + '_geofence.txt', 'w') as f:
    f.write(content)
