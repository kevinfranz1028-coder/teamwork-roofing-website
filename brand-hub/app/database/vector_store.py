"""
Brand Intelligence Content Hub - Vector Store

ChromaDB wrapper for semantic search across brand content,
voice samples, generated examples, and terminology.

Falls back to an in-memory stub when ChromaDB is unavailable
(e.g. Python 3.14 pydantic compatibility issues).
"""

from typing import Dict, List, Optional

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except Exception:
    CHROMADB_AVAILABLE = False


class _InMemoryCollection:
    """Minimal in-memory stand-in for a ChromaDB collection."""

    def __init__(self, name: str):
        self.name = name
        self._docs: Dict[str, dict] = {}

    def add(self, documents: List[str], metadatas: Optional[List[dict]] = None,
            ids: Optional[List[str]] = None, **kwargs):
        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in documents]
        for i, doc_id in enumerate(ids):
            self._docs[doc_id] = {
                "document": documents[i],
                "metadata": metadatas[i] if metadatas else {},
            }

    def query(self, query_texts: List[str], n_results: int = 5, **kwargs):
        all_ids = list(self._docs.keys())[:n_results]
        return {
            "ids": [all_ids],
            "documents": [[self._docs[d]["document"] for d in all_ids]],
            "metadatas": [[self._docs[d]["metadata"] for d in all_ids]],
            "distances": [[0.0] * len(all_ids)],
        }

    def delete(self, ids: List[str]):
        for doc_id in ids:
            self._docs.pop(doc_id, None)

    def count(self) -> int:
        return len(self._docs)


class VectorStore:
    """Persistent ChromaDB vector store with pre-defined brand collections.

    Falls back to in-memory storage when ChromaDB cannot be loaded.
    """

    COLLECTIONS = {
        "brand_content": "Ingested collateral and materials",
        "brand_voice": "Voice analysis samples",
        "generated_examples": "Approved outputs for reference",
        "terminology": "Brand-specific terms",
    }

    def __init__(self, persist_directory: str = "data/chromadb"):
        self._fallback = False
        self._memory_collections: Dict[str, _InMemoryCollection] = {}

        if CHROMADB_AVAILABLE:
            try:
                self.client = chromadb.PersistentClient(
                    path=persist_directory,
                    settings=Settings(anonymized_telemetry=False),
                )
                return
            except Exception:
                pass

        # Fallback: in-memory store
        self._fallback = True
        self.client = None

    @property
    def is_fallback(self) -> bool:
        return self._fallback

    def _get_or_create_collection(self, name: str):
        if name not in self.COLLECTIONS:
            raise ValueError(
                f"Unknown collection '{name}'. "
                f"Valid collections: {list(self.COLLECTIONS.keys())}"
            )

        if self._fallback:
            if name not in self._memory_collections:
                self._memory_collections[name] = _InMemoryCollection(name)
            return self._memory_collections[name]

        try:
            return self.client.get_or_create_collection(name=name)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to get or create collection '{name}': {exc}"
            ) from exc

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: Optional[List[dict]] = None,
        ids: Optional[List[str]] = None,
    ) -> None:
        if not documents:
            raise ValueError("documents list must not be empty.")
        if ids is not None and len(ids) != len(documents):
            raise ValueError(
                f"Length mismatch: {len(ids)} ids vs {len(documents)} documents."
            )
        if metadatas is not None and len(metadatas) != len(documents):
            raise ValueError(
                f"Length mismatch: {len(metadatas)} metadatas vs {len(documents)} documents."
            )

        collection = self._get_or_create_collection(collection_name)
        try:
            kwargs = {"documents": documents}
            if metadatas is not None:
                kwargs["metadatas"] = metadatas
            if ids is not None:
                kwargs["ids"] = ids
            collection.add(**kwargs)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to add documents to '{collection_name}': {exc}"
            ) from exc

    def query(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 5,
    ) -> dict:
        collection = self._get_or_create_collection(collection_name)
        try:
            return collection.query(query_texts=[query_text], n_results=n_results)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to query collection '{collection_name}': {exc}"
            ) from exc

    def delete(self, collection_name: str, ids: List[str]) -> None:
        if not ids:
            raise ValueError("ids list must not be empty.")
        collection = self._get_or_create_collection(collection_name)
        try:
            collection.delete(ids=ids)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to delete documents from '{collection_name}': {exc}"
            ) from exc

    def get_collection_stats(self) -> Dict[str, int]:
        stats: Dict[str, int] = {}
        for name in self.COLLECTIONS:
            try:
                collection = self._get_or_create_collection(name)
                stats[name] = collection.count()
            except Exception:
                stats[name] = 0
        return stats

    def clear_collection(self, collection_name: str) -> None:
        if collection_name not in self.COLLECTIONS:
            raise ValueError(
                f"Unknown collection '{collection_name}'. "
                f"Valid collections: {list(self.COLLECTIONS.keys())}"
            )

        if self._fallback:
            self._memory_collections[collection_name] = _InMemoryCollection(collection_name)
            return

        try:
            self.client.delete_collection(name=collection_name)
            self.client.get_or_create_collection(name=collection_name)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to clear collection '{collection_name}': {exc}"
            ) from exc
