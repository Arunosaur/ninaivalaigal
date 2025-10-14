#!/usr/bin/env python

import sys
import yaml

def repair_front_matter(content):
    parts = content.split('---')
    if len(parts) < 3:
        return f'---\n---\n{content}'
    try:
        front_matter = yaml.safe_load(parts[1])
        if not isinstance(front_matter, dict):
            front_matter = {}
    except yaml.YAMLError:
        front_matter = {}
    
    new_content = f'---\n{yaml.dump(front_matter)}---\n{'---'.join(parts[2:])}'
    return new_content

for filepath in sys.argv[1:]:
    try:
        with open(filepath, 'r+') as f:
            content = f.read()
            new_content = repair_front_matter(content)
            f.seek(0, 0)
            f.write(new_content)
            f.truncate()
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
