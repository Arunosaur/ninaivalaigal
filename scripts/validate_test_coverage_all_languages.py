#!/usr/bin/env python3
"""
Comprehensive Test Coverage Validation for All Languages

This script validates that all source code files across different languages
have corresponding test files. It uses flexible matching to account for
integration tests, functional tests, and module-level tests.

Usage:
    python scripts/validate_test_coverage_all_languages.py
    python scripts/validate_test_coverage_all_languages.py --language python
    python scripts/validate_test_coverage_all_languages.py --output report.txt
"""

import argparse
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class ComprehensiveTestValidator:
    """Comprehensive test coverage validator for all languages."""

    def __init__(self, root: Path = None):
        self.root = Path(root) if root else Path.cwd()
        self.results = defaultdict(
            lambda: {
                "total_files": 0,
                "files_with_tests": 0,
                "files_without_tests": [],
                "test_files_found": set(),
            }
        )

    def is_test_file(self, file_path: Path) -> bool:
        """Check if a file is a test file."""
        name = file_path.name.lower()
        path_str = str(file_path).lower()

        # Common test file patterns
        test_patterns = [
            "test_",
            "_test",
            ".test.",
            ".spec.",
            "__tests__",
            "test/",
            "tests/",
            "test.go",
            "_test.go",
            "test.rs",
            "_test.rs",
            "test.java",
            "test.ts",
            "test.tsx",
        ]

        return any(pattern in name or pattern in path_str for pattern in test_patterns)

    def is_generated_file(self, file_path: Path) -> bool:
        """Check if a file is generated or should be excluded."""
        name = file_path.name
        path_str = str(file_path)

        # Exclude patterns
        exclude_patterns = [
            "__pycache__",
            "node_modules",
            "target/",
            "dist/",
            ".pb.go",
            "_pb2.py",
            "_pb2_grpc.py",  # Generated protobuf
            "migrations/",
            "alembic/",
            "versions/",
            "conftest.py",
            "setup.py",
            "__init__.py",
            "main.go",
            "main.rs",
            "main.py",  # Entry points (optional to test)
            "build.rs",  # Build script
        ]

        return any(pattern in path_str for pattern in exclude_patterns)

    def find_python_test(self, source_file: Path) -> Optional[Path]:
        """Find test file for Python source file."""
        source_name = source_file.stem
        relative_path = source_file.relative_to(self.root)

        # Multiple strategies for finding tests

        # Strategy 1: Exact name match in tests/
        test_paths = [
            self.root / "tests" / f"test_{source_name}.py",
            self.root / "tests" / "unit" / f"test_{source_name}.py",
            self.root / "tests" / "integration" / f"test_{source_name}.py",
        ]

        # Strategy 2: Module-based test (e.g., server/memory/engine.py -> tests/test_memory_engine.py)
        if "/" in str(relative_path):
            parts = str(relative_path).split("/")
            # Try last component
            if len(parts) >= 2:
                module_name = parts[-2] if parts[-2] != "server" else parts[-1]
                test_paths.append(self.root / "tests" / f"test_{module_name}_{source_name}.py")

        # Strategy 3: Check in same directory or parent directory
        parent_dir = source_file.parent
        test_paths.extend(
            [
                parent_dir / f"test_{source_name}.py",
                parent_dir / "tests" / f"test_{source_name}.py",
            ]
        )

        # Strategy 4: Check services/*/tests/
        if "services/" in str(relative_path):
            service_match = re.search(r"services/([^/]+)/", str(relative_path))
            if service_match:
                service_name = service_match.group(1)
                test_paths.append(self.root / "services" / service_name / "tests" / f"test_{source_name}.py")

        # Check all possible paths
        for test_path in test_paths:
            if test_path.exists():
                return test_path

        # Strategy 5: Check if any test file imports this module
        # This is expensive but more accurate
        test_dirs = [
            self.root / "tests",
            self.root / "server" / "tests",
        ]

        for test_dir in test_dirs:
            if test_dir.exists():
                for test_file in test_dir.rglob("test_*.py"):
                    if self.is_test_file(test_file):
                        # Check if test file imports the source module
                        try:
                            content = test_file.read_text(encoding="utf-8", errors="ignore")
                            module_path = str(relative_path).replace("/", ".").replace(".py", "")
                            # Simple heuristic: check if module name appears in imports
                            if any(part in content for part in [source_name, module_path.split(".")[-1]]):
                                return test_file
                        except Exception:
                            continue

        return None

    def find_rust_test(self, source_file: Path) -> Optional[Path]:
        """Find test file for Rust source file."""
        source_name = source_file.stem
        relative_path = source_file.relative_to(self.root)

        # Strategy 1: Check tests/ directory at project root
        if "rust-services" in str(relative_path) or "services/memory-service-rust" in str(relative_path):
            # Find project root (graphops or memory-service)
            for parent in source_file.parents:
                if parent.name in ["graphops", "memory-service"]:
                    tests_dir = parent / "tests"
                    if tests_dir.exists():
                        # Check all test files
                        for test_file in tests_dir.glob("*.rs"):
                            if self.is_test_file(test_file):
                                return test_file
                        # Also check for integration_test.rs or similar
                        for pattern in ["*integration*.rs", "*test*.rs"]:
                            for test_file in tests_dir.glob(pattern):
                                if test_file.exists():
                                    return test_file

        # Strategy 2: Check for inline tests (files with #[cfg(test)])
        try:
            content = source_file.read_text(encoding="utf-8", errors="ignore")
            if "#[cfg(test)]" in content or "#[cfg(test)]" in content:
                # File has inline tests
                return source_file  # Return self to indicate tests exist
        except Exception:
            pass

        # Strategy 3: Check same directory
        test_file = source_file.parent / f"{source_name}_test.rs"
        if test_file.exists():
            return test_file

        return None

    def find_go_test(self, source_file: Path) -> Optional[Path]:
        """Find test file for Go source file."""
        source_name = source_file.stem

        # Go convention: test file in same directory
        test_file = source_file.parent / f"{source_name}_test.go"
        if test_file.exists():
            return test_file

        # Check for package-level test file
        test_file = source_file.parent / f"{source_file.parent.name}_test.go"
        if test_file.exists() and self.is_test_file(test_file):
            return test_file

        return None

    def find_typescript_test(self, source_file: Path) -> Optional[Path]:
        """Find test file for TypeScript/JavaScript source file."""
        source_name = source_file.stem
        directory = source_file.parent

        # Strategy 1: Check __tests__ directory
        test_dir = directory / "__tests__"
        if test_dir.exists():
            for ext in ["ts", "tsx", "js", "jsx"]:
                test_file = test_dir / f"{source_name}.test.{ext}"
                if test_file.exists():
                    return test_file

        # Strategy 2: Check same directory
        for ext in ["ts", "tsx", "js", "jsx"]:
            test_file = directory / f"{source_name}.test.{ext}"
            if test_file.exists():
                return test_file

        # Strategy 3: Check tests/ directory at project root
        for parent in source_file.parents:
            if parent.name in ["frontend-nextjs-customer", "frontend-nextjs", "frontend-shared", "apps"]:
                tests_dir = parent / "tests"
                if tests_dir.exists():
                    for test_file in tests_dir.rglob(f"*{source_name}*"):
                        if self.is_test_file(test_file):
                            return test_file
                break

        return None

    def find_java_test(self, source_file: Path) -> Optional[Path]:
        """Find test file for Java source file."""
        source_name = source_file.stem
        directory = source_file.parent

        # Java convention: Test class in test/ directory
        # Convert src/main/java/com/example/Class.java -> src/test/java/com/example/ClassTest.java
        if "src/main/java" in str(source_file):
            test_path = str(source_file).replace("src/main/java", "src/test/java")
            test_file = Path(test_path.replace(".java", "Test.java"))
            if test_file.exists():
                return test_file

        # Check same directory
        test_file = directory / f"{source_name}Test.java"
        if test_file.exists():
            return test_file

        return None

    def validate_language(self, language: str) -> Dict:
        """Validate test coverage for a specific language."""
        configs = {
            "python": {
                "extensions": [".py"],
                "source_dirs": ["server/", "services/", "shared/", "mcp_server/", "rbac/", "utils/", "python-clients/"],
                "finder": self.find_python_test,
            },
            "rust": {
                "extensions": [".rs"],
                "source_dirs": ["rust-services/", "services/memory-service-rust/"],
                "finder": self.find_rust_test,
            },
            "go": {
                "extensions": [".go"],
                "source_dirs": ["go-services/", "shared/"],
                "finder": self.find_go_test,
                "exclude_patterns": [".pb.go", "_pb.go"],
            },
            "typescript": {
                "extensions": [".ts", ".tsx"],
                "source_dirs": [
                    "frontend/",
                    "frontend-nextjs/",
                    "frontend-nextjs-customer/",
                    "frontend-shared/",
                    "apps/",
                    "packages/",
                ],
                "finder": self.find_typescript_test,
            },
            "java": {
                "extensions": [".java"],
                "source_dirs": ["jetbrains-plugin/"],
                "finder": self.find_java_test,
            },
        }

        config = configs.get(language)
        if not config:
            return {}

        # Find all source files
        source_files = []
        for source_dir in config["source_dirs"]:
            source_path = self.root / source_dir
            if source_path.exists():
                for ext in config["extensions"]:
                    source_files.extend(source_path.rglob(f"*{ext}"))

        # Filter out test files and generated files
        valid_source_files = []
        for source_file in source_files:
            if self.is_test_file(source_file):
                continue
            if self.is_generated_file(source_file):
                continue
            # Additional exclusions for Go
            if language == "go" and any(
                source_file.name.endswith(pattern) for pattern in config.get("exclude_patterns", [])
            ):
                continue

            valid_source_files.append(source_file)

        # Check each source file for tests
        files_with_tests = 0
        files_without_tests = []

        for source_file in valid_source_files:
            test_file = config["finder"](source_file)
            if test_file:
                files_with_tests += 1
                self.results[language]["test_files_found"].add(test_file)
            else:
                files_without_tests.append(source_file.relative_to(self.root))

        return {
            "total_files": len(valid_source_files),
            "files_with_tests": files_with_tests,
            "files_without_tests": files_without_tests,
            "coverage_percent": (files_with_tests / len(valid_source_files) * 100) if valid_source_files else 0,
        }

    def generate_report(self, languages: List[str] = None, output_file: Optional[Path] = None):
        """Generate comprehensive test coverage report."""
        languages = languages or ["python", "rust", "go", "typescript", "java"]

        print("\n" + "=" * 80)
        print("COMPREHENSIVE TEST COVERAGE VALIDATION REPORT")
        print("=" * 80 + "\n")

        all_results = {}
        for lang in languages:
            print(f"Analyzing {lang.upper()}...")
            results = self.validate_language(lang)
            all_results[lang] = results
            self.results[lang].update(results)

        # Print summary
        print("\n" + "=" * 80)
        print("SUMMARY BY LANGUAGE")
        print("=" * 80 + "\n")

        for lang in languages:
            stats = all_results.get(lang, {})
            total = stats.get("total_files", 0)
            with_tests = stats.get("files_with_tests", 0)
            without_tests = stats.get("files_without_tests", [])
            coverage = stats.get("coverage_percent", 0)

            print(f"\n{lang.upper()}:")
            print(f"  📁 Total source files: {total}")
            print(f"  ✅ Files with tests: {with_tests}")
            print(f"  ❌ Files without tests: {len(without_tests)}")
            print(f"  📊 Coverage: {coverage:.1f}%")

            if without_tests:
                print(f"\n  ⚠️  Files without tests (showing first 20):")
                for missing in without_tests[:20]:
                    print(f"    - {missing}")
                if len(without_tests) > 20:
                    print(f"    ... and {len(without_tests) - 20} more")

        # Overall statistics
        print("\n" + "=" * 80)
        print("OVERALL STATISTICS")
        print("=" * 80 + "\n")

        total_all = sum(r.get("total_files", 0) for r in all_results.values())
        with_tests_all = sum(r.get("files_with_tests", 0) for r in all_results.values())
        without_tests_all = sum(len(r.get("files_without_tests", [])) for r in all_results.values())

        print(f"Total source files across all languages: {total_all}")
        print(f"Files with tests: {with_tests_all}")
        print(f"Files without tests: {without_tests_all}")
        print(f"Overall coverage: {(with_tests_all / total_all * 100) if total_all > 0 else 0:.1f}%")

        print("\n" + "=" * 80 + "\n")

        # Write to file if requested
        if output_file:
            with open(output_file, "w") as f:
                f.write("COMPREHENSIVE TEST COVERAGE VALIDATION REPORT\n")
                f.write("=" * 80 + "\n\n")
                for lang in languages:
                    stats = all_results.get(lang, {})
                    f.write(f"\n{lang.upper()}:\n")
                    f.write(f"  Total files: {stats.get('total_files', 0)}\n")
                    f.write(f"  Files with tests: {stats.get('files_with_tests', 0)}\n")
                    f.write(f"  Files without tests: {len(stats.get('files_without_tests', []))}\n")
                    f.write(f"  Coverage: {stats.get('coverage_percent', 0):.1f}%\n\n")
                    f.write("  Files without tests:\n")
                    for missing in stats.get("files_without_tests", []):
                        f.write(f"    - {missing}\n")

            print(f"📄 Full report written to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Validate test coverage across all programming languages")
    parser.add_argument(
        "--language",
        choices=["python", "rust", "go", "typescript", "java", "all"],
        default="all",
        help="Language to validate (default: all)",
    )
    parser.add_argument("--output", type=str, help="Output file for detailed report")

    args = parser.parse_args()

    validator = ComprehensiveTestValidator()

    languages = ["python", "rust", "go", "typescript", "java"] if args.language == "all" else [args.language]
    output_file = Path(args.output) if args.output else None

    validator.generate_report(languages, output_file)


if __name__ == "__main__":
    main()
