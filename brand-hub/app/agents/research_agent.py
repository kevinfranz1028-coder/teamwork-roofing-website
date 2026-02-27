"""
Brand Intelligence Content Hub - Research Agent

Queries all available knowledge sources (ChromaDB collections, SQLite
tables, brand_config.json) and assembles a :class:`ContentBrief` that
informs every generation with existing brand content, voice guidance,
approved examples, and terminology.

Usage:
    from app.agents.research_agent import ResearchAgent

    agent = ResearchAgent()
    brief = agent.build_brief("Create a customer service training deck")
    context = brief.to_prompt_context()  # inject into Claude system prompt
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from app.agents.task_plan import ContentBrief
from app.config import BRAND_ASSETS_DIR, CHROMADB_DIR

logger = logging.getLogger(__name__)


class ResearchAgent:
    """Pre-generation research agent that queries all knowledge sources.

    Initialises lazily — the vector store and database session are only
    created when :meth:`build_brief` is first called.  This keeps the
    import lightweight for modules that only need the class definition.
    """

    def __init__(self, brand_config: Optional[dict] = None) -> None:
        self.brand_config: dict = brand_config or self._load_brand_config()
        self._vector_store = None
        self._db_session = None

    # ------------------------------------------------------------------
    # Lazy accessors
    # ------------------------------------------------------------------

    def _get_vector_store(self):
        """Return a lazily-initialised VectorStore instance."""
        if self._vector_store is None:
            try:
                from app.database.vector_store import VectorStore
                self._vector_store = VectorStore(
                    persist_directory=str(CHROMADB_DIR),
                )
            except Exception as exc:
                logger.warning("Could not init VectorStore: %s", exc)
        return self._vector_store

    def _get_db_session(self):
        """Return a lazily-initialised SQLAlchemy session."""
        if self._db_session is None:
            try:
                from app.database.models import get_session
                self._db_session = get_session()
            except Exception as exc:
                logger.warning("Could not init DB session: %s", exc)
        return self._db_session

    # ------------------------------------------------------------------
    # Brand config
    # ------------------------------------------------------------------

    @staticmethod
    def _load_brand_config() -> dict:
        """Load brand_config.json from brand_assets/."""
        config_path = BRAND_ASSETS_DIR / "brand_config.json"
        if config_path.exists():
            try:
                with open(config_path, encoding="utf-8") as fh:
                    return json.load(fh)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Could not load brand config: %s", exc)
        return {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_brief(
        self,
        query: str,
        content_type: str = "",
        n_results: int = 5,
    ) -> ContentBrief:
        """Assemble a :class:`ContentBrief` by querying all knowledge sources.

        Args:
            query: The user's request / topic description.
            content_type: Optional content type hint (e.g. ``"presentation"``,
                ``"document"``, ``"training"``).  Used to filter library
                matches and recommend templates.
            n_results: Maximum results per ChromaDB collection query.

        Returns:
            A populated ContentBrief.  Individual fields are left empty
            when their data source is unavailable or returns no results.
        """
        brief = ContentBrief(query=query)

        # --- Static brand config ---
        brief.brand_colors = self.brand_config.get("colors", {})
        brief.brand_fonts = self.brand_config.get("fonts", {})
        brief.company_name = self.brand_config.get("company_name", "")
        brief.voice_profile = self.brand_config.get("voice_profile", {})
        brief.terminology_config = self.brand_config.get("terminology", {})

        # --- ChromaDB queries ---
        vs = self._get_vector_store()
        if vs is not None:
            brief.relevant_existing_content = self._query_collection(
                vs, "brand_content", query, n_results,
            )
            brief.voice_guidance = self._query_collection(
                vs, "brand_voice", query, n_results=3,
            )
            brief.similar_approved_examples = self._query_collection(
                vs, "generated_examples", query, n_results,
            )
            brief.relevant_terms = self._query_collection(
                vs, "terminology", query, n_results,
            )

            try:
                brief.collection_stats = vs.get_collection_stats()
            except Exception:
                pass

        # --- SQLite queries ---
        brief.library_matches = self._search_content_library(query)
        brief.recommended_template = self._find_best_template(content_type)

        logger.info("Research brief built: %s", brief.summary())
        return brief

    # ------------------------------------------------------------------
    # ChromaDB helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _query_collection(
        vs,
        collection_name: str,
        query: str,
        n_results: int = 5,
    ) -> list[dict]:
        """Query a single ChromaDB collection and return normalised results.

        Returns a list of dicts with ``text``, ``metadata``, ``distance``.
        Empty list on any failure.
        """
        try:
            raw = vs.search(
                collection_name=collection_name,
                query_text=query,
                n_results=n_results,
            )
        except Exception:
            try:
                # Fall back to basic query() if search() is unavailable
                raw = vs.query(
                    collection_name=collection_name,
                    query_text=query,
                    n_results=n_results,
                )
            except Exception as exc:
                logger.debug("Query failed for %s: %s", collection_name, exc)
                return []

        return _normalise_chromadb_results(raw)

    # ------------------------------------------------------------------
    # SQLite helpers
    # ------------------------------------------------------------------

    def _search_content_library(self, query: str) -> list[dict]:
        """Search the ContentLibraryItem table for approved items matching
        the query keywords.
        """
        session = self._get_db_session()
        if session is None:
            return []

        try:
            from app.database.models import ContentLibraryItem

            # Extract keywords (simple word tokenisation)
            keywords = [w.lower() for w in query.split() if len(w) > 2]

            # Build OR filter across title, description, tags, content_text
            from sqlalchemy import or_

            filters = []
            for kw in keywords[:6]:  # Limit to avoid huge queries
                pattern = f"%{kw}%"
                filters.append(ContentLibraryItem.title.ilike(pattern))
                filters.append(ContentLibraryItem.description.ilike(pattern))
                filters.append(ContentLibraryItem.tags.ilike(pattern))
                filters.append(ContentLibraryItem.content_text.ilike(pattern))

            if not filters:
                return []

            items = (
                session.query(ContentLibraryItem)
                .filter(or_(*filters))
                .limit(10)
                .all()
            )

            return [
                {
                    "id": item.id,
                    "title": item.title or "",
                    "description": (item.description or "")[:300],
                    "tags": item.tags or "",
                    "category": item.category or "",
                    "content_text": (item.content_text or "")[:500],
                    "is_approved": item.is_approved,
                    "source_type": item.source_type or "",
                }
                for item in items
            ]
        except Exception as exc:
            logger.debug("Content library search failed: %s", exc)
            return []

    def _find_best_template(self, content_type: str) -> Optional[dict]:
        """Find the best matching BrandAsset template for the content type."""
        session = self._get_db_session()
        if session is None:
            return None

        try:
            from app.database.models import BrandAsset

            q = session.query(BrandAsset).filter(
                BrandAsset.asset_type == "template",
                BrandAsset.is_active == True,  # noqa: E712
            )

            # Try to match content type to template tags
            if content_type:
                # Try specific match first
                type_map = {
                    "presentation": "pptx",
                    "document": "docx",
                    "training": "pptx",
                }
                ext = type_map.get(content_type, "")
                if ext:
                    specific = q.filter(
                        BrandAsset.filename.ilike(f"%{ext}%")
                    ).first()
                    if specific:
                        return {
                            "id": specific.id,
                            "filename": specific.filename,
                            "file_path": specific.file_path,
                            "asset_type": specific.asset_type,
                            "tags": specific.tags or "",
                        }

            # Fallback: return first active template
            first = q.first()
            if first:
                return {
                    "id": first.id,
                    "filename": first.filename,
                    "file_path": first.file_path,
                    "asset_type": first.asset_type,
                    "tags": first.tags or "",
                }
        except Exception as exc:
            logger.debug("Template search failed: %s", exc)

        return None

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close the DB session if open."""
        if self._db_session is not None:
            try:
                self._db_session.close()
            except Exception:
                pass
            self._db_session = None


# ======================================================================
# Module-level helpers
# ======================================================================

def _normalise_chromadb_results(raw: dict) -> list[dict]:
    """Convert raw ChromaDB query output to a flat list of dicts.

    ChromaDB returns nested lists: ``{"ids": [[...]], "documents": [[...]],
    "metadatas": [[...]], "distances": [[...]]}``.  This flattens them
    into ``[{"text": ..., "metadata": ..., "distance": ...}, ...]``.
    """
    results = []
    ids = raw.get("ids", [[]])[0]
    docs = raw.get("documents", [[]])[0]
    metas = raw.get("metadatas", [[]])[0]
    dists = raw.get("distances", [[]])[0]

    for i, doc_id in enumerate(ids):
        text = docs[i] if i < len(docs) else ""
        meta = metas[i] if i < len(metas) else {}
        dist = dists[i] if i < len(dists) else 1.0
        if text:  # Skip empty documents
            results.append({
                "id": doc_id,
                "text": text,
                "metadata": meta or {},
                "distance": dist,
            })

    return results
