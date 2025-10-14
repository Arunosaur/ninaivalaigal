#!/usr/bin/env python

import os
import sys
import yaml

root_dir = 'specs'

def repair_front_matter(content):
    parts = content.split('---')
    if len(parts) < 3:
        return f'---\ntitle: "Untitled SPEC"\n---\n{content}'
    try:
        front_matter = yaml.safe_load(parts[1])
        if not isinstance(front_matter, dict):
            front_matter = {'title': 'Untitled SPEC'}
    except yaml.YAMLError:
        front_matter = {'title': 'Untitled SPEC'}
    
    new_content = f'---\n{yaml.dump(front_matter)}---\n{'---'.join(parts[2:])}'
    return new_content

for dir_name, _, files in os.walk(root_dir):
    for file in files:
        if file.lower() == 'readme.md':
            filepath = os.path.join(dir_name, file)
            try:
                with open(filepath, 'r+') as f:
                    content = f.read()
                    new_content = repair_front_matter(content)
                    f.seek(0, 0)
                    f.write(new_content)
                    f.truncate()
            except Exception as e:
                print(f"Error processing {filepath}: {e}")

print("Front-matter cleanup complete.")
