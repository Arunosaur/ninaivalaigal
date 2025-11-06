#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
SQLAlchemy Mapper Debug Script
Systematically debug the Team.invitations mapper issue without commenting out code
"""

import traceback

from sqlalchemy.orm import configure_mappers


def debug_step(step_name, func):
    """Execute a debug step and report results"""
    print(f"\n🔍 {step_name}")
    print("=" * 50)
    try:
        result = func()
        print(f"✅ SUCCESS: {result}")
        return True, result
    except Exception as e:
        print(f"❌ FAILED: {e}")
        print(f"📍 Traceback: {traceback.format_exc()}")
        return False, str(e)


def step1_basic_imports():
    """Test basic model imports"""

    return "Imported User, Team, Organization successfully"


def step2_check_team_attributes():
    """Check what attributes Team actually has"""
    from database.models import Team

    attrs = [attr for attr in dir(Team) if not attr.startswith("_")]
    return f"Team attributes: {attrs}"


def step3_check_team_relationships():
    """Check Team's SQLAlchemy relationships"""
    from database.models import Team
    from sqlalchemy import inspect

    mapper = inspect(Team)
    relationships = [rel.key for rel in mapper.relationships]
    return f"Team relationships: {relationships}"


def step4_import_team_invitation():
    """Test TeamInvitation import"""
    from database import UserInvitation

    return f"TeamInvitation imported: {UserInvitation}"


def step5_check_team_invitation_relationships():
    """Check TeamInvitation's relationships"""
    from database import UserInvitation
    from sqlalchemy import inspect

    mapper = inspect(UserInvitation)
    relationships = [rel.key for rel in mapper.relationships]
    return f"TeamInvitation relationships: {relationships}"


def step6_check_registry_state():
    """Check SQLAlchemy registry state"""
    from database.models import Base

    mappers = list(Base.registry._class_registry.keys())
    return f"Registered classes: {mappers}"


def step7_configure_mappers():
    """Try to configure mappers and see exact error"""
    configure_mappers()
    return "Mappers configured successfully"


def step8_check_back_populates():
    """Check if any relationships have back_populates='invitations'"""
    from database import UserInvitation
    from sqlalchemy import inspect

    mapper = inspect(UserInvitation)
    for rel in mapper.relationships:
        if hasattr(rel, "back_populates"):
            print(f"  {rel.key} -> back_populates: {rel.back_populates}")

    return "Checked back_populates relationships"


def main():
    """Run systematic debugging"""
    print("🚀 SQLAlchemy Mapper Debug Session")
    print("=" * 60)

    steps = [
        ("Basic Model Imports", step1_basic_imports),
        ("Check Team Attributes", step2_check_team_attributes),
        ("Check Team Relationships", step3_check_team_relationships),
        ("Import TeamInvitation", step4_import_team_invitation),
        (
            "Check TeamInvitation Relationships",
            step5_check_team_invitation_relationships,
        ),
        ("Check Registry State", step6_check_registry_state),
        ("Check Back-Populates", step8_check_back_populates),
        ("Configure Mappers", step7_configure_mappers),
    ]

    results = {}

    for step_name, step_func in steps:
        success, result = debug_step(step_name, step_func)
        results[step_name] = (success, result)

        if not success and "invitations" in result:
            print(f"\n🎯 FOUND THE ISSUE IN: {step_name}")
            print(f"🔍 Error details: {result}")
            break

    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)

    for step_name, (success, result) in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {step_name}: {result[:100]}...")

    print("\n🎯 NEXT STEPS:")
    print("1. Look at the first failed step")
    print("2. Fix the specific issue without commenting out code")
    print("3. Re-run this debug script to verify fix")


if __name__ == "__main__":
    main()
