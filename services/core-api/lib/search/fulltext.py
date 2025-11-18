#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
"""
Full-Text Search Module for PostgreSQL (SPEC-152, US-944)

This module provides full-text search functionality using PostgreSQL's
tsvector and tsquery capabilities with GIN indexes for fast search.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from database.models import SearchIndex
from lib.search.tag_search import AdvancedTagSearch
from sqlalchemy import desc, extract, func, or_, text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class FullTextSearch:
    """Full-text search implementation using PostgreSQL"""

    def __init__(self, db: Session):
        """
        Initialize full-text search

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def search(
        self,
        query: str,
        user_id: Optional[UUID] = None,
        scope_type: Optional[str] = None,
        scope_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        tag_expression: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Perform full-text search using PostgreSQL tsvector

        Args:
            query: Search query string
            user_id: Optional user ID for filtering
            scope_type: Optional scope type filter (user, team, org, public)
            scope_id: Optional scope ID filter
            tags: Optional list of tags to filter by
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of search results with memory_id, content_text, relevance_score, etc.
        """
        try:
            # Convert query to tsquery using plainto_tsquery for phrase matching
            # This handles multi-word queries better than to_tsquery
            tsquery = func.plainto_tsquery("english", query)

            # Build base query with combined ranking formula
            # Formula: final_score = relevance_score * 0.7 + recency_score * 0.3
            # recency_score = 1 / (1 + days_since_created)
            relevance_score = func.ts_rank(SearchIndex.search_vector, tsquery)

            # Calculate recency score: 1 / (1 + days_since_created)
            # days_since_created = EXTRACT(EPOCH FROM (NOW() - created_at)) / 86400.0
            days_since_created = extract("epoch", func.now() - SearchIndex.created_at) / 86400.0
            recency_score = 1.0 / (1.0 + days_since_created)

            # Combined final score: relevance * 0.7 + recency * 0.3
            final_score = (relevance_score * 0.7) + (recency_score * 0.3)

            base_query = self.db.query(
                SearchIndex.memory_id,
                SearchIndex.content_text,
                SearchIndex.tags,
                SearchIndex.scope_type,
                SearchIndex.scope_id,
                SearchIndex.created_at,
                # Calculate relevance score using ts_rank
                relevance_score.label("relevance_score"),
                # Calculate recency score
                recency_score.label("recency_score"),
                # Calculate final combined score
                final_score.label("final_score"),
            ).filter(
                # Full-text search match using @@ operator
                SearchIndex.search_vector.op("@@")(tsquery)
            )

            # Apply scope filters
            if scope_type:
                base_query = base_query.filter(SearchIndex.scope_type == scope_type)
            if scope_id:
                base_query = base_query.filter(SearchIndex.scope_id == scope_id)

            # Apply user filter (if user_id provided, only show user's own memories or public)
            if user_id:
                base_query = base_query.filter(or_(SearchIndex.scope_id == user_id, SearchIndex.scope_type == "public"))

            # Apply tag filters (simple list - all must match)
            if tags:
                for tag in tags:
                    base_query = base_query.filter(SearchIndex.tags.contains([tag]))

            # Apply advanced tag expression (boolean operators)
            if tag_expression:
                tag_search = AdvancedTagSearch(self.db)
                base_query = tag_search.search_with_tag_expression(
                    base_query,
                    tag_expression,
                    scope_type=scope_type,
                    scope_id=scope_id,
                )

            # Apply date range filters
            if date_from:
                base_query = base_query.filter(SearchIndex.created_at >= date_from)
            if date_to:
                base_query = base_query.filter(SearchIndex.created_at <= date_to)

            # Order by final combined score (descending) and created_at (descending)
            base_query = base_query.order_by(desc("final_score"), desc(SearchIndex.created_at))

            # Apply pagination
            base_query = base_query.limit(limit).offset(offset)

            # Execute query
            results = base_query.all()

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append(
                    {
                        "memory_id": str(result.memory_id),
                        "content_text": result.content_text,
                        "tags": result.tags or [],
                        "scope_type": result.scope_type,
                        "scope_id": str(result.scope_id) if result.scope_id else None,
                        "created_at": result.created_at.isoformat() if result.created_at else None,
                        "relevance_score": float(result.relevance_score) if result.relevance_score else 0.0,
                        "recency_score": (
                            float(result.recency_score)
                            if hasattr(result, "recency_score") and result.recency_score
                            else 0.0
                        ),
                        "final_score": (
                            float(result.final_score) if hasattr(result, "final_score") and result.final_score else 0.0
                        ),
                    }
                )

            logger.info(f"Full-text search for '{query}' returned {len(formatted_results)} results")
            return formatted_results

        except Exception as e:
            logger.error(f"Full-text search failed for query '{query}': {e}", exc_info=True)
            return []

    def search_with_highlighting(
        self,
        query: str,
        user_id: Optional[UUID] = None,
        scope_type: Optional[str] = None,
        scope_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        tag_expression: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Perform full-text search with HTML highlighting of matched terms

        Args:
            query: Search query string
            user_id: Optional user ID for filtering
            scope_type: Optional scope type filter
            scope_id: Optional scope ID filter
            tags: Optional list of tags to filter by
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of search results with highlighted content
        """
        try:
            # Get base search results
            results = self.search(
                query=query,
                user_id=user_id,
                scope_type=scope_type,
                scope_id=scope_id,
                tags=tags,
                tag_expression=tag_expression,
                date_from=date_from,
                date_to=date_to,
                limit=limit,
                offset=offset,
            )

            # Add highlighting using ts_headline
            tsquery = func.plainto_tsquery("english", query)

            for result in results:
                memory_id = UUID(result["memory_id"])

                # Get highlighted content using ts_headline
                highlighted = (
                    self.db.query(
                        func.ts_headline(
                            "english",
                            SearchIndex.content_text,
                            tsquery,
                            text("'StartSel=<mark>, StopSel=</mark>, MaxWords=35, MinWords=15'"),
                        ).label("highlighted")
                    )
                    .filter(SearchIndex.memory_id == memory_id)
                    .first()
                )

                if highlighted and highlighted.highlighted:
                    result["highlighted_content"] = highlighted.highlighted
                else:
                    # Fallback: truncate content if highlighting fails
                    content = result["content_text"]
                    if len(content) > 200:
                        content = content[:200] + "..."
                    result["highlighted_content"] = content

            return results

        except Exception as e:
            logger.error(f"Full-text search with highlighting failed for query '{query}': {e}", exc_info=True)
            return []

    def get_result_count(
        self,
        query: str,
        user_id: Optional[UUID] = None,
        scope_type: Optional[str] = None,
        scope_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        tag_expression: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> int:
        """
        Get total count of search results without fetching all results

        Args:
            query: Search query string
            user_id: Optional user ID for filtering
            scope_type: Optional scope type filter
            scope_id: Optional scope ID filter
            tags: Optional list of tags to filter by

        Returns:
            Total number of matching results
        """
        try:
            tsquery = func.plainto_tsquery("english", query)

            base_query = self.db.query(func.count(SearchIndex.id)).filter(SearchIndex.search_vector.op("@@")(tsquery))

            # Apply same filters as search()
            if scope_type:
                base_query = base_query.filter(SearchIndex.scope_type == scope_type)
            if scope_id:
                base_query = base_query.filter(SearchIndex.scope_id == scope_id)
            if user_id:
                base_query = base_query.filter(or_(SearchIndex.scope_id == user_id, SearchIndex.scope_type == "public"))
            if tags:
                for tag in tags:
                    base_query = base_query.filter(SearchIndex.tags.contains([tag]))

            # Apply advanced tag expression (boolean operators)
            if tag_expression:
                tag_search = AdvancedTagSearch(self.db)
                base_query = tag_search.search_with_tag_expression(
                    base_query,
                    tag_expression,
                    scope_type=scope_type,
                    scope_id=scope_id,
                )

            # Apply date range filters
            if date_from:
                base_query = base_query.filter(SearchIndex.created_at >= date_from)
            if date_to:
                base_query = base_query.filter(SearchIndex.created_at <= date_to)

            count = base_query.scalar()
            return count or 0

        except Exception as e:
            logger.error(f"Failed to get search result count for query '{query}': {e}", exc_info=True)
            return 0
