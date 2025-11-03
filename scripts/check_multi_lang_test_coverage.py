#!/usr/bin/env python3
"""
Multi-Language Test Coverage Checker

Checks that new/modified code in Python, TypeScript/JavaScript, Rust, and Go
has corresponding test files. Also validates existing code coverage.

Usage:
    python scripts/check_multi_lang_test_coverage.py --check-new-files
    python scripts/check_multi_lang_test_coverage.py --analyze-coverage
    python scripts/check_multi_lang_test_coverage.py --language python
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class MultiLangTestChecker:
    """Check test coverage across multiple programming languages."""

    def __init__(self, root: Path = None):
        self.root = Path(root) if root else Path.cwd()
        self.languages = {
            "python": {
                "extensions": [".py"],
                "test_patterns": [
                    "tests/test_{name}.py",
                    "tests/unit/test_{name}.py",
                    "tests/integration/test_{name}.py",
                    "tests/{module}/test_{name}.py",
                    "{dir}/tests/test_{name}.py",
                    "{dir}/test_{name}.py",
                ],
                "source_dirs": ["server/", "services/", "shared/", "mcp_server/", "rbac/", "utils/", "python-clients/"],
                "test_command": "pytest --cov={path} --cov-report=term-missing",
                "exclude_patterns": ["__pycache__", "migrations", "alembic", "test_", "_test.py"],
            },
            "typescript": {
                "extensions": [".ts", ".tsx"],
                "test_patterns": [
                    "{dir}/__tests__/{name}.test.{ext}",
                    "{dir}/{name}.test.{ext}",
                    "tests/{name}.test.{ext}",
                    "{dir}/tests/{name}.test.{ext}",
                ],
                "source_dirs": [
                    "frontend/",
                    "frontend-nextjs/",
                    "frontend-nextjs-customer/",
                    "frontend-shared/",
                    "apps/",
                    "packages/",
                ],
                "test_command": "npm run test:coverage",
                "exclude_patterns": [".test.", ".spec.", "__tests__"],
            },
            "rust": {
                "extensions": [".rs"],
                "test_patterns": [
                    "tests/{name}_test.rs",
                    "tests/{name}.rs",
                    "{dir}/{name}_test.rs",
                ],
                "source_dirs": ["rust-services/", "services/memory-service-rust/"],
                "test_command": "cargo test --all-targets",
            },
            "go": {
                "extensions": [".go"],
                "test_patterns": [
                    "{name}_test.go",
                    "{dir}/{name}_test.go",
                ],
                "source_dirs": ["go-services/", "shared/"],
                "test_command": "go test -v -coverprofile=coverage.out ./...",
                "exclude_patterns": ["_test.go", ".pb.go"],  # Exclude generated files and test files
            },
            "java": {
                "extensions": [".java"],
                "test_patterns": [
                    "{dir}/{name}Test.java",
                    "test/{dir}/{name}Test.java",
                    "tests/{dir}/{name}Test.java",
                ],
                "source_dirs": ["jetbrains-plugin/"],
                "test_command": "gradle test",
            },
        }

    def find_test_file(self, source_file: Path, language: str) -> Optional[Path]:
        """Find corresponding test file for a source file."""
        lang_config = self.languages.get(language)
        if not lang_config:
            return None

        source_file = Path(source_file)
        if not source_file.is_absolute():
            source_file = self.root / source_file

        # Skip test files themselves
        if any(part in str(source_file) for part in ["test", "spec", "__tests__"]):
            return None

        # Check if file is in a source directory
        source_dirs = lang_config.get("source_dirs", [])
        if not any(dir_path in str(source_file) for dir_path in source_dirs):
            return None

        # Extract base name and directory
        name_without_ext = source_file.stem
        directory = source_file.parent
        relative_dir = directory.relative_to(self.root) if directory != self.root else Path("")

        # Try each test pattern
        test_patterns = lang_config.get("test_patterns", [])
        for pattern in test_patterns:
            try:
                # Extract module name from relative path if available
                parts = str(relative_dir).split("/")
                module = parts[-1] if parts and parts[-1] else ""

                test_path_str = pattern.format(
                    name=name_without_ext,
                    dir=str(relative_dir),
                    module=module,
                    ext=source_file.suffix[1:] if source_file.suffix else "ts",
                )
                test_path = self.root / test_path_str
                if test_path.exists():
                    return test_path
            except KeyError:
                # Skip patterns that require keys we don't have
                continue

        # Special handling for TypeScript/JavaScript - check __tests__ directories
        if language == "typescript":
            # Check for __tests__ directory at same level
            test_dir = directory / "__tests__"
            if test_dir.exists():
                for ext in ["ts", "tsx"]:
                    test_file = test_dir / f"{name_without_ext}.test.{ext}"
                    if test_file.exists():
                        return test_file

        # Special handling for Go - check same directory
        if language == "go":
            test_file = directory / f"{name_without_ext}_test.go"
            if test_file.exists():
                return test_file

        # Special handling for Rust - check tests/ directory
        if language == "rust":
            # Check tests/ directory at project root level
            if "rust-services" in str(source_file):
                project_root = None
                for parent in source_file.parents:
                    if parent.name in ["graphops", "memory-service"]:
                        project_root = parent
                        break
                if project_root:
                    tests_dir = project_root / "tests"
                    if tests_dir.exists():
                        for test_file in tests_dir.glob(f"*{name_without_ext}*"):
                            if test_file.suffix == ".rs":
                                return test_file
            # Also check inline tests (difficult to verify programmatically, but we can check if file has #[cfg(test)])
            # For now, we'll rely on explicit test files

        return None

    def detect_language(self, file_path: Path) -> Optional[str]:
        """Detect programming language from file extension."""
        ext = file_path.suffix.lower()
        for lang, config in self.languages.items():
            if ext in config.get("extensions", []):
                return lang
        return None

    def get_staged_files(self) -> List[Path]:
        """Get list of newly staged files from git."""
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only", "--diff-filter=A"],
                capture_output=True,
                text=True,
                check=True,
                cwd=self.root,
            )
            return [Path(f) for f in result.stdout.strip().split("\n") if f]
        except subprocess.CalledProcessError:
            return []

    def get_changed_files(self) -> List[Path]:
        """Get list of changed files in current branch."""
        try:
            # Try main first, then master
            for branch in ["origin/main", "origin/master"]:
                try:
                    result = subprocess.run(
                        ["git", "diff", "--name-only", "--diff-filter=AM", f"{branch}...HEAD"],
                        capture_output=True,
                        text=True,
                        check=True,
                        cwd=self.root,
                    )
                    if result.stdout.strip():
                        return [Path(f) for f in result.stdout.strip().split("\n") if f]
                except subprocess.CalledProcessError:
                    continue
            return []
        except Exception:
            return []

    def check_new_files(self) -> Tuple[bool, Dict[str, List[Path]]]:
        """Check if newly added files have test files."""
        new_files = self.get_staged_files()
        missing_tests = {}

        for new_file in new_files:
            language = self.detect_language(new_file)
            if not language:
                continue

            # Check if file is in a source directory
            lang_config = self.languages.get(language, {})
            source_dirs = lang_config.get("source_dirs", [])
            if not any(dir_path in str(new_file) for dir_path in source_dirs):
                continue

            test_file = self.find_test_file(new_file, language)
            if not test_file:
                if language not in missing_tests:
                    missing_tests[language] = []
                missing_tests[language].append(new_file)

        return len(missing_tests) == 0, missing_tests

    def analyze_coverage(self, language: Optional[str] = None) -> Dict[str, any]:
        """Analyze test coverage for specified language(s)."""
        results = {}

        languages_to_check = [language] if language else self.languages.keys()

        for lang in languages_to_check:
            lang_config = self.languages.get(lang, {})
            source_dirs = lang_config.get("source_dirs", [])

            # Find all source files
            source_files = []
            for source_dir in source_dirs:
                source_path = self.root / source_dir
                if source_path.exists():
                    for ext in lang_config.get("extensions", []):
                        source_files.extend(source_path.rglob(f"*{ext}"))

            # Filter out test files and generated files
            exclude_keywords = [
                "test",
                "spec",
                "__tests__",
                "node_modules",
                "target",
                "dist",
                "__pycache__",
                ".pb.go",
                "pb.go",
            ]
            exclude_patterns = lang_config.get("exclude_patterns", [])
            exclude_keywords.extend(exclude_patterns)

            source_files = [
                f
                for f in source_files
                if not any(
                    part in str(f) or any(f.name.endswith(pattern) for pattern in exclude_patterns)
                    for part in exclude_keywords
                )
            ]

            # Check which have tests
            files_with_tests = 0
            files_without_tests = []

            for source_file in source_files:
                test_file = self.find_test_file(source_file, lang)
                if test_file:
                    files_with_tests += 1
                else:
                    files_without_tests.append(source_file.relative_to(self.root))

            coverage_percent = (files_with_tests / len(source_files) * 100) if source_files else 0

            results[lang] = {
                "total_files": len(source_files),
                "files_with_tests": files_with_tests,
                "files_without_tests": len(files_without_tests),
                "coverage_percent": round(coverage_percent, 1),
                "missing_tests": files_without_tests[:20],  # Limit to first 20
            }

        return results

    def print_results(self, success: bool, missing_tests: Dict[str, List[Path]]):
        """Print check results."""
        if success:
            print("✅ All new files have corresponding test files.")
            return

        print("❌ New files found without corresponding test files:\n")

        for language, files in missing_tests.items():
            print(f"📋 {language.upper()}:")
            for source_file in files:
                print(f"  📄 {source_file}")
                lang_config = self.languages.get(language, {})
                test_patterns = lang_config.get("test_patterns", [])
                if test_patterns:
                    suggested = test_patterns[0].format(
                        name=source_file.stem,
                        dir=str(source_file.parent.relative_to(self.root)),
                        ext=source_file.suffix[1:] if source_file.suffix else "ts",
                    )
                    print(f"     💡 Expected: {suggested}")
            print()

        print("⚠️  Please add test files before committing.")
        print("💡 Each language has specific test file conventions:")
        print("   - Python: tests/test_<name>.py")
        print("   - TypeScript: <dir>/__tests__/<name>.test.ts or <name>.test.ts")
        print("   - Rust: tests/<name>_test.rs or <name>_test.rs in same directory")
        print("   - Go: <name>_test.go in same directory")


def main():
    parser = argparse.ArgumentParser(description="Check test coverage across multiple programming languages")
    parser.add_argument("--check-new-files", action="store_true", help="Check that newly added files have test files")
    parser.add_argument(
        "--check-changed-files", action="store_true", help="Check that changed files have test files (warning only)"
    )
    parser.add_argument("--analyze-coverage", action="store_true", help="Analyze test coverage for existing code")
    parser.add_argument(
        "--language",
        choices=["python", "typescript", "rust", "go", "java", "all"],
        default="all",
        help="Language to check (default: all)",
    )
    parser.add_argument("--file", type=str, help="Check a specific file for test coverage")

    args = parser.parse_args()

    checker = MultiLangTestChecker()

    if args.file:
        # Check specific file
        file_path = Path(args.file)
        language = checker.detect_language(file_path)
        if not language:
            print(f"❌ Could not detect language for: {file_path}")
            sys.exit(1)

        test_file = checker.find_test_file(file_path, language)
        if test_file:
            print(f"✅ Test file found: {test_file.relative_to(checker.root)}")
            sys.exit(0)
        else:
            print(f"❌ No test file found for: {file_path}")
            sys.exit(1)

    elif args.analyze_coverage:
        # Analyze coverage
        language = None if args.language == "all" else args.language
        results = checker.analyze_coverage(language)

        print("\n📊 Test Coverage Analysis\n")
        print("=" * 60)

        for lang, stats in results.items():
            print(f"\n{lang.upper()}:")
            print(f"  Total files: {stats['total_files']}")
            print(f"  Files with tests: {stats['files_with_tests']}")
            print(f"  Files without tests: {stats['files_without_tests']}")
            print(f"  Coverage: {stats['coverage_percent']:.1f}%")

            if stats["missing_tests"]:
                print(f"\n  ⚠️  Files without tests (showing first 10):")
                for missing in stats["missing_tests"][:10]:
                    print(f"    - {missing}")

        print("\n" + "=" * 60)

    elif args.check_new_files:
        # Check new files
        success, missing_tests = checker.check_new_files()
        checker.print_results(success, missing_tests)
        sys.exit(0 if success else 1)

    elif args.check_changed_files:
        # Check changed files (warning only)
        changed_files = checker.get_changed_files()
        missing_tests = {}

        for changed_file in changed_files:
            language = checker.detect_language(changed_file)
            if not language:
                continue

            lang_config = checker.languages.get(language, {})
            source_dirs = lang_config.get("source_dirs", [])
            if not any(dir_path in str(changed_file) for dir_path in source_dirs):
                continue

            test_file = checker.find_test_file(changed_file, language)
            if not test_file:
                if language not in missing_tests:
                    missing_tests[language] = []
                missing_tests[language].append(changed_file)

        if missing_tests:
            print("⚠️  Changed files without corresponding test files:\n")
            checker.print_results(False, missing_tests)
        else:
            print("✅ All changed files have corresponding test files.")

    else:
        # Default: check new files
        success, missing_tests = checker.check_new_files()
        checker.print_results(success, missing_tests)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
