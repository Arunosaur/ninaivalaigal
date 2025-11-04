#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Database Manager for ninaivalaigal
Extracted from monolithic database.py for better organization

This addresses external code review feedback:
- Break down monolithic files (database.py 1285 lines → focused modules)
- Improve code organization and maintainability
"""

import json
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import DEFAULT_RUST_DATABASE_URL

from .models import Base, Context, Memory, User


class DatabaseManager:
    """Core database manager with connection and session management"""

    def __init__(self, config=None):
        """Initialize instance."""
        # Get database URL from environment or use default
        default_url = os.getenv(
            "DATABASE_URL",
            os.getenv("NINAIVALAIGAL_DATABASE_URL", DEFAULT_RUST_DATABASE_URL),
        )

        # Handle both string URL and config dict
        if isinstance(config, dict):
            database_url = config.get("database_url", default_url)
        elif config is not None:
            database_url = config
        else:
            database_url = default_url

        # Ensure we always use PostgreSQL
        if not database_url.startswith("postgresql"):
            database_url = DEFAULT_RUST_DATABASE_URL
        print(f"🐘 Using PostgreSQL: {database_url}")

        # PostgreSQL connection with pool settings
        self.engine = create_engine(database_url, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.create_tables()

    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)

    def get_session(self):
        """Get a new database session"""
        return self.SessionLocal()

    def migrate_from_json(self, json_file="ninaivalaigal_data.json"):
        """Migrate existing JSON data to database"""
        if not os.path.exists(json_file):
            return

        try:
            with open(json_file) as f:
                data = json.load(f)

            session = self.get_session()
            try:
                # Migrate memories
                for memory_entry in data.get("memories", []):
                    memory = Memory(
                        context=memory_entry["context"],
                        type=memory_entry["payload"]["type"],
                        source=memory_entry["payload"]["source"],
                        data=memory_entry["payload"]["data"],
                    )
                    session.add(memory)

                # Migrate active recording context
                active_context = data.get("recording_context")
                if active_context:
                    # Clear any existing active contexts
                    session.query(Context).update({"is_active": False})

                    # Set or create the active context
                    context = session.query(Context).filter_by(name=active_context).first()
                    if context:
                        context.is_active = True
                    else:
                        context = Context(name=active_context, is_active=True)
                        session.add(context)

                session.commit()
                print(f"Successfully migrated data from {json_file}")

                # Backup the original file
                backup_file = f"{json_file}.backup"
                os.rename(json_file, backup_file)
                print(f"Original file backed up to {backup_file}")

            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()

        except Exception as e:
            print(f"Error migrating from JSON: {e}")

    def _has_permission_level(self, user_level: str, required_level: str) -> bool:
        """Check if user permission level meets required level"""
        levels = {"read": 1, "write": 2, "admin": 3, "owner": 4}
        return levels.get(user_level, 0) >= levels.get(required_level, 999)

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        import bcrypt

        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        import bcrypt

        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

    # User management methods
    def get_user_by_email(self, email: str):
        """Get user by email"""
        session = self.get_session()
        try:
            return session.query(User).filter(User.email == email).first()
        finally:
            session.close()

    def get_user_by_id(self, user_id):
        """Get user by ID"""
        session = self.get_session()
        try:
            return session.query(User).filter(User.id == user_id).first()
        finally:
            session.close()

    def create_user(self, **kwargs):
        """Create a new user"""
        session = self.get_session()
        try:
            user = User(**kwargs)
            session.add(user)
            session.commit()
            session.refresh(user)  # Refresh to get generated ID
            return user
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def create_user_simple(self, email: str, name: str, password_hash: str, **kwargs):
        """Create a user using raw SQL to avoid ORM relationship loading issues"""
        import uuid
        from datetime import datetime

        from sqlalchemy import text

        session = self.get_session()
        try:
            user_id = str(uuid.uuid4())
            created_at = datetime.utcnow()

            # Use raw SQL to insert user
            insert_sql = text(
                """
                INSERT INTO users (
                    id, email, name, password_hash, account_type, subscription_tier,
                    role, created_via, email_verified, verification_token, created_at, updated_at, is_active
                )
                VALUES (
                    :id, :email, :name, :password_hash, :account_type, :subscription_tier,
                    :role, :created_via, :email_verified, :verification_token, :created_at, :updated_at, :is_active
                )
                RETURNING id, email, name, account_type, role, created_at
            """
            )

            result = session.execute(
                insert_sql,
                {
                    "id": user_id,
                    "email": email,
                    "name": name,
                    "password_hash": password_hash,
                    "account_type": kwargs.get("account_type", "individual"),
                    "subscription_tier": kwargs.get("subscription_tier", "free"),
                    "role": kwargs.get("role", "user"),
                    "created_via": kwargs.get("created_via", "signup"),
                    "email_verified": kwargs.get("email_verified", False),
                    "verification_token": kwargs.get("verification_token", None),
                    "created_at": created_at,
                    "updated_at": created_at,
                    "is_active": True,
                },
            )

            session.commit()
            user_data = result.fetchone()

            # Return a dict with user data
            return {
                "id": str(user_data[0]),
                "email": user_data[1],
                "name": user_data[2],
                "account_type": user_data[3],
                "role": user_data[4],
                "created_at": user_data[5].isoformat() if user_data[5] else None,
            }
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def authenticate_user(self, email: str, password_hash: str):
        """Authenticate user by email and password hash"""
        user = self.get_user_by_email(email)
        if user and user.password_hash == password_hash:
            return user
        return None
