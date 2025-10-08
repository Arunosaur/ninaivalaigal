#!/usr/bin/env python3
"""
Helper script for update-agent-context.sh
Updates agent context file with new technology information.
"""

import re
import sys
from datetime import datetime


def update_context_file(
    target_file: str,
    temp_file: str,
    new_lang: str,
    new_framework: str,
    new_db: str,
    new_project_type: str,
    current_branch: str,
) -> None:
    """Update agent context file with new tech stack information."""

    # Read existing file
    with open(target_file, "r") as f:
        content = f.read()

    # Check if new tech already exists
    tech_section = re.search(r"## Active Technologies\n(.*?)\n\n", content, re.DOTALL)
    if tech_section:
        existing_tech = tech_section.group(1)

        # Add new tech if not already present
        new_additions = []
        if new_lang and new_lang not in existing_tech:
            new_additions.append(f"- {new_lang} + {new_framework} ({current_branch})")
        if new_db and new_db not in existing_tech and new_db != "N/A":
            new_additions.append(f"- {new_db} ({current_branch})")

        if new_additions:
            updated_tech = existing_tech + "\n" + "\n".join(new_additions)
            content = content.replace(tech_section.group(0), f"## Active Technologies\n{updated_tech}\n\n")

    # Update project structure if needed
    if new_project_type == "web" and "frontend/" not in content:
        struct_section = re.search(r"## Project Structure\n```\n(.*?)\n```", content, re.DOTALL)
        if struct_section:
            updated_struct = struct_section.group(1) + "\nfrontend/src/      # Web UI"
            content = re.sub(
                r"(## Project Structure\n```\n).*?(\n```)",
                f"\\1{updated_struct}\\2",
                content,
                flags=re.DOTALL,
            )

    # Add new commands if language is new
    if new_lang and f"# {new_lang}" not in content:
        commands_section = re.search(r"## Commands\n```bash\n(.*?)\n```", content, re.DOTALL)
        if not commands_section:
            commands_section = re.search(r"## Commands\n(.*?)\n\n", content, re.DOTALL)

        if commands_section:
            new_commands = commands_section.group(1)
            if "Python" in new_lang:
                new_commands += "\ncd src && pytest && ruff check ."
            elif "Rust" in new_lang:
                new_commands += "\ncargo test && cargo clippy"
            elif "JavaScript" in new_lang or "TypeScript" in new_lang:
                new_commands += "\nnpm test && npm run lint"

            if "```bash" in content:
                content = re.sub(
                    r"(## Commands\n```bash\n).*?(\n```)",
                    f"\\1{new_commands}\\2",
                    content,
                    flags=re.DOTALL,
                )
            else:
                content = re.sub(
                    r"(## Commands\n).*?(\n\n)",
                    f"\\1{new_commands}\\2",
                    content,
                    flags=re.DOTALL,
                )

    # Update recent changes (keep only last 3)
    changes_section = re.search(r"## Recent Changes\n(.*?)(\n\n|$)", content, re.DOTALL)
    if changes_section:
        changes = changes_section.group(1).strip().split("\n")
        changes.insert(0, f"- {current_branch}: Added {new_lang} + {new_framework}")
        # Keep only last 3
        changes = changes[:3]
        content = re.sub(
            r"(## Recent Changes\n).*?(\n\n|$)",
            f"\\1{chr(10).join(changes)}\\2",
            content,
            flags=re.DOTALL,
        )

    # Update date
    content = re.sub(
        r"Last updated: \d{4}-\d{2}-\d{2}",
        f'Last updated: {datetime.now().strftime("%Y-%m-%d")}',
        content,
    )

    # Write to temp file
    with open(temp_file, "w") as f:
        f.write(content)


if __name__ == "__main__":
    if len(sys.argv) != 8:
        print(
            "Usage: update_agent_context.py <target_file> <temp_file> <new_lang> "
            "<new_framework> <new_db> <new_project_type> <current_branch>",
            file=sys.stderr,
        )
        sys.exit(1)

    update_context_file(
        target_file=sys.argv[1],
        temp_file=sys.argv[2],
        new_lang=sys.argv[3],
        new_framework=sys.argv[4],
        new_db=sys.argv[5],
        new_project_type=sys.argv[6],
        current_branch=sys.argv[7],
    )
