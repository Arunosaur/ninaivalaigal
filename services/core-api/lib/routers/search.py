#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
"""
Search API Router for PostgreSQL Full-Text Search (SPEC-152, US-944, US-946)

This router provides endpoints for full-text search across memory content
using PostgreSQL's tsvector and tsquery capabilities, with faceted filtering.
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..auth_utils import get_current_user
from ..config import get_dynamic_database_url
from ..database.manager import DatabaseManager
from ..search.autocomplete import SearchAutocomplete
from ..search.facets import FacetedSearch
from ..search.fulltext import FullTextSearch
from ..search.indexer import SearchIndexer
from ..search.suggestions import SearchSuggestions
from ..search.tag_search import AdvancedTagSearch

# Try to import SearchAnalytics if it exists
try:
    from ..search.analytics import SearchAnalytics

    HAS_ANALYTICS = True
except ImportError:
    HAS_ANALYTICS = False
    SearchAnalytics = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


# Pydantic models
class SearchRequest(BaseModel):
    """Search request model"""

    query: str = Field(..., min_length=1, max_length=500, description="Search query string")
    scope_type: Optional[str] = Field(None, description="Scope type filter (user, team, org, public)")
    scope_id: Optional[str] = Field(None, description="Scope ID filter")
    tags: Optional[List[str]] = Field(None, description="Tags to filter by (simple list, all must match)")
    tag_expression: Optional[str] = Field(
        None, description="Boolean tag expression (e.g., 'tag1 AND tag2 OR tag3', 'work/projects AND NOT urgent')"
    )
    date_from: Optional[str] = Field(None, description="Start date filter (ISO format)")
    date_to: Optional[str] = Field(None, description="End date filter (ISO format)")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Offset for pagination")
    highlight: bool = Field(True, description="Include HTML highlighting in results")
    include_facets: bool = Field(False, description="Include facet counts in response")


class SearchResult(BaseModel):
    """Search result model"""

    memory_id: str
    content_text: str
    highlighted_content: Optional[str] = None
    tags: List[str]
    scope_type: Optional[str] = None
    scope_id: Optional[str] = None
    created_at: Optional[str] = None
    relevance_score: float
    recency_score: Optional[float] = Field(None, description="Recency score (0-1)")
    final_score: Optional[float] = Field(None, description="Combined ranking score (relevance * 0.7 + recency * 0.3)")


class FacetCounts(BaseModel):
    """Facet counts model"""

    tags: List[Dict[str, Any]] = Field(default_factory=list, description="Tag facet counts")
    scopes: List[Dict[str, Any]] = Field(default_factory=list, description="Scope facet counts")
    date_ranges: List[Dict[str, Any]] = Field(default_factory=list, description="Date range facet counts")


class SearchResponse(BaseModel):
    """Search response model"""

    query: str
    results: List[SearchResult]
    total_count: int
    limit: int
    offset: int
    facets: Optional[FacetCounts] = Field(None, description="Facet counts (if requested)")


def get_db():
    """Get database manager with dynamic configuration"""
    return DatabaseManager(get_dynamic_database_url())


def get_db_session(db: DatabaseManager = Depends(get_db)):
    """Get database session"""
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()


def get_search_service(session=Depends(get_db_session)):
    """Get full-text search service"""
    return FullTextSearch(session)


def get_tag_search_service(session=Depends(get_db_session)):
    """Get advanced tag search service"""
    return AdvancedTagSearch(session)


def get_indexer_service(session=Depends(get_db_session)):
    """Get search indexer service"""
    return SearchIndexer(session)


def get_facets_service(session=Depends(get_db_session)):
    """Get faceted search service"""
    return FacetedSearch(session)


def get_autocomplete_service(session=Depends(get_db_session)):
    """Get autocomplete service"""
    return SearchAutocomplete(session)


def get_suggestions_service(session=Depends(get_db_session)):
    """Get search suggestions service"""
    return SearchSuggestions(session)


def get_analytics_service(session=Depends(get_db_session)):
    """Get search analytics service"""
    if HAS_ANALYTICS:
        return SearchAnalytics(session)
    return None


@router.post("/", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    current_user: dict = Depends(get_current_user),
    search_service: FullTextSearch = Depends(get_search_service),
    facets_service: FacetedSearch = Depends(get_facets_service),
    analytics=Depends(get_analytics_service),
):
    """
    Perform full-text search across memory content

    Uses PostgreSQL full-text search with tsvector and tsquery for fast,
    relevance-ranked search results. Tracks search queries for analytics.
    """
    start_time = time.time()
    search_query_id = None

    try:
        user_id = UUID(current_user.get("user_id")) if current_user.get("user_id") else None

        # Convert scope_id to UUID if provided
        scope_id = UUID(request.scope_id) if request.scope_id else None

        # Parse date filters
        date_from = None
        date_to = None
        if request.date_from:
            try:
                date_from = datetime.fromisoformat(request.date_from.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_from format. Use ISO format.")
        if request.date_to:
            try:
                date_to = datetime.fromisoformat(request.date_to.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_to format. Use ISO format.")

        # Perform search
        # Use tag_expression if provided, otherwise use tags list
        tag_expression = request.tag_expression if request.tag_expression else None
        tags = request.tags if not tag_expression else None  # Don't use both

        if request.highlight:
            results = search_service.search_with_highlighting(
                query=request.query,
                user_id=user_id,
                scope_type=request.scope_type,
                scope_id=scope_id,
                tags=tags,
                tag_expression=tag_expression,
                date_from=date_from,
                date_to=date_to,
                limit=request.limit,
                offset=request.offset,
            )
        else:
            results = search_service.search(
                query=request.query,
                user_id=user_id,
                scope_type=request.scope_type,
                scope_id=scope_id,
                tags=tags,
                tag_expression=tag_expression,
                date_from=date_from,
                date_to=date_to,
                limit=request.limit,
                offset=request.offset,
            )

        # Get total count
        total_count = search_service.get_result_count(
            query=request.query,
            user_id=user_id,
            scope_type=request.scope_type,
            scope_id=scope_id,
            tags=tags,
            tag_expression=tag_expression,
            date_from=date_from,
            date_to=date_to,
        )

        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)

        # Track search query for analytics (if available)
        search_query_id = None
        if analytics:
            try:
                search_query_id = analytics.track_query(
                    query=request.query,
                    user_id=user_id,
                    result_count=total_count,
                    latency_ms=latency_ms,
                )
            except Exception as e:
                logger.warning(f"Analytics tracking failed: {e}")

        # Get facet counts if requested
        facet_counts = None
        if request.include_facets:
            try:
                base_filters = {}
                if request.scope_type:
                    base_filters["scope_type"] = request.scope_type
                if scope_id:
                    base_filters["scope_id"] = scope_id
                if request.tags:
                    base_filters["tags"] = request.tags
                if date_from:
                    base_filters["date_from"] = date_from
                if date_to:
                    base_filters["date_to"] = date_to

                facets = facets_service.get_facet_counts(
                    query=request.query,
                    user_id=user_id,
                    base_filters=base_filters,
                )
                facet_counts = FacetCounts(**facets)
            except Exception as e:
                logger.warning(f"Failed to get facet counts: {e}")

        # Format results
        search_results = [
            SearchResult(
                memory_id=r["memory_id"],
                content_text=r["content_text"],
                highlighted_content=r.get("highlighted_content"),
                tags=r.get("tags", []),
                scope_type=r.get("scope_type"),
                scope_id=r.get("scope_id"),
                created_at=r.get("created_at"),
                relevance_score=r.get("relevance_score", 0.0),
                recency_score=r.get("recency_score"),
                final_score=r.get("final_score"),
            )
            for r in results
        ]

        response = SearchResponse(
            query=request.query,
            results=search_results,
            total_count=total_count,
            limit=request.limit,
            offset=request.offset,
            facets=facet_counts,
        )

        # Add search_query_id to response metadata (if needed for click tracking)
        # This can be used by the frontend to track clicks
        if search_query_id:
            # Store in response model if we extend it, or return in headers
            pass

        return response

    except Exception as e:
        # Track failed query if we have partial data
        latency_ms = int((time.time() - start_time) * 1000)
        if analytics:
            try:
                user_id = UUID(current_user.get("user_id")) if current_user.get("user_id") else None
                analytics.track_query(
                    query=request.query,
                    user_id=user_id,
                    result_count=0,
                    latency_ms=latency_ms,
                )
            except Exception:
                pass  # Don't fail on analytics tracking

        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/", response_model=SearchResponse)
async def search_get(
    q: str = Query(..., min_length=1, max_length=500, description="Search query string"),
    scope_type: Optional[str] = Query(None, description="Scope type filter"),
    scope_id: Optional[str] = Query(None, description="Scope ID filter"),
    tags: Optional[List[str]] = Query(None, description="Tags to filter by (simple list)"),
    tag_expression: Optional[str] = Query(None, description="Boolean tag expression (e.g., 'tag1 AND tag2 OR tag3')"),
    date_from: Optional[str] = Query(None, description="Start date filter (ISO format)"),
    date_to: Optional[str] = Query(None, description="End date filter (ISO format)"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    highlight: bool = Query(True, description="Include HTML highlighting"),
    include_facets: bool = Query(False, description="Include facet counts"),
    current_user: dict = Depends(get_current_user),
    search_service: FullTextSearch = Depends(get_search_service),
    facets_service: FacetedSearch = Depends(get_facets_service),
    tag_search_service: AdvancedTagSearch = Depends(get_tag_search_service),
    analytics=Depends(get_analytics_service),
):
    """
    Perform full-text search (GET endpoint for convenience)
    """
    request = SearchRequest(
        query=q,
        scope_type=scope_type,
        scope_id=scope_id,
        tags=tags,
        tag_expression=tag_expression,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
        highlight=highlight,
        include_facets=include_facets,
    )
    return await search(request, current_user, search_service, facets_service, tag_search_service, analytics)


@router.post("/reindex/{memory_id}")
async def reindex_memory(
    memory_id: str,
    current_user: dict = Depends(get_current_user),
    indexer: SearchIndexer = Depends(get_indexer_service),
):
    """
    Reindex a specific memory

    Useful for updating search index after memory content changes.
    """
    try:
        memory_uuid = UUID(memory_id)
        success = indexer.reindex_memory(memory_uuid)

        if success:
            return {"success": True, "message": f"Memory {memory_id} reindexed successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Memory {memory_id} not found or reindexing failed")

    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid memory ID: {memory_id}")
    except Exception as e:
        logger.error(f"Reindex failed for memory {memory_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Reindex failed: {str(e)}")


@router.post("/reindex/batch")
async def batch_reindex(
    limit: int = Query(1000, ge=1, le=10000, description="Maximum number of memories to index"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: dict = Depends(get_current_user),
    indexer: SearchIndexer = Depends(get_indexer_service),
):
    """
    Batch reindex memories

    Useful for initial indexing or rebuilding the search index.
    """
    try:
        # TODO: Add admin-only check
        indexed_count = indexer.batch_reindex(limit=limit, offset=offset)

        return {
            "success": True,
            "indexed_count": indexed_count,
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        logger.error(f"Batch reindex failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch reindex failed: {str(e)}")


@router.get("/facets")
async def get_facets(
    q: Optional[str] = Query(None, min_length=1, max_length=500, description="Optional search query to filter facets"),
    scope_type: Optional[str] = Query(None, description="Scope type filter"),
    scope_id: Optional[str] = Query(None, description="Scope ID filter"),
    tags: Optional[List[str]] = Query(None, description="Tags to filter by"),
    date_from: Optional[str] = Query(None, description="Start date filter (ISO format)"),
    date_to: Optional[str] = Query(None, description="End date filter (ISO format)"),
    current_user: dict = Depends(get_current_user),
    facets_service: FacetedSearch = Depends(get_facets_service),
):
    """
    Get facet counts for tags, scopes, and date ranges

    Returns facet counts that can be used for filtering search results.
    Optionally filters facets by a search query and other filters.
    """
    try:
        user_id = UUID(current_user.get("user_id")) if current_user.get("user_id") else None

        # Convert scope_id to UUID if provided
        scope_id = UUID(scope_id) if scope_id else None

        # Parse date filters
        date_from_dt = None
        date_to_dt = None
        if date_from:
            try:
                date_from_dt = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_from format. Use ISO format.")
        if date_to:
            try:
                date_to_dt = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_to format. Use ISO format.")

        # Build base filters
        base_filters = {}
        if scope_type:
            base_filters["scope_type"] = scope_type
        if scope_id:
            base_filters["scope_id"] = scope_id
        if tags:
            base_filters["tags"] = tags
        if date_from_dt:
            base_filters["date_from"] = date_from_dt
        if date_to_dt:
            base_filters["date_to"] = date_to_dt

        # Get facet counts
        facets = facets_service.get_facet_counts(
            query=q,
            user_id=user_id,
            base_filters=base_filters if base_filters else None,
        )

        return FacetCounts(**facets)

    except Exception as e:
        logger.error(f"Failed to get facets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get facets: {str(e)}")


@router.get("/autocomplete")
async def autocomplete(
    q: str = Query(..., min_length=1, max_length=500, description="Query prefix for autocomplete"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of suggestions"),
    current_user: dict = Depends(get_current_user),
    autocomplete_service: SearchAutocomplete = Depends(get_autocomplete_service),
):
    """
    Get autocomplete suggestions for a search query

    Returns query completions based on prefix matching against indexed content
    and search history.
    """
    try:
        user_id = UUID(current_user.get("user_id")) if current_user.get("user_id") else None

        suggestions = autocomplete_service.autocomplete(
            query=q,
            user_id=user_id,
            limit=limit,
        )

        return {
            "query": q,
            "suggestions": suggestions,
            "count": len(suggestions),
        }

    except Exception as e:
        logger.error(f"Autocomplete failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Autocomplete failed: {str(e)}")


@router.get("/suggestions")
async def get_suggestions(
    q: Optional[str] = Query(None, min_length=1, max_length=500, description="Optional query to base suggestions on"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of suggestions"),
    current_user: dict = Depends(get_current_user),
    suggestions_service: SearchSuggestions = Depends(get_suggestions_service),
):
    """
    Get search suggestions

    Returns suggestions based on:
    - Popular queries
    - User's search history
    - Query-based completions
    """
    try:
        user_id = UUID(current_user.get("user_id")) if current_user.get("user_id") else None

        suggestions = suggestions_service.get_suggestions(
            query=q,
            user_id=user_id,
            limit=limit,
        )

        return {
            "query": q,
            "suggestions": suggestions,
            "count": len(suggestions),
        }

    except Exception as e:
        logger.error(f"Failed to get suggestions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")
