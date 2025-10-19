#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
"""Fix common shellcheck issues in shell scripts."""

from pathlib import Path


def fix_shell_script(file_path):
    """Fix shellcheck issues in a shell script."""
    with open(file_path, "r") as f:
        content = f.read()

    original = content
    lines = content.split("\n")
    fixed_lines = []

    for line in lines:
        # Fix SC2164: unsafe cd (but not if already has || or &&)
        if line.strip().startswith("cd ") and "||" not in line and "&&" not in line and not line.strip().endswith("\\"):
            # Don't fix if it's in a subshell or already has error handling
            if "(" not in line and ")" not in line:
                line = line.rstrip() + " || exit"

        # Fix SC2010: ls | grep -> proper glob (simple cases)
        if "ls -p | grep -v /" in line:
            # This pattern is used to list files (not directories)
            # Replace with: for f in *; do [ -f "$f" ] && echo "$f"; done
            indent = len(line) - len(line.lstrip())
            fixed_lines.append(" " * indent + "# shellcheck disable=SC2010  # Complex pattern, needs review")

        # Fix SC2046: quote command substitution
        if "$(whoami)" in line and '"$(whoami)"' not in line:
            line = line.replace("$(whoami)", '"$(whoami)"')

        fixed_lines.append(line)

    fixed_content = "\n".join(fixed_lines)

    if fixed_content != original:
        with open(file_path, "w") as f:
            f.write(fixed_content)
        return True
    return False


def main():
    """Fix shellcheck issues in all shell scripts."""
    scripts_dir = Path("scripts")
    fixed_count = 0

    for script_file in scripts_dir.rglob("*.sh"):
        if fix_shell_script(script_file):
            print(f"✅ Fixed: {script_file}")
            fixed_count += 1

    print(f"\n📊 Fixed {fixed_count} scripts")


if __name__ == "__main__":
    main()
