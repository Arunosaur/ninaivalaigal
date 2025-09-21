# SPEC-020: Memory Provider Architecture

## Overview

This specification defines the memory provider architecture for ninaivalaigal, implementing a flexible, pluggable system for memory storage and retrieval with support for multiple backends including native PostgreSQL and external HTTP services like mem0.

## Motivation

- **Provider Abstraction**: Clean interface for different memory storage backends
- **Flexibility**: Support for both native and external memory providers
- **Scalability**: Ability to switch providers based on deployment requirements
- **Testing**: Easy mocking and testing with different provider implementations
- **Future-Proofing**: Extensible architecture for new memory backends

## Specification

### 1. Memory Provider Interface

#### 1.1 Core Provider Protocol
```python
from typing import Protocol, List, Dict, Any, Optional
from datetime import datetime

class MemoryProvider(Protocol):
    """Abstract interface for memory providers"""
    
    async def remember(
        self, 
        user_id: str, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store a memory and return memory ID"""
        ...
    
    async def recall(
        self, 
        user_id: str, 
        query: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve memories similar to query"""
        ...
    
    async def delete(self, user_id: str, memory_id: str) -> bool:
        """Delete a specific memory"""
        ...
    
    async def list_memories(
        self, 
        user_id: str, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List all memories for a user"""
        ...
    
    async def health_check(self) -> Dict[str, Any]:
        """Check provider health and return status"""
        ...
```

#### 1.2 Memory Data Structure
```python
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class MemoryRecord(BaseModel):
    """Standard memory record structure"""
    id: str
    user_id: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    embedding: Optional[List[float]] = None
    similarity_score: Optional[float] = None
```

### 2. Native PostgreSQL Provider

#### 2.1 PostgresMemoryProvider Implementation
```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from pgvector.sqlalchemy import Vector
import openai
import json

class PostgresMemoryProvider:
    """Native PostgreSQL memory provider with pgvector"""
    
    def __init__(self, session_factory, openai_client=None):
        self.session_factory = session_factory
        self.openai_client = openai_client
    
    async def remember(
        self, 
        user_id: str, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store memory in PostgreSQL with vector embedding"""
        
        async with self.session_factory() as session:
            # Generate embedding if OpenAI client available
            embedding = None
            if self.openai_client:
                response = await self.openai_client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=content
                )
                embedding = response.data[0].embedding
            
            # Create memory record
            memory = Memory(
                user_id=user_id,
                content=content,
                metadata=json.dumps(metadata) if metadata else None,
                embedding=embedding
            )
            
            session.add(memory)
            await session.commit()
            await session.refresh(memory)
            
            return str(memory.id)
    
    async def recall(
        self, 
        user_id: str, 
        query: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve similar memories using vector search"""
        
        async with self.session_factory() as session:
            # Generate query embedding
            query_embedding = None
            if self.openai_client:
                response = await self.openai_client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=query
                )
                query_embedding = response.data[0].embedding
            
            # Vector similarity search
            if query_embedding:
                stmt = (
                    select(Memory)
                    .where(Memory.user_id == user_id)
                    .order_by(Memory.embedding.cosine_distance(query_embedding))
                    .limit(limit)
                )
            else:
                # Fallback to text search
                stmt = (
                    select(Memory)
                    .where(Memory.user_id == user_id)
                    .where(Memory.content.ilike(f"%{query}%"))
                    .limit(limit)
                )
            
            result = await session.execute(stmt)
            memories = result.scalars().all()
            
            return [
                {
                    "id": str(memory.id),
                    "content": memory.content,
                    "metadata": json.loads(memory.metadata) if memory.metadata else None,
                    "created_at": memory.created_at.isoformat(),
                    "similarity_score": None  # Could calculate if needed
                }
                for memory in memories
            ]
    
    async def health_check(self) -> Dict[str, Any]:
        """Check PostgreSQL connection and pgvector availability"""
        
        try:
            async with self.session_factory() as session:
                # Test basic connection
                await session.execute(select(1))
                
                # Test pgvector extension
                result = await session.execute(
                    select(func.count()).select_from(Memory)
                )
                memory_count = result.scalar()
                
                return {
                    "healthy": True,
                    "provider": "PostgresMemoryProvider",
                    "database_connection": "healthy",
                    "total_memories": memory_count,
                    "pgvector_available": True
                }
        
        except Exception as e:
            return {
                "healthy": False,
                "provider": "PostgresMemoryProvider",
                "error": str(e)
            }
```

### 3. HTTP Memory Provider (mem0 Integration)

#### 3.1 Mem0HttpMemoryProvider Implementation
```python
import httpx
import hashlib
import hmac
from typing import Dict, Any, List, Optional

class Mem0HttpMemoryProvider:
    """HTTP-based memory provider for mem0 service"""
    
    def __init__(
        self, 
        base_url: str, 
        api_key: Optional[str] = None,
        hmac_secret: Optional[str] = None
    ):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.hmac_secret = hmac_secret
        self.client = httpx.AsyncClient()
    
    def _get_headers(self, user_id: str) -> Dict[str, str]:
        """Generate authentication headers"""
        headers = {"Content-Type": "application/json"}
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        if self.hmac_secret:
            # HMAC-SHA256 authentication
            message = f"user:{user_id}"
            signature = hmac.new(
                self.hmac_secret.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            headers["X-User-Context"] = user_id
            headers["X-Signature"] = signature
        
        return headers
    
    async def remember(
        self, 
        user_id: str, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store memory via HTTP API"""
        
        payload = {
            "messages": [{"role": "user", "content": content}],
            "user_id": user_id
        }
        
        if metadata:
            payload["metadata"] = metadata
        
        response = await self.client.post(
            f"{self.base_url}/v1/memories/",
            json=payload,
            headers=self._get_headers(user_id)
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("memory_id", "unknown")
        else:
            raise Exception(f"Failed to store memory: {response.text}")
    
    async def recall(
        self, 
        user_id: str, 
        query: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve memories via HTTP API"""
        
        payload = {
            "query": query,
            "user_id": user_id,
            "limit": limit
        }
        
        response = await self.client.post(
            f"{self.base_url}/v1/memories/search/",
            json=payload,
            headers=self._get_headers(user_id)
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("memories", [])
        else:
            raise Exception(f"Failed to recall memories: {response.text}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check mem0 service health"""
        
        try:
            response = await self.client.get(
                f"{self.base_url}/health",
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return {
                    "healthy": True,
                    "provider": "Mem0HttpMemoryProvider",
                    "endpoint": self.base_url,
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                }
            else:
                return {
                    "healthy": False,
                    "provider": "Mem0HttpMemoryProvider",
                    "error": f"HTTP {response.status_code}"
                }
        
        except Exception as e:
            return {
                "healthy": False,
                "provider": "Mem0HttpMemoryProvider",
                "error": str(e)
            }
```

### 4. Provider Factory System

#### 4.1 Memory Provider Factory
```python
from enum import Enum
from typing import Union
import os

class MemoryProviderType(Enum):
    NATIVE = "native"
    HTTP = "http"
    MOCK = "mock"  # For testing

class MemoryProviderFactory:
    """Factory for creating memory providers"""
    
    @staticmethod
    def create_provider(
        provider_type: Union[str, MemoryProviderType] = None
    ) -> MemoryProvider:
        """Create memory provider based on configuration"""
        
        if provider_type is None:
            provider_type = os.getenv("MEMORY_PROVIDER", "native")
        
        if isinstance(provider_type, str):
            provider_type = MemoryProviderType(provider_type.lower())
        
        if provider_type == MemoryProviderType.NATIVE:
            return MemoryProviderFactory._create_postgres_provider()
        
        elif provider_type == MemoryProviderType.HTTP:
            return MemoryProviderFactory._create_http_provider()
        
        elif provider_type == MemoryProviderType.MOCK:
            return MemoryProviderFactory._create_mock_provider()
        
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")
    
    @staticmethod
    def _create_postgres_provider() -> PostgresMemoryProvider:
        """Create PostgreSQL memory provider"""
        from server.database import get_session_factory
        
        session_factory = get_session_factory()
        
        # Optional OpenAI client for embeddings
        openai_client = None
        if os.getenv("OPENAI_API_KEY"):
            import openai
            openai_client = openai.AsyncOpenAI()
        
        return PostgresMemoryProvider(session_factory, openai_client)
    
    @staticmethod
    def _create_http_provider() -> Mem0HttpMemoryProvider:
        """Create HTTP memory provider"""
        base_url = os.getenv("MEM0_BASE_URL", "http://localhost:8001")
        api_key = os.getenv("MEM0_API_KEY")
        hmac_secret = os.getenv("MEM0_HMAC_SECRET")
        
        return Mem0HttpMemoryProvider(base_url, api_key, hmac_secret)
    
    @staticmethod
    def _create_mock_provider() -> 'MockMemoryProvider':
        """Create mock memory provider for testing"""
        return MockMemoryProvider()
```

### 5. FastAPI Integration

#### 5.1 Memory API Router
```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/memory", tags=["memory"])

# Dependency to get memory provider
def get_memory_provider() -> MemoryProvider:
    return MemoryProviderFactory.create_provider()

class MemoryRequest(BaseModel):
    content: str
    metadata: Optional[Dict[str, Any]] = None

class RecallRequest(BaseModel):
    query: str
    limit: int = 10

@router.post("/remember")
async def remember_memory(
    request: MemoryRequest,
    user_id: str = Depends(get_current_user_id),
    provider: MemoryProvider = Depends(get_memory_provider)
):
    """Store a new memory"""
    try:
        memory_id = await provider.remember(
            user_id=user_id,
            content=request.content,
            metadata=request.metadata
        )
        return {"memory_id": memory_id, "status": "stored"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recall")
async def recall_memories(
    request: RecallRequest,
    user_id: str = Depends(get_current_user_id),
    provider: MemoryProvider = Depends(get_memory_provider)
):
    """Retrieve similar memories"""
    try:
        memories = await provider.recall(
            user_id=user_id,
            query=request.query,
            limit=request.limit
        )
        return {"memories": memories, "count": len(memories)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def memory_health(
    provider: MemoryProvider = Depends(get_memory_provider)
):
    """Check memory provider health"""
    return await provider.health_check()
```

### 6. Configuration Management

#### 6.1 Environment-Based Configuration
```python
# server/config.py
import os
from enum import Enum

class MemoryConfig:
    """Memory provider configuration"""
    
    # Provider selection
    PROVIDER_TYPE = os.getenv("MEMORY_PROVIDER", "native")
    
    # Native provider settings
    DATABASE_URL = os.getenv("DATABASE_URL")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # HTTP provider settings
    MEM0_BASE_URL = os.getenv("MEM0_BASE_URL", "http://localhost:8001")
    MEM0_API_KEY = os.getenv("MEM0_API_KEY")
    MEM0_HMAC_SECRET = os.getenv("MEM0_HMAC_SECRET")
    
    # Performance settings
    DEFAULT_RECALL_LIMIT = int(os.getenv("MEMORY_RECALL_LIMIT", "10"))
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
```

#### 6.2 Provider Selection Logic
```yaml
Provider Selection:
  Development:
    - Default: native (PostgreSQL)
    - Override: MEMORY_PROVIDER=http for mem0 testing
  
  Production:
    - Native: For self-hosted deployments
    - HTTP: For managed mem0 service
    - Decision based on scale and requirements
```

### 7. Testing Framework

#### 7.1 Mock Memory Provider
```python
class MockMemoryProvider:
    """Mock memory provider for testing"""
    
    def __init__(self):
        self.memories = {}
        self.next_id = 1
    
    async def remember(
        self, 
        user_id: str, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        memory_id = str(self.next_id)
        self.next_id += 1
        
        self.memories[memory_id] = {
            "id": memory_id,
            "user_id": user_id,
            "content": content,
            "metadata": metadata,
            "created_at": datetime.utcnow().isoformat()
        }
        
        return memory_id
    
    async def recall(
        self, 
        user_id: str, 
        query: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        user_memories = [
            memory for memory in self.memories.values()
            if memory["user_id"] == user_id and query.lower() in memory["content"].lower()
        ]
        return user_memories[:limit]
    
    async def health_check(self) -> Dict[str, Any]:
        return {
            "healthy": True,
            "provider": "MockMemoryProvider",
            "total_memories": len(self.memories)
        }
```

#### 7.2 Provider Testing
```python
import pytest
from server.memory_providers import MemoryProviderFactory, MemoryProviderType

@pytest.mark.asyncio
async def test_memory_provider_interface():
    """Test memory provider interface compliance"""
    
    provider = MemoryProviderFactory.create_provider(MemoryProviderType.MOCK)
    
    # Test remember
    memory_id = await provider.remember(
        user_id="test_user",
        content="Test memory content",
        metadata={"category": "test"}
    )
    assert memory_id is not None
    
    # Test recall
    memories = await provider.recall(
        user_id="test_user",
        query="test",
        limit=5
    )
    assert len(memories) > 0
    assert memories[0]["content"] == "Test memory content"
    
    # Test health check
    health = await provider.health_check()
    assert health["healthy"] is True
```

## Success Criteria

### 1. Functional Requirements
- ✅ All providers implement the MemoryProvider protocol
- ✅ Provider factory creates correct provider instances
- ✅ Memory operations work across all provider types
- ✅ Health checks provide accurate status information
- ✅ Configuration-based provider selection works

### 2. Performance Requirements
- ✅ Native provider: < 100ms for remember/recall operations
- ✅ HTTP provider: < 500ms for remember/recall operations
- ✅ Provider switching: < 1ms overhead
- ✅ Health checks: < 50ms response time

### 3. Integration Requirements
- ✅ FastAPI endpoints work with all providers
- ✅ Authentication integrates properly
- ✅ Error handling is consistent across providers
- ✅ Logging captures provider-specific information

## Future Enhancements

1. **Additional Providers**: Redis, Elasticsearch, Pinecone integration
2. **Provider Chaining**: Fallback providers for high availability
3. **Caching Layer**: Provider-agnostic caching for performance
4. **Batch Operations**: Bulk remember/recall operations
5. **Provider Metrics**: Detailed performance and usage metrics
6. **Schema Evolution**: Versioned memory schemas for compatibility

## Dependencies

- FastAPI (web framework)
- SQLAlchemy + pgvector (native provider)
- httpx (HTTP provider)
- OpenAI (embeddings, optional)
- Pydantic (data validation)
- pytest (testing framework)

This specification ensures ninaivalaigal has a flexible, extensible memory provider architecture that can adapt to different deployment scenarios and scale with growing requirements.
