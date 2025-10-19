#!/usr/bin/env python
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#

"""Audit YAML front matter in markdown files."""
import os

root_dir = "specs"
missing_front_matter = []

for dir_name, _, _ in os.walk(root_dir):
    if not any(char.isdigit() for char in os.path.basename(dir_name)):
        continue

    readme_path = os.path.join(dir_name, "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r") as f:
            content = f.read()
            if not content.startswith("---"):
                missing_front_matter.append(readme_path)

if missing_front_matter:
    print("SPECs missing YAML front-matter:")
    for spec in missing_front_matter:
        print(f"  - {spec}")
else:
    print("All SPECs have YAML front-matter.")
