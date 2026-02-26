"""
Brand Intelligence Content Hub - Usage Analytics Engine

Pure data-layer module that computes usage analytics from the SQLite
database and the filesystem.  Every public method returns plain Python
dicts / lists so that UI pages (Streamlit) can feed them straight into
charts, metrics, and tables without importing any plotting library here.

All database queries are wrapped in try/except blocks and return sane
defaults on failure so the dashboard never crashes due to a query error.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import func

from app.config import (
    DOCUMENTS_DIR,
    EXPORTS_DIR,
    OUTPUT_DIR,
    PRESENTATIONS_DIR,
    TRAINING_DIR,
    VISUALS_DIR,
)
from app.database.models import (
    BatchJob,
    BrandAsset,
    ContentLibraryItem,
    GeneratedContent,
    Template,
    get_session,
)

# ---------------------------------------------------------------------------
# Cost estimates per content type (USD)
# ---------------------------------------------------------------------------
COST_PER_TYPE: dict[str, float] = {
    "presentation": 0.05,
    "document": 0.03,
    "training_package": 0.15,
    "visual": 0.02,
    "quiz": 0.04,
    "batch_job": 0.10,
}

# ---------------------------------------------------------------------------
# Time-saved estimates per content type (minutes)
# ---------------------------------------------------------------------------
TIME_SAVED_PER_TYPE: dict[str, int] = {
    "presentation": 120,
    "document": 60,
    "training_package": 240,
    "visual": 30,
    "quiz": 45,
}

# ---------------------------------------------------------------------------
# Canonical content types used across the hub
# ---------------------------------------------------------------------------
CONTENT_TYPES: list[str] = [
    "presentation",
    "document",
    "training_package",
    "visual",
    "quiz",
]


class AnalyticsEngine:
    """Computes usage analytics for the Brand Intelligence Content Hub.

    Every method opens and closes its own DB session so the caller does not
    need to manage session lifecycle.  All methods are safe to call from a
    Streamlit page -- they never raise and always return a default payload
    when the underlying query fails.
    """

    # ------------------------------------------------------------------
    # Constructor
    # ------------------------------------------------------------------
    def __init__(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Generation volume
    # ------------------------------------------------------------------
    def get_generation_volume(self, days: int = 30) -> dict:
        """Generation volume by content type over a rolling window.

        Returns
        -------
        dict
            ``{'by_type': {'presentation': 5, ...},
               'by_day': [{'date': '2024-01-01', 'count': 3}, ...],
               'total': 25}``
        """
        by_type: dict[str, int] = {ct: 0 for ct in CONTENT_TYPES}
        by_day: list[dict[str, Any]] = []
        total: int = 0

        try:
            session = get_session()
            cutoff = datetime.utcnow() - timedelta(days=days)

            # --- counts by type ---
            type_rows = (
                session.query(
                    GeneratedContent.content_type,
                    func.count(GeneratedContent.id),
                )
                .filter(GeneratedContent.generated_at >= cutoff)
                .group_by(GeneratedContent.content_type)
                .all()
            )
            for content_type, count in type_rows:
                key = (content_type or "").lower().strip()
                if key in by_type:
                    by_type[key] = count
                else:
                    by_type[key] = count
                total += count

            # --- counts by day ---
            day_rows = (
                session.query(
                    func.date(GeneratedContent.generated_at).label("day"),
                    func.count(GeneratedContent.id),
                )
                .filter(GeneratedContent.generated_at >= cutoff)
                .group_by("day")
                .order_by("day")
                .all()
            )
            for day, count in day_rows:
                by_day.append({"date": str(day), "count": count})

            session.close()
        except Exception:
            pass

        return {"by_type": by_type, "by_day": by_day, "total": total}

    # ------------------------------------------------------------------
    # Generation timeline (daily breakdown by type, for stacked charts)
    # ------------------------------------------------------------------
    def get_generation_timeline(self, days: int = 30) -> list[dict]:
        """Daily generation counts broken down by content type.

        Returns
        -------
        list[dict]
            ``[{'date': '2024-01-01', 'presentation': 2, 'document': 1, ...}, ...]``
        """
        # Build an empty date scaffold so every day in the range appears
        today = datetime.utcnow().date()
        scaffold: dict[str, dict[str, Any]] = {}
        for offset in range(days):
            d = today - timedelta(days=days - 1 - offset)
            key = d.isoformat()
            scaffold[key] = {"date": key}
            for ct in CONTENT_TYPES:
                scaffold[key][ct] = 0

        try:
            session = get_session()
            cutoff = datetime.utcnow() - timedelta(days=days)

            rows = (
                session.query(
                    func.date(GeneratedContent.generated_at).label("day"),
                    GeneratedContent.content_type,
                    func.count(GeneratedContent.id),
                )
                .filter(GeneratedContent.generated_at >= cutoff)
                .group_by("day", GeneratedContent.content_type)
                .order_by("day")
                .all()
            )

            for day, content_type, count in rows:
                day_str = str(day)
                ct_key = (content_type or "").lower().strip()
                if day_str in scaffold:
                    scaffold[day_str][ct_key] = scaffold[day_str].get(ct_key, 0) + count

            session.close()
        except Exception:
            pass

        return list(scaffold.values())

    # ------------------------------------------------------------------
    # Average generation time
    # ------------------------------------------------------------------
    def get_avg_generation_time(self) -> dict:
        """Average generation time (seconds) by content type.

        Returns
        -------
        dict
            ``{'presentation': 12.5, 'document': 8.3, ...}``
        """
        result: dict[str, float] = {}

        try:
            session = get_session()

            rows = (
                session.query(
                    GeneratedContent.content_type,
                    func.avg(GeneratedContent.generation_time_seconds),
                )
                .filter(GeneratedContent.generation_time_seconds.isnot(None))
                .group_by(GeneratedContent.content_type)
                .all()
            )

            for content_type, avg_time in rows:
                key = (content_type or "").lower().strip()
                result[key] = round(float(avg_time), 2) if avg_time else 0.0

            session.close()
        except Exception:
            pass

        # Ensure every canonical type is present
        for ct in CONTENT_TYPES:
            result.setdefault(ct, 0.0)

        return result

    # ------------------------------------------------------------------
    # API cost estimate
    # ------------------------------------------------------------------
    def get_api_cost_estimate(self, days: int = 30) -> dict:
        """Estimate API costs based on generation counts.

        Uses the rough per-type cost constants defined at module level.

        Returns
        -------
        dict
            ``{'total_cost': 5.50, 'by_type': {...}, 'daily_avg': 0.18}``
        """
        by_type: dict[str, float] = {}
        total_cost: float = 0.0

        try:
            session = get_session()
            cutoff = datetime.utcnow() - timedelta(days=days)

            # Content generation costs
            type_rows = (
                session.query(
                    GeneratedContent.content_type,
                    func.count(GeneratedContent.id),
                )
                .filter(GeneratedContent.generated_at >= cutoff)
                .group_by(GeneratedContent.content_type)
                .all()
            )
            for content_type, count in type_rows:
                key = (content_type or "").lower().strip()
                unit_cost = COST_PER_TYPE.get(key, 0.03)
                cost = round(unit_cost * count, 2)
                by_type[key] = cost
                total_cost += cost

            # Batch job costs
            batch_count = (
                session.query(func.count(BatchJob.id))
                .filter(BatchJob.created_at >= cutoff)
                .scalar()
            ) or 0
            if batch_count:
                batch_cost = round(COST_PER_TYPE["batch_job"] * batch_count, 2)
                by_type["batch_job"] = batch_cost
                total_cost += batch_cost

            session.close()
        except Exception:
            pass

        total_cost = round(total_cost, 2)
        daily_avg = round(total_cost / max(days, 1), 2)

        return {
            "total_cost": total_cost,
            "by_type": by_type,
            "daily_avg": daily_avg,
        }

    # ------------------------------------------------------------------
    # Template usage
    # ------------------------------------------------------------------
    def get_template_usage(self) -> list[dict]:
        """Most-used templates ranked by ``usage_count`` descending.

        Returns
        -------
        list[dict]
            ``[{'name': 'Job Aid', 'type': 'docx', 'usage_count': 15}, ...]``
        """
        results: list[dict] = []

        try:
            session = get_session()

            rows = (
                session.query(Template)
                .order_by(Template.usage_count.desc())
                .all()
            )

            for row in rows:
                results.append(
                    {
                        "id": row.id,
                        "name": row.name,
                        "type": row.template_type,
                        "description": row.description or "",
                        "usage_count": row.usage_count or 0,
                        "created_at": (
                            row.created_at.strftime("%Y-%m-%d")
                            if row.created_at
                            else "N/A"
                        ),
                    }
                )

            session.close()
        except Exception:
            pass

        return results

    # ------------------------------------------------------------------
    # Content library stats
    # ------------------------------------------------------------------
    def get_library_stats(self) -> dict:
        """Content library growth and composition.

        Returns
        -------
        dict
            ``{'total_items': 50, 'approved': 40, 'pending': 10,
               'by_category': {...}, 'avg_rating': 4.2,
               'top_downloaded': [...]}``
        """
        result: dict[str, Any] = {
            "total_items": 0,
            "approved": 0,
            "pending": 0,
            "by_category": {},
            "avg_rating": 0.0,
            "top_downloaded": [],
        }

        try:
            session = get_session()

            # Total / approved / pending
            result["total_items"] = session.query(ContentLibraryItem).count()
            result["approved"] = (
                session.query(ContentLibraryItem)
                .filter(ContentLibraryItem.is_approved.is_(True))
                .count()
            )
            result["pending"] = result["total_items"] - result["approved"]

            # Breakdown by category
            cat_rows = (
                session.query(
                    ContentLibraryItem.category,
                    func.count(ContentLibraryItem.id),
                )
                .group_by(ContentLibraryItem.category)
                .all()
            )
            for category, count in cat_rows:
                cat_key = category if category else "Uncategorized"
                result["by_category"][cat_key] = count

            # Average rating (lives on GeneratedContent, joined through library)
            avg_row = (
                session.query(func.avg(GeneratedContent.user_rating))
                .join(
                    ContentLibraryItem,
                    ContentLibraryItem.generated_content_id == GeneratedContent.id,
                )
                .filter(GeneratedContent.user_rating.isnot(None))
                .scalar()
            )
            result["avg_rating"] = round(float(avg_row), 2) if avg_row else 0.0

            # Top downloaded items
            top_rows = (
                session.query(ContentLibraryItem)
                .order_by(ContentLibraryItem.download_count.desc())
                .limit(10)
                .all()
            )
            for row in top_rows:
                result["top_downloaded"].append(
                    {
                        "id": row.id,
                        "title": row.title,
                        "category": row.category or "Uncategorized",
                        "download_count": row.download_count or 0,
                        "is_approved": row.is_approved,
                    }
                )

            session.close()
        except Exception:
            pass

        return result

    # ------------------------------------------------------------------
    # Rating distribution
    # ------------------------------------------------------------------
    def get_rating_distribution(self) -> dict:
        """Distribution of user ratings across all generated content.

        Returns
        -------
        dict
            ``{'1': 2, '2': 5, '3': 10, '4': 20, '5': 15,
               'avg': 3.8, 'total_rated': 52}``
        """
        distribution: dict[str, int] = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
        avg: float = 0.0
        total_rated: int = 0

        try:
            session = get_session()

            rows = (
                session.query(
                    GeneratedContent.user_rating,
                    func.count(GeneratedContent.id),
                )
                .filter(GeneratedContent.user_rating.isnot(None))
                .group_by(GeneratedContent.user_rating)
                .all()
            )

            for rating, count in rows:
                if rating is not None and 1 <= rating <= 5:
                    distribution[str(int(rating))] = count
                    total_rated += count

            avg_row = (
                session.query(func.avg(GeneratedContent.user_rating))
                .filter(GeneratedContent.user_rating.isnot(None))
                .scalar()
            )
            avg = round(float(avg_row), 2) if avg_row else 0.0

            session.close()
        except Exception:
            pass

        return {
            **distribution,
            "avg": avg,
            "total_rated": total_rated,
        }

    # ------------------------------------------------------------------
    # Time saved estimate
    # ------------------------------------------------------------------
    def get_time_saved_estimate(self) -> dict:
        """Estimate total time saved by using AI generation.

        Uses the per-type minute constants defined at module level.

        Returns
        -------
        dict
            ``{'total_minutes': 1200, 'total_hours': 20.0, 'by_type': {...}}``
        """
        by_type: dict[str, int] = {}
        total_minutes: int = 0

        try:
            session = get_session()

            rows = (
                session.query(
                    GeneratedContent.content_type,
                    func.count(GeneratedContent.id),
                )
                .group_by(GeneratedContent.content_type)
                .all()
            )

            for content_type, count in rows:
                key = (content_type or "").lower().strip()
                minutes_per = TIME_SAVED_PER_TYPE.get(key, 30)
                saved = minutes_per * count
                by_type[key] = saved
                total_minutes += saved

            session.close()
        except Exception:
            pass

        return {
            "total_minutes": total_minutes,
            "total_hours": round(total_minutes / 60, 1),
            "by_type": by_type,
        }

    # ------------------------------------------------------------------
    # Storage usage
    # ------------------------------------------------------------------
    def get_storage_usage(self) -> dict:
        """Calculate storage consumed by each output directory.

        Returns
        -------
        dict
            ``{'total_bytes': 123456, 'total_mb': 123.5,
               'by_dir': {'presentations': 50.2, 'documents': 30.1, ...}}``
        """
        dir_map: dict[str, Path] = {
            "presentations": PRESENTATIONS_DIR,
            "documents": DOCUMENTS_DIR,
            "training": TRAINING_DIR,
            "visuals": VISUALS_DIR,
            "exports": EXPORTS_DIR,
        }

        by_dir: dict[str, float] = {}
        total_bytes: int = 0

        for label, path in dir_map.items():
            size = self._get_dir_size(path)
            by_dir[label] = round(size / (1024 * 1024), 2)  # MB
            total_bytes += size

        return {
            "total_bytes": total_bytes,
            "total_mb": round(total_bytes / (1024 * 1024), 2),
            "by_dir": by_dir,
        }

    # ------------------------------------------------------------------
    # Batch job stats
    # ------------------------------------------------------------------
    def get_batch_job_stats(self) -> dict:
        """Statistics on batch processing jobs.

        Returns
        -------
        dict
            ``{'total_jobs': 10, 'completed': 8, 'failed': 1, 'pending': 1,
               'running': 0, 'avg_items_per_job': 5.0, 'success_rate': 0.8}``
        """
        result: dict[str, Any] = {
            "total_jobs": 0,
            "completed": 0,
            "failed": 0,
            "pending": 0,
            "running": 0,
            "avg_items_per_job": 0.0,
            "success_rate": 0.0,
        }

        try:
            session = get_session()

            # Totals by status
            status_rows = (
                session.query(
                    BatchJob.status,
                    func.count(BatchJob.id),
                )
                .group_by(BatchJob.status)
                .all()
            )

            for status, count in status_rows:
                status_key = (status or "").lower().strip()
                result["total_jobs"] += count
                if status_key == "completed":
                    result["completed"] = count
                elif status_key == "failed":
                    result["failed"] = count
                elif status_key == "pending":
                    result["pending"] = count
                elif status_key == "running":
                    result["running"] = count

            # Average items per job (parse items_json for each job)
            all_jobs = session.query(BatchJob).all()
            item_counts: list[int] = []
            for job in all_jobs:
                if job.items_json:
                    try:
                        items = json.loads(job.items_json)
                        if isinstance(items, list):
                            item_counts.append(len(items))
                    except (json.JSONDecodeError, TypeError):
                        pass

            if item_counts:
                result["avg_items_per_job"] = round(
                    sum(item_counts) / len(item_counts), 1
                )

            # Success rate
            finished = result["completed"] + result["failed"]
            if finished > 0:
                result["success_rate"] = round(result["completed"] / finished, 2)

            session.close()
        except Exception:
            pass

        return result

    # ------------------------------------------------------------------
    # Dashboard summary (single call for the main dashboard)
    # ------------------------------------------------------------------
    def get_dashboard_summary(self) -> dict:
        """Combined summary for the dashboard.

        Aggregates the most important metrics from several other methods
        into a single dictionary so the dashboard page can hydrate all its
        widgets with one call.

        Returns
        -------
        dict
            Keys: ``generation_volume``, ``api_cost``, ``time_saved``,
            ``library``, ``batch_jobs``, ``ratings``, ``storage``,
            ``avg_generation_time``, ``template_usage``.
        """
        return {
            "generation_volume": self.get_generation_volume(days=30),
            "api_cost": self.get_api_cost_estimate(days=30),
            "time_saved": self.get_time_saved_estimate(),
            "library": self.get_library_stats(),
            "batch_jobs": self.get_batch_job_stats(),
            "ratings": self.get_rating_distribution(),
            "storage": self.get_storage_usage(),
            "avg_generation_time": self.get_avg_generation_time(),
            "template_usage": self.get_template_usage(),
        }

    # ------------------------------------------------------------------
    # Content type breakdown (pie chart data)
    # ------------------------------------------------------------------
    def get_content_type_breakdown(self) -> list[dict]:
        """Breakdown of all generated content by type (useful for pie charts).

        Returns
        -------
        list[dict]
            ``[{'type': 'presentation', 'count': 15, 'pct': 30.0}, ...]``
        """
        results: list[dict] = []

        try:
            session = get_session()

            rows = (
                session.query(
                    GeneratedContent.content_type,
                    func.count(GeneratedContent.id),
                )
                .group_by(GeneratedContent.content_type)
                .all()
            )

            total = sum(count for _, count in rows)

            for content_type, count in rows:
                key = (content_type or "").lower().strip() or "unknown"
                pct = round((count / total) * 100, 1) if total > 0 else 0.0
                results.append({"type": key, "count": count, "pct": pct})

            # Sort descending by count
            results.sort(key=lambda r: r["count"], reverse=True)

            session.close()
        except Exception:
            pass

        return results

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _get_dir_size(self, path: Path | str) -> int:
        """Recursively calculate directory size in bytes.

        Parameters
        ----------
        path : Path | str
            Root directory to measure.

        Returns
        -------
        int
            Total size in bytes.  Returns ``0`` if the path does not
            exist or an error occurs.
        """
        total: int = 0
        target = Path(path) if not isinstance(path, Path) else path

        if not target.exists():
            return 0

        try:
            for entry in target.rglob("*"):
                if entry.is_file():
                    try:
                        total += entry.stat().st_size
                    except OSError:
                        pass
        except OSError:
            pass

        return total
