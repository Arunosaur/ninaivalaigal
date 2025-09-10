# database.py - Database models and operations for mem0

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json
import os

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class Memory(Base):
    __tablename__ = "memories"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)  # NULL for backward compatibility
    context = Column(String(255), index=True, nullable=False)
    type = Column(String(100), nullable=False)
    source = Column(String(255), nullable=False)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class RecordingContext(Base):
    __tablename__ = "recording_contexts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)  # NULL for backward compatibility
    name = Column(String(255), nullable=False, index=True)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DatabaseManager:
    def __init__(self, database_url="postgresql://mem0:mem0@localhost:5432/mem0"):
        # Use different connection args for PostgreSQL vs SQLite
        if database_url.startswith("sqlite"):
            self.engine = create_engine(database_url, connect_args={"check_same_thread": False})
        else:
            self.engine = create_engine(database_url, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.create_tables()
        
    def create_tables(self):
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        return self.SessionLocal()
    
    def migrate_from_json(self, json_file="mem0_data.json"):
        """Migrate existing JSON data to database"""
        if not os.path.exists(json_file):
            return
            
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            session = self.get_session()
            try:
                # Migrate memories
                for memory_entry in data.get("memories", []):
                    memory = Memory(
                        context=memory_entry["context"],
                        type=memory_entry["payload"]["type"],
                        source=memory_entry["payload"]["source"],
                        data=memory_entry["payload"]["data"]
                    )
                    session.add(memory)
                
                # Migrate active recording context
                active_context = data.get("recording_context")
                if active_context:
                    # Clear any existing active contexts
                    session.query(RecordingContext).update({"is_active": False})
                    
                    # Set or create the active context
                    context = session.query(RecordingContext).filter_by(name=active_context).first()
                    if context:
                        context.is_active = True
                    else:
                        context = RecordingContext(name=active_context, is_active=True)
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
    
    
    def set_active_context(self, context_name: str, user_id: int = None):
        session = self.get_session()
        try:
            # Don't clear other active contexts - allow multiple active contexts per user
            # Just set this specific context to active
            if user_id:
                context = session.query(RecordingContext).filter_by(name=context_name, user_id=user_id).first()
            else:
                context = session.query(RecordingContext).filter_by(name=context_name, user_id=None).first()
            
            if context:
                context.is_active = True
            else:
                context = RecordingContext(name=context_name, is_active=True, user_id=user_id)
                session.add(context)
            
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def clear_active_context(self, user_id: int = None):
        session = self.get_session()
        try:
            if user_id:
                session.query(RecordingContext).filter_by(user_id=user_id).update({"is_active": False})
            else:
                session.query(RecordingContext).update({"is_active": False})
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_active_context(self, user_id: int = None):
        session = self.get_session()
        try:
            if user_id:
                contexts = session.query(RecordingContext).filter_by(is_active=True, user_id=user_id).all()
            else:
                contexts = session.query(RecordingContext).filter_by(is_active=True, user_id=None).all()
            
            # Return the most recently created active context
            if contexts:
                latest_context = max(contexts, key=lambda c: c.created_at)
                return latest_context.name
            return None
        finally:
            session.close()
    
    def get_all_contexts(self, user_id: int = None):
        session = self.get_session()
        try:
            if user_id:
                contexts = session.query(RecordingContext).filter_by(user_id=user_id).order_by(RecordingContext.created_at).all()
            else:
                contexts = session.query(RecordingContext).filter_by(user_id=None).order_by(RecordingContext.created_at).all()
            return [
                {
                    "name": context.name,
                    "is_active": context.is_active,
                    "created_at": context.created_at.isoformat()
                }
                for context in contexts
            ]
        finally:
            session.close()
    
    def add_memory(self, context: str, memory_type: str, source: str, data: dict, user_id: int = None):
        session = self.get_session()
        try:
            memory = Memory(
                context=context,
                type=memory_type,
                source=source,
                data=data,
                user_id=user_id
            )
            session.add(memory)
            session.commit()
            return memory.id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_memories(self, context: str, user_id: int = None):
        session = self.get_session()
        try:
            if user_id:
                memories = session.query(Memory).filter_by(context=context, user_id=user_id).order_by(Memory.created_at.desc()).all()
            else:
                memories = session.query(Memory).filter_by(context=context, user_id=None).order_by(Memory.created_at.desc()).all()
            
            return [
                {
                    "type": memory.type,
                    "source": memory.source,
                    "data": memory.data,
                    "created_at": memory.created_at.isoformat()
                }
                for memory in memories
            ]
        finally:
            session.close()

    def get_all_memories(self, user_id: int = None):
        session = self.get_session()
        try:
            if user_id:
                memories = session.query(Memory).filter_by(user_id=user_id).order_by(Memory.created_at.desc()).all()
            else:
                memories = session.query(Memory).filter_by(user_id=None).order_by(Memory.created_at.desc()).all()
            
            return [
                {
                    "type": memory.type,
                    "source": memory.source,
                    "data": memory.data,
                    "context": memory.context,
                    "created_at": memory.created_at.isoformat()
                }
                for memory in memories
            ]
        finally:
            session.close()

    def get_recent_memories(self, limit: int = 50, user_id: int = None):
        session = self.get_session()
        try:
            if user_id:
                memories = session.query(Memory).filter_by(user_id=user_id).order_by(Memory.created_at.desc()).limit(limit).all()
            else:
                memories = session.query(Memory).filter_by(user_id=None).order_by(Memory.created_at.desc()).limit(limit).all()
            
            return [
                {
                    "type": memory.type,
                    "source": memory.source,
                    "data": memory.data,
                    "context": memory.context,
                    "created_at": memory.created_at.isoformat()
                }
                for memory in memories
            ]
        finally:
            session.close()

    def get_contexts(self, user_id: int = None):
        session = self.get_session()
        try:
            if user_id:
                contexts = session.query(Memory.context).filter_by(user_id=user_id).distinct().all()
            else:
                contexts = session.query(Memory.context).filter_by(user_id=None).distinct().all()
            
            return [context[0] for context in contexts if context[0]]
        finally:
            session.close()

    def start_context(self, context_name: str):
        # For MCP compatibility - could store active context state
        pass

    def stop_context(self):
        # For MCP compatibility - could clear active context state
        pass
    
    def stop_specific_context(self, context_name: str, user_id: int = None):
        session = self.get_session()
        try:
            if user_id:
                session.query(RecordingContext).filter_by(name=context_name, user_id=user_id).update({"is_active": False})
            else:
                session.query(RecordingContext).filter_by(name=context_name, user_id=None).update({"is_active": False})
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def delete_context(self, context_name: str, user_id: int = None):
        session = self.get_session()
        try:
            # Delete all memories for this context
            if user_id:
                session.query(Memory).filter_by(context=context_name, user_id=user_id).delete()
                session.query(RecordingContext).filter_by(name=context_name, user_id=user_id).delete()
            else:
                session.query(Memory).filter_by(context=context_name, user_id=None).delete()
                session.query(RecordingContext).filter_by(name=context_name, user_id=None).delete()
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
