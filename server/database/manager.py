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

from .models import (
    Base,
    User,
    Memory,
    Organization,
    Team,
    TeamMember,
    Context,
    ContextPermission,
    OrganizationRegistration,
    UserInvitation,
)


class DatabaseManager:
    """Core database manager with connection and session management"""
    
    def __init__(self, config="postgresql://mem0user:mem0pass@localhost:5432/mem0db"):
        # Handle both string URL and config dict
        if isinstance(config, dict):
            database_url = config.get(
                "database_url", "postgresql://mem0user:mem0pass@localhost:5432/mem0db"
            )
        else:
            database_url = config

        # Ensure we always use PostgreSQL
        if not database_url.startswith("postgresql"):
            database_url = "postgresql://mem0user:mem0pass@localhost:5432/mem0db"
        print(f"🐘 Using PostgreSQL: {database_url}")

        # PostgreSQL connection with pool settings
        self.engine = create_engine(database_url, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        self.create_tables()

    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)

    def get_session(self):
        """Get a new database session"""
        return self.SessionLocal()

    def migrate_from_json(self, json_file="mem0_data.json"):
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
                    context = (
                        session.query(Context).filter_by(name=active_context).first()
                    )
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
