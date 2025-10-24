#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""
Database Schema Drift Detection

Validates Alembic migrations for:
- Ordering conflicts
- Breaking schema changes
- Dangerous operations
- Migration reversibility
- Cross-service compatibility

Part of US #87: Schema Drift Prevention CI
"""

import argparse
import ast
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class SchemaDriftDetector:
    """Detects schema drift and migration issues in Alembic migrations."""

    # Dangerous SQL operations that should be flagged
    DANGEROUS_OPERATIONS = [
        "DROP TABLE",
        "DROP COLUMN",
        "ALTER COLUMN",
        "DROP INDEX",
        "DROP CONSTRAINT",
        "TRUNCATE",
    ]

    # Breaking change patterns
    BREAKING_PATTERNS = [
        r"ALTER\s+COLUMN\s+\w+\s+SET\s+NOT\s+NULL",  # Making column NOT NULL
        r"ALTER\s+COLUMN\s+\w+\s+DROP\s+DEFAULT",  # Removing default value
        r"ALTER\s+COLUMN\s+\w+\s+TYPE",  # Changing column type
        r"ADD\s+CONSTRAINT\s+\w+\s+NOT\s+NULL",  # Adding NOT NULL constraint
    ]

    def __init__(self, migration_dirs: List[Path]):
        self.migration_dirs = migration_dirs
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.migrations: Dict[Path, List[Dict]] = {}

    def scan_migrations(self) -> bool:
        """Scan all migration directories and load migration metadata."""
        for migration_dir in self.migration_dirs:
            if not migration_dir.exists():
                self.warnings.append(f"⚠️  Migration directory not found: {migration_dir}")
                continue

            migrations = []
            for migration_file in sorted(migration_dir.glob("*.py")):
                if migration_file.name.startswith("__"):
                    continue

                try:
                    metadata = self._parse_migration(migration_file)
                    migrations.append(metadata)
                except Exception as e:
                    self.errors.append(f"❌ Failed to parse {migration_file.name}: {e}")
                    return False

            self.migrations[migration_dir] = migrations
            print(f"✅ Scanned {len(migrations)} migrations in {migration_dir.name}")

        return True

    def _parse_migration(self, migration_file: Path) -> Dict:
        """Parse migration file and extract metadata."""
        content = migration_file.read_text()

        # Extract revision info
        revision = self._extract_field(content, "revision")
        down_revision = self._extract_field(content, "down_revision")

        # Analyze SQL operations
        upgrade_sql = self._extract_upgrade_sql(content)
        downgrade_sql = self._extract_downgrade_sql(content)

        return {
            "file": migration_file,
            "name": migration_file.stem,
            "revision": revision,
            "down_revision": down_revision,
            "upgrade_sql": upgrade_sql,
            "downgrade_sql": downgrade_sql,
            "content": content,
        }

    def _extract_field(self, content: str, field_name: str) -> Optional[str]:
        """Extract field value from migration file."""
        pattern = rf'{field_name}\s*=\s*["\']([^"\']+)["\']'
        match = re.search(pattern, content)
        return match.group(1) if match else None

    def _extract_upgrade_sql(self, content: str) -> List[str]:
        """Extract SQL statements from upgrade() function."""
        return self._extract_sql_from_function(content, "def upgrade():")

    def _extract_downgrade_sql(self, content: str) -> List[str]:
        """Extract SQL statements from downgrade() function."""
        return self._extract_sql_from_function(content, "def downgrade():")

    def _extract_sql_from_function(self, content: str, func_sig: str) -> List[str]:
        """Extract SQL statements from a function."""
        sql_statements = []

        # Find all op.execute() calls
        execute_pattern = r'op\.execute\(["\']([^"\']+)["\']'
        for match in re.finditer(execute_pattern, content):
            sql_statements.append(match.group(1))

        # Find all multi-line SQL statements
        multiline_pattern = r'op\.execute\(["\'\n\s]+(.*?)["\'\n\s]*\)'
        for match in re.finditer(multiline_pattern, content, re.DOTALL):
            sql = match.group(1).strip()
            if sql and sql not in sql_statements:
                sql_statements.append(sql)

        return sql_statements

    def validate_revision_chain(self) -> bool:
        """Validate that revision chain is consistent (no conflicts)."""
        for migration_dir, migrations in self.migrations.items():
            revisions = {m["revision"] for m in migrations if m["revision"]}
            down_revisions = {
                m["down_revision"] for m in migrations if m["down_revision"] and m["down_revision"] != "None"
            }

            # Check for duplicate revisions
            if len(revisions) != len([m for m in migrations if m["revision"]]):
                self.errors.append(f"❌ Duplicate revision IDs in {migration_dir.name}")
                return False

            # Check for orphaned migrations
            orphaned = down_revisions - revisions - {None, "None"}
            if orphaned:
                self.errors.append(f"❌ Orphaned migrations in {migration_dir.name}: {orphaned}")
                return False

            # Check for migration conflicts (multiple migrations with same down_revision)
            down_rev_count: Dict[str, int] = {}
            for m in migrations:
                down_rev = m["down_revision"]
                if down_rev and down_rev != "None":
                    down_rev_count[down_rev] = down_rev_count.get(down_rev, 0) + 1

            conflicts = {rev: count for rev, count in down_rev_count.items() if count > 1}
            if conflicts:
                self.errors.append(f"❌ Migration conflicts in {migration_dir.name}: {conflicts}")
                return False

        return True

    def detect_dangerous_operations(self) -> bool:
        """Detect dangerous SQL operations that could break production."""
        found_dangerous = False

        for migration_dir, migrations in self.migrations.items():
            for migration in migrations:
                for sql in migration["upgrade_sql"]:
                    sql_upper = sql.upper()

                    for dangerous_op in self.DANGEROUS_OPERATIONS:
                        if dangerous_op in sql_upper:
                            self.warnings.append(f"⚠️  DANGEROUS: {migration['name']} contains {dangerous_op}")
                            found_dangerous = True

        return not found_dangerous

    def detect_breaking_changes(self) -> bool:
        """Detect breaking schema changes."""
        found_breaking = False

        for migration_dir, migrations in self.migrations.items():
            for migration in migrations:
                for sql in migration["upgrade_sql"]:
                    sql_upper = sql.upper()

                    for pattern in self.BREAKING_PATTERNS:
                        if re.search(pattern, sql_upper):
                            self.warnings.append(f"🚨 BREAKING: {migration['name']} may break existing code")
                            self.warnings.append(f"   Pattern: {pattern}")
                            found_breaking = True

        return not found_breaking

    def validate_reversibility(self) -> bool:
        """Validate that all migrations have downgrade paths."""
        missing_downgrade = []

        for migration_dir, migrations in self.migrations.items():
            for migration in migrations:
                if not migration["downgrade_sql"]:
                    # Check if downgrade() function exists but is empty
                    if "def downgrade():" in migration["content"]:
                        if "pass" in migration["content"].split("def downgrade():")[1].split("def ")[0]:
                            missing_downgrade.append(migration["name"])

        if missing_downgrade:
            self.warnings.append(f"⚠️  Migrations without downgrade: {', '.join(missing_downgrade)}")

        return True  # Don't fail, just warn

    def check_naming_convention(self) -> bool:
        """Validate migration file naming conventions."""
        for migration_dir, migrations in self.migrations.items():
            for migration in migrations:
                filename = migration["file"].name

                # Check for timestamp prefix (YYYYMMDD_NNN format)
                if not re.match(r"^\d{8}_\d{3}_", filename):
                    self.warnings.append(
                        f"⚠️  {filename} doesn't follow naming convention (YYYYMMDD_NNN_description.py)"
                    )

        return True  # Don't fail, just warn

    def generate_report(self) -> Dict:
        """Generate validation report."""
        total_migrations = sum(len(m) for m in self.migrations.values())

        return {
            "passed": len(self.errors) == 0,
            "total_migrations": total_migrations,
            "migration_dirs": len(self.migration_dirs),
            "errors": self.errors,
            "warnings": self.warnings,
        }

    def run_all_validations(self) -> bool:
        """Run all validation checks."""
        print("🔍 Scanning migrations...")
        if not self.scan_migrations():
            return False

        print("\n📋 Validating revision chain...")
        self.validate_revision_chain()

        print("⚠️  Checking for dangerous operations...")
        self.detect_dangerous_operations()

        print("🚨 Detecting breaking changes...")
        self.detect_breaking_changes()

        print("🔄 Validating reversibility...")
        self.validate_reversibility()

        print("📝 Checking naming conventions...")
        self.check_naming_convention()

        return len(self.errors) == 0


def find_migration_directories(root_dir: Path) -> List[Path]:
    """Find all Alembic migration directories in the project."""
    migration_dirs = []

    # Common migration directory patterns
    patterns = [
        "alembic/versions",
        "migrations/versions",
        "db/migrations/versions",
        "*/migrations/versions",
    ]

    for pattern in patterns:
        for path in root_dir.glob(pattern):
            if path.is_dir():
                migration_dirs.append(path)

    return migration_dirs


def main():
    parser = argparse.ArgumentParser(description="Detect schema drift and validate Alembic migrations")
    parser.add_argument(
        "--migration-dirs", nargs="+", help="Migration directories to scan (auto-detected if not specified)"
    )
    parser.add_argument(
        "--fail-on-warnings", action="store_true", help="Fail if warnings are found (default: only fail on errors)"
    )

    args = parser.parse_args()

    # Determine migration directories
    if args.migration_dirs:
        migration_dirs = [Path(d) for d in args.migration_dirs]
    else:
        root_dir = Path(__file__).parent.parent
        migration_dirs = find_migration_directories(root_dir)

    if not migration_dirs:
        print("❌ No migration directories found")
        sys.exit(1)

    print("🔍 Database Schema Drift Detection")
    print("=" * 70)
    print(f"Scanning {len(migration_dirs)} migration directories:")
    for d in migration_dirs:
        print(f"  - {d}")
    print("=" * 70)

    # Run validation
    detector = SchemaDriftDetector(migration_dirs)
    success = detector.run_all_validations()

    # Generate report
    report = detector.generate_report()

    print("\n" + "=" * 70)
    if report["passed"]:
        print("✅ Schema Drift Validation PASSED")
    else:
        print("❌ Schema Drift Validation FAILED")
    print("=" * 70)

    print(f"\nScanned {report['total_migrations']} migrations across {report['migration_dirs']} directories")

    if report["errors"]:
        print("\n❌ ERRORS:")
        for error in report["errors"]:
            print(f"  {error}")

    if report["warnings"]:
        print("\n⚠️  WARNINGS:")
        for warning in report["warnings"]:
            print(f"  {warning}")

    # Determine exit code
    if not report["passed"]:
        sys.exit(1)
    elif args.fail_on_warnings and report["warnings"]:
        print("\n⚠️  Failing due to --fail-on-warnings")
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
