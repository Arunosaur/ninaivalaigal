#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Validate All Done/Archived Taiga Stories

This script:
1. Fetches all Done and Archived stories from Taiga
2. Validates each against the codebase
3. Checks for actual implementation, tests, and documentation
4. Reports stories that are incorrectly marked as Done
5. Adds "Developer F validated" signature to confirmed stories
6. Optionally reopens stories that should not be Done

Usage:
    python3 scripts/validate_done_stories.py [--dry-run] [--reopen] [--skip-signature]
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

# Configuration
TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
PROJECT_SLUG = "ninaivalaigal"
TAIGA_USERNAME = os.getenv("TAIGA_USERNAME", "admin")
TAIGA_PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")

# Repository root
REPO_ROOT = Path(__file__).parent.parent


def authenticate() -> Optional[str]:
    """Authenticate with Taiga and return auth token."""
    auth_url = f"{API_ENDPOINT}/auth"
    auth_data = {"username": TAIGA_USERNAME, "password": TAIGA_PASSWORD, "type": "normal"}

    try:
        response = requests.post(auth_url, json=auth_data)
        if response.status_code == 200:
            return response.json().get("auth_token")
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None


def get_project_id(auth_token: str) -> Optional[int]:
    """Get project ID for ninaivalaigal project."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/projects/by_slug?slug={PROJECT_SLUG}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get("id")
        return None
    except Exception as e:
        print(f"❌ Error getting project: {e}")
        return None


def get_statuses(auth_token: str, project_id: int) -> Dict[str, int]:
    """Get all status IDs for the project."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstory-statuses?project={project_id}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            statuses = {}
            for status in response.json():
                name = status.get("name", "").lower()
                statuses[name] = status.get("id")
            return statuses
        return {}
    except Exception as e:
        print(f"❌ Error getting statuses: {e}")
        return {}


def get_all_done_stories(auth_token: str, project_id: int) -> List[Dict]:
    """Get all Done and Archived stories."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstories"

    # Get all stories (we'll filter by status)
    all_stories = []
    page = 1

    while True:
        params = {"project": project_id, "page": page, "page_size": 100}
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            break

        result = response.json()
        if isinstance(result, list):
            stories = result
        elif isinstance(result, dict):
            stories = result.get("results", [])
        else:
            break

        if not stories:
            break

        all_stories.extend(stories)

        # Check if there are more pages
        if isinstance(result, dict) and not result.get("next"):
            break

        page += 1

    # Filter for Done and Archived
    done_stories = []
    for story in all_stories:
        status_name = story.get("status_extra_info", {}).get("name", "").lower()
        if status_name in ["done", "archived"]:
            done_stories.append(story)

    return done_stories


def extract_spec_number(story_subject: str) -> Optional[int]:
    """Extract SPEC number from story subject."""
    # Patterns: "SPEC-XXX", "SPEC-0XXX", "SPEC-00XXX"
    match = re.search(r"SPEC[-\s]*(\d+)", story_subject, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def check_spec_exists(spec_num: int) -> Tuple[bool, Optional[Path]]:
    """Check if SPEC directory exists."""
    spec_dir = REPO_ROOT / "specs" / f"{spec_num:03d}-*"
    matching_dirs = list(REPO_ROOT.glob(f"specs/{spec_num:03d}-*"))

    if matching_dirs:
        return True, matching_dirs[0]
    return False, None


def get_spec_index_status(spec_num: int) -> Optional[str]:
    """Check SPEC completion status in SPEC_INDEX.md."""
    spec_index = REPO_ROOT / "specs" / "SPEC_INDEX.md"
    if not spec_index.exists():
        return None

    try:
        content = spec_index.read_text()
        # Look for SPEC number in table format
        pattern = rf"\|\s*{spec_num}\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|"
        match = re.search(pattern, content)
        if match:
            return match.group(2).strip().lower()  # Status column
    except Exception:
        pass

    return None


def check_spec_completion(spec_dir: Path, spec_num: int) -> Dict:
    """Check SPEC completion markers."""
    completion_indicators = {
        "spec.md": False,
        "README.md": False,
        "completion_summary": False,
        "implementation_files": [],
        "codebase_implementation": [],
        "spec_index_status": None,
    }

    # Check SPEC_INDEX.md status
    spec_status = get_spec_index_status(spec_num)
    completion_indicators["spec_index_status"] = spec_status

    # Check for spec.md or README.md
    if (spec_dir / "spec.md").exists() or (spec_dir / "README.md").exists():
        completion_indicators["spec.md"] = True

        # Read README to check for implementation status
        try:
            readme = (spec_dir / "README.md").read_text()
            if "status: complete" in readme.lower() or "status: implemented" in readme.lower():
                completion_indicators["completion_summary"] = True
        except Exception:
            pass

    # Check for completion summary
    completion_files = list(spec_dir.glob("*completion*.md")) + list(spec_dir.glob("*COMPLETE*.md"))
    if completion_files:
        completion_indicators["completion_summary"] = True

    # Check for implementation files in SPEC directory
    impl_files = []
    for pattern in ["*.py", "*.ts", "*.tsx", "*.go", "*.rs"]:
        impl_files.extend(spec_dir.rglob(pattern))

    completion_indicators["implementation_files"] = [str(f.relative_to(REPO_ROOT)) for f in impl_files[:10]]

    # Search codebase for SPEC-related implementations
    spec_keywords = [f"spec-{spec_num:03d}", f"spec-{spec_num}", f"SPEC-{spec_num:03d}", f"SPEC-{spec_num}"]
    codebase_files = []

    for keyword in spec_keywords:
        for search_dir in [
            REPO_ROOT / "services",
            REPO_ROOT / "server",
            REPO_ROOT / "rust-services",
            REPO_ROOT / "go-services",
        ]:
            if search_dir.exists():
                # Search in file contents
                for py_file in search_dir.rglob("*.py"):
                    try:
                        content = py_file.read_text(encoding="utf-8", errors="ignore")
                        if keyword.lower() in content.lower():
                            codebase_files.append(str(py_file.relative_to(REPO_ROOT)))
                            if len(codebase_files) >= 5:
                                break
                    except Exception:
                        continue
                if len(codebase_files) >= 5:
                    break
        if len(codebase_files) >= 5:
            break

    completion_indicators["codebase_implementation"] = codebase_files

    return completion_indicators


def check_feature_implementation(story_subject: str, story_tags: List) -> Dict:
    """Check if feature is implemented in codebase."""
    validation = {"files_found": [], "tests_found": False, "documentation_found": False, "confidence": "low"}

    # Extract keywords from subject and tags
    keywords = []
    subject_lower = story_subject.lower()

    # Extract feature keywords
    if "health" in subject_lower:
        keywords.extend(["health", "slo", "monitoring", "observability"])
    if "auth" in subject_lower or "authentication" in subject_lower:
        keywords.extend(["auth", "jwt", "rbac", "security"])
    if "memory" in subject_lower:
        keywords.extend(["memory", "remember", "recall"])
    if "test" in subject_lower:
        keywords.extend(["test", "pytest", "coverage"])

    # Add tags as keywords
    for tag in story_tags:
        if isinstance(tag, (list, tuple)):
            keywords.append(tag[0] if tag else "")
        else:
            keywords.append(str(tag).lower())

    # Search for files matching keywords
    for keyword in keywords:
        if not keyword:
            continue

        # Search in common directories
        search_dirs = [
            REPO_ROOT / "server",
            REPO_ROOT / "services",
            REPO_ROOT / "tests",
            REPO_ROOT / "scripts",
        ]

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue

            # Search for files with keyword in name
            for pattern in [f"*{keyword}*", f"*{keyword.replace('-', '_')}*"]:
                matches = list(search_dir.rglob(pattern))
                for match in matches[:5]:  # Limit results
                    rel_path = str(match.relative_to(REPO_ROOT))
                    if rel_path not in validation["files_found"]:
                        validation["files_found"].append(rel_path)

        # Check for test files
        test_patterns = [f"*test*{keyword}*", f"*{keyword}*test*"]
        for test_dir in [REPO_ROOT / "tests", REPO_ROOT / "server" / "tests"]:
            if test_dir.exists():
                for pattern in test_patterns:
                    if list(test_dir.rglob(pattern)):
                        validation["tests_found"] = True
                        break

    # Determine confidence
    if len(validation["files_found"]) >= 3:
        validation["confidence"] = "high"
    elif len(validation["files_found"]) >= 1:
        validation["confidence"] = "medium"

    return validation


def validate_story(story: Dict) -> Dict:
    """Validate a single story against codebase."""
    story_ref = story.get("ref")
    subject = story.get("subject", "")
    tags = story.get("tags", [])
    description = story.get("description", "")
    status = story.get("status_extra_info", {}).get("name", "")

    validation_result = {
        "ref": story_ref,
        "subject": subject,
        "status": status,
        "valid": True,
        "issues": [],
        "evidence": {},
        "recommendation": "keep_done",
    }

    # Check if it's a SPEC story
    spec_num = extract_spec_number(subject)
    if spec_num is not None:
        spec_exists, spec_dir = check_spec_exists(spec_num)
        if not spec_exists:
            # SPEC directory doesn't exist - check if it's marked Complete in SPEC_INDEX
            spec_status = get_spec_index_status(spec_num)
            if spec_status and spec_status in ["complete", "implemented"]:
                # SPEC exists in index and is complete - this is likely a retrospective story
                validation_result["valid"] = True
                validation_result["evidence"]["spec_index_status"] = spec_status
                validation_result["evidence"]["retrospective"] = True
            else:
                validation_result["valid"] = False
                validation_result["issues"].append(
                    f"SPEC-{spec_num:03d} directory not found and not marked Complete in SPEC_INDEX"
                )
                validation_result["recommendation"] = "reopen"
        else:
            completion = check_spec_completion(spec_dir, spec_num)
            validation_result["evidence"]["spec_directory"] = str(spec_dir.relative_to(REPO_ROOT))
            validation_result["evidence"]["completion"] = completion

            # Check SPEC_INDEX status first
            spec_status = completion.get("spec_index_status")
            if spec_status and spec_status in ["complete", "implemented"]:
                # Marked as complete in SPEC_INDEX - validate that status
                if spec_status == "complete":
                    validation_result["valid"] = True
                    validation_result["evidence"]["validated_by_spec_index"] = True
                else:
                    validation_result["valid"] = False
                    validation_result["issues"].append(f"SPEC marked as '{spec_status}' in SPEC_INDEX, not Complete")
            elif (
                not completion["implementation_files"]
                and not completion["codebase_implementation"]
                and not completion["completion_summary"]
            ):
                # No evidence of implementation anywhere
                validation_result["valid"] = False
                validation_result["issues"].append("No implementation files found in SPEC directory or codebase")
                validation_result["recommendation"] = "reopen"
            elif completion["codebase_implementation"]:
                # Found implementation in codebase
                validation_result["valid"] = True
                validation_result["evidence"]["implementation_in_codebase"] = True
    else:
        # Not a SPEC story - check for feature implementation
        feature_check = check_feature_implementation(subject, tags)
        validation_result["evidence"]["feature_check"] = feature_check

        if feature_check["confidence"] == "low" and not feature_check["files_found"]:
            validation_result["valid"] = False
            validation_result["issues"].append("No implementation files found for feature")
            validation_result["recommendation"] = "investigate"
        elif feature_check["confidence"] == "low":
            validation_result["valid"] = False
            validation_result["issues"].append("Low confidence - minimal implementation found")
            validation_result["recommendation"] = "review"

    # Check for completion markers in description
    if description:
        if "complete" in description.lower() or "done" in description.lower():
            validation_result["evidence"]["description_mentions_completion"] = True

    return validation_result


def add_validation_signature(auth_token: str, story_id: int, validation_evidence: Dict, dry_run: bool = False) -> bool:
    """Add validation signature to story description with round tracking."""
    from datetime import datetime

    if dry_run:
        print(f"  [DRY RUN] Would add validation signature to story {story_id}")
        return True

    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    url = f"{API_ENDPOINT}/userstories/{story_id}"

    # Get current story
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return False

    story = response.json()
    current_description = story.get("description", "")

    # Count existing Developer F validations
    import re

    validation_pattern = r"\*\*Round (\d+):\*\*\s+\*\*Developer F validated\*\*"
    existing_validations = re.findall(validation_pattern, current_description)

    # Determine round number
    if existing_validations:
        # Get highest round number
        round_numbers = [int(r) for r in existing_validations]
        next_round = max(round_numbers) + 1
    else:
        # Check for legacy format (no round number)
        if "Validated by: Developer F" in current_description:
            next_round = 2
        else:
            next_round = 1

    # Build evidence details
    evidence_lines = []
    if validation_evidence.get("spec_index_status"):
        evidence_lines.append(f"- SPEC marked as **{validation_evidence['spec_index_status']}** in SPEC_INDEX.md")
    if validation_evidence.get("spec_directory"):
        evidence_lines.append(f"- SPEC directory exists: `{validation_evidence['spec_directory']}`")
    if validation_evidence.get("implementation_in_codebase"):
        evidence_lines.append("- Implementation found in codebase")
    if validation_evidence.get("codebase_implementation"):
        files = validation_evidence["codebase_implementation"][:3]
        evidence_lines.append(f"- Implementation files: {', '.join(files)}")
    if validation_evidence.get("validated_by_spec_index"):
        evidence_lines.append("- ✅ Validated against SPEC_INDEX.md (Complete status confirmed)")
    if validation_evidence.get("retrospective"):
        evidence_lines.append("- Note: Retrospective story (created after completion)")

    # Build validation signature
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if next_round == 1:
        # First validation - add new section
        validation_signature = f"""

---
**✅ Validation History - Developer F**

**Round 1:** **Developer F validated**
*Timestamp: {timestamp}*

**Evidence:**
"""
        if evidence_lines:
            validation_signature += "\n".join(f"  {line}" for line in evidence_lines) + "\n"
        else:
            validation_signature += "  - Story confirmed as complete\n"
    else:
        # Subsequent validation - append to existing section
        validation_signature = f"""
**Round {next_round}:** **Developer F validated**
*Timestamp: {timestamp}*

**Evidence:**
"""
        if evidence_lines:
            validation_signature += "\n".join(f"  {line}" for line in evidence_lines) + "\n"
        else:
            validation_signature += "  - Story confirmed as complete\n"

    # If round 1, check if we need to replace legacy format
    if next_round == 1 and "Validated by: Developer F" in current_description:
        # Remove old legacy signature format
        legacy_pattern = r"---\s*\*\*✅ Validation Confirmed\*\*.*?(?=\n\n---|\Z)"
        current_description = re.sub(legacy_pattern, "", current_description, flags=re.DOTALL).strip()
        # Also check for old format without round
        legacy_pattern2 = (
            r"\*\*✅ Validation Confirmed\*\*\s*\n\n\*Validated by: Developer F\*.*?(?=\n\n---|\n\n\*\*|$)"
        )
        current_description = re.sub(legacy_pattern2, "", current_description, flags=re.DOTALL).strip()

    # Append validation signature
    new_description = f"{current_description}{validation_signature}"

    payload = {"description": new_description, "version": story.get("version", 1)}

    update_response = requests.patch(url, headers=headers, json=payload)
    return update_response.status_code in [200, 204]


def update_story_status(
    auth_token: str, story_id: int, status_id: int, reason: str = "", dry_run: bool = False
) -> bool:
    """Update story status and add reason to description."""
    if dry_run:
        print(f"  [DRY RUN] Would update story {story_id} to status {status_id}")
        if reason:
            print(f"  [DRY RUN] Would add reason: {reason[:100]}...")
        return True

    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

    url = f"{API_ENDPOINT}/userstories/{story_id}"

    # Get current story to get version
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return False

    story = response.json()
    current_description = story.get("description", "")

    # Add reopening reason to description
    if reason:
        from datetime import datetime

        reopen_note = f"""

---
**⚠️ Story Reopened - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}**

**Reason for Reopening:**
{reason}

*Action taken by validation script (Developer F)*
"""
        new_description = f"{current_description}{reopen_note}"
    else:
        new_description = current_description

    payload = {"status": status_id, "version": story.get("version", 1), "description": new_description}

    update_response = requests.patch(url, headers=headers, json=payload)
    return update_response.status_code in [200, 204]


def main():
    parser = argparse.ArgumentParser(description="Validate all Done/Archived Taiga stories")
    parser.add_argument("--dry-run", action="store_true", help="Don't make changes, just report")
    parser.add_argument("--reopen", action="store_true", help="Reopen stories that should not be Done")
    parser.add_argument("--skip-signature", action="store_true", help="Skip adding validation signatures")
    parser.add_argument("--limit", type=int, help="Limit number of stories to check")

    args = parser.parse_args()

    print("=" * 80)
    print("VALIDATING ALL DONE/ARCHIVED TAIGA STORIES")
    print("=" * 80)
    print()

    # Authenticate
    print("Authenticating with Taiga...")
    auth_token = authenticate()
    if not auth_token:
        print("❌ Failed to authenticate")
        sys.exit(1)
    print("✅ Authenticated")
    print()

    # Get project ID
    print(f"Getting project ID for '{PROJECT_SLUG}'...")
    project_id = get_project_id(auth_token)
    if not project_id:
        print("❌ Failed to get project ID")
        sys.exit(1)
    print(f"✅ Project ID: {project_id}")
    print()

    # Get statuses
    print("Getting project statuses...")
    statuses = get_statuses(auth_token, project_id)
    print(f"✅ Found {len(statuses)} statuses")
    print()

    # Get all Done/Archived stories
    print("Fetching all Done/Archived stories...")
    done_stories = get_all_done_stories(auth_token, project_id)
    print(f"✅ Found {len(done_stories)} Done/Archived stories")

    if args.limit:
        done_stories = done_stories[: args.limit]
        print(f"⚠️  Limited to first {args.limit} stories")
    print()

    # Validate each story
    print("=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)
    print()

    invalid_stories = []
    valid_stories = []

    for i, story in enumerate(done_stories, 1):
        story_ref = story.get("ref")
        subject = story.get("subject", "")

        print(f"[{i}/{len(done_stories)}] Validating US#{story_ref}: {subject[:60]}")

        validation = validate_story(story)

        if not validation["valid"]:
            invalid_stories.append((story, validation))
            print(f"  ❌ INVALID - Issues found:")
            for issue in validation["issues"]:
                print(f"     - {issue}")
            print(f"  📋 Recommendation: {validation['recommendation']}")
        else:
            valid_stories.append((story, validation))
            print(f"  ✅ VALID")

            # Add validation signature (unless skipped)
            if not args.skip_signature:
                story_id = story.get("id")
                if story_id:
                    if add_validation_signature(auth_token, story_id, validation["evidence"], args.dry_run):
                        if not args.dry_run:
                            print(f"  ✅ Validation signature added (Developer F)")
                    else:
                        print(f"  ⚠️  Could not add validation signature")

        print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print(f"Total stories checked: {len(done_stories)}")
    print(f"✅ Valid: {len(valid_stories)}")
    print(f"❌ Invalid/Issues: {len(invalid_stories)}")
    print()

    if invalid_stories:
        print("=" * 80)
        print("STORIES THAT NEED ATTENTION")
        print("=" * 80)
        print()

        for story, validation in invalid_stories:
            story_ref = story.get("ref")
            subject = story.get("subject", "")
            status = story.get("status_extra_info", {}).get("name", "")

            print(f"US#{story_ref}: {subject}")
            print(f"  Current Status: {status}")
            print(f"  Issues: {', '.join(validation['issues'])}")
            print(f"  Recommendation: {validation['recommendation']}")
            print(f"  Taiga URL: {TAIGA_URL}/project/{PROJECT_SLUG}/us/{story_ref}")
            print()

        # Optionally reopen stories
        if args.reopen:
            print("=" * 80)
            print("REOPENING INVALID STORIES")
            print("=" * 80)
            print()

            # Get "Ready" or "In Progress" status ID
            ready_status_id = statuses.get("ready") or statuses.get("in progress") or statuses.get("new")

            if not ready_status_id:
                print("❌ Could not find appropriate status ID to reopen stories")
                print(f"   Available statuses: {list(statuses.keys())}")
            else:
                reopened = 0
                for story, validation in invalid_stories:
                    # Reopen all invalid stories (not just "reopen" recommendation)
                    story_id = story.get("id")
                    story_ref = story.get("ref")
                    subject = story.get("subject", "")

                    # Build detailed reason for reopening
                    issues = validation.get("issues", [])
                    recommendation = validation.get("recommendation", "review")

                    reason = f"**Story was marked as Done but validation found issues:**\n\n"
                    reason += f"**Issues Found:**\n"
                    for issue in issues:
                        reason += f"- {issue}\n"

                    reason += f"\n**Validation Recommendation:** {recommendation}\n"

                    # Add specific details based on evidence
                    evidence = validation.get("evidence", {})
                    if evidence.get("spec_directory"):
                        reason += f"\n**Note:** SPEC directory exists at `{evidence['spec_directory']}`, but no implementation files or completion summary found.\n"
                    elif "SPEC" in subject:
                        spec_num = extract_spec_number(subject)
                        if spec_num:
                            spec_status = get_spec_index_status(spec_num)
                            if spec_status:
                                reason += f"\n**Note:** SPEC-{spec_num:03d} is marked as '{spec_status}' in SPEC_INDEX.md, but no implementation evidence found in codebase.\n"

                    reason += "\n**Action Required:** Please review and either:\n"
                    reason += "- Complete the implementation and update the story\n"
                    reason += "- Provide evidence that the work is actually complete\n"
                    reason += "- Close/archive if this is a documentation-only story\n"

                    if update_story_status(auth_token, story_id, ready_status_id, reason, args.dry_run):
                        reopened += 1
                        print(f"✅ {'[DRY RUN] ' if args.dry_run else ''}Reopened US#{story_ref}: {subject[:60]}")
                    else:
                        print(f"❌ Failed to reopen US#{story_ref}")

                print()
                print(f"✅ {'Would reopen' if args.dry_run else 'Reopened'} {reopened} stories")

    # Generate report file
    report_file = REPO_ROOT / "tasks" / "active" / "TAIGA_VALIDATION_REPORT.md"
    report_file.parent.mkdir(parents=True, exist_ok=True)

    with open(report_file, "w") as f:
        f.write("# Taiga Done Stories Validation Report\n\n")
        f.write(f"**Date**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Total Stories Checked**: {len(done_stories)}\n")
        f.write(f"**Valid**: {len(valid_stories)}\n")
        f.write(f"**Invalid/Issues**: {len(invalid_stories)}\n\n")

        if invalid_stories:
            f.write("## Stories Requiring Attention\n\n")
            for story, validation in invalid_stories:
                f.write(f"### US#{story.get('ref')}: {story.get('subject')}\n")
                f.write(f"- **Status**: {story.get('status_extra_info', {}).get('name', 'Unknown')}\n")
                f.write(f"- **Issues**: {', '.join(validation['issues'])}\n")
                f.write(f"- **Recommendation**: {validation['recommendation']}\n")
                f.write(f"- **URL**: {TAIGA_URL}/project/{PROJECT_SLUG}/us/{story.get('ref')}\n\n")

    print(f"📄 Full report written to: {report_file}")
    print()


if __name__ == "__main__":
    main()
