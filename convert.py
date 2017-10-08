import os
import re
from glob import glob
import json


def get_path(path):
    if not os.path.isabs(path):
        path = os.path.join(os.path.dirname(__file__), path)
    return path

files = glob(get_path('filters/*.json'))
for file_ in files:
    print(file_)
    with open(get_path(file_), 'r', encoding="utf-8") as f:
        filters = json.load(f)
    with open(get_path(file_), 'w', encoding="utf-8") as f:
        json.dump(filters, f, indent=4)
