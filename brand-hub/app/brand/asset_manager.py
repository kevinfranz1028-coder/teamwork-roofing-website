"""
Brand Intelligence Content Hub - Asset Manager

Manages brand asset files (logos, fonts, colors, collateral, templates, samples).
Handles uploading, organizing, listing, and soft-deleting assets while keeping
the database in sync with the filesystem.
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path

from app.config import BRAND_ASSETS_DIR
from app.database.models import BrandAsset, get_session


# Mapping from asset_type values to their filesystem subdirectories
ASSET_TYPE_DIRS = {
    "logo": "logos",
    "font": "fonts",
    "color": "colors",
    "template": "templates",
    "collateral": "collateral",
    "sample": "sample_content",
}


class AssetManager:
    """Upload, organise, query, and soft-delete brand asset files."""

    def __init__(self):
        """Set up base paths from the project configuration."""
        self.base_dir = BRAND_ASSETS_DIR
        # Ensure every expected subdirectory exists
        for subdir in ASSET_TYPE_DIRS.values():
            (self.base_dir / subdir).mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def upload_asset(self, file_obj, asset_type: str, tags: list[str] | None = None) -> BrandAsset:
        """Save a file to the appropriate brand_assets/ subdirectory and create a DB record.

        Parameters
        ----------
        file_obj : file-like
            An open file object (or ``UploadedFile`` from Streamlit) with a
            ``.name`` attribute and readable content.
        asset_type : str
            One of ``logo``, ``font``, ``color``, ``template``,
            ``collateral``, or ``sample``.
        tags : list[str] | None
            Optional list of tags for categorising the asset.

        Returns
        -------
        BrandAsset
            The newly created database record.

        Raises
        ------
        ValueError
            If *asset_type* is not recognised.
        """
        if asset_type not in ASSET_TYPE_DIRS:
            raise ValueError(
                f"Unknown asset_type '{asset_type}'. "
                f"Must be one of: {', '.join(ASSET_TYPE_DIRS.keys())}"
            )

        subdir = ASSET_TYPE_DIRS[asset_type]
        target_dir = self.base_dir / subdir
        target_dir.mkdir(parents=True, exist_ok=True)

        # Determine the filename; support both plain file objects and
        # Streamlit UploadedFile objects.
        filename = getattr(file_obj, "name", "unnamed_asset")
        filename = os.path.basename(filename)

        # Avoid overwriting existing files by appending a timestamp
        dest_path = target_dir / filename
        if dest_path.exists():
            stem = dest_path.stem
            suffix = dest_path.suffix
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            filename = f"{stem}_{timestamp}{suffix}"
            dest_path = target_dir / filename

        # Write file content to disk
        with open(dest_path, "wb") as out:
            # Handle both file objects with .read() and path-like sources
            if hasattr(file_obj, "read"):
                shutil.copyfileobj(file_obj, out)
            else:
                raise TypeError("file_obj must be a readable file-like object")

        # Create the database record
        tags_str = ",".join(tags) if tags else None
        session = get_session()
        try:
            asset = BrandAsset(
                filename=filename,
                file_path=str(dest_path),
                asset_type=asset_type,
                tags=tags_str,
                is_active=True,
            )
            session.add(asset)
            session.commit()
            session.refresh(asset)
            return asset
        except Exception:
            session.rollback()
            # Clean up the file if the DB insert failed
            if dest_path.exists():
                dest_path.unlink()
            raise
        finally:
            session.close()

    def list_assets(
        self, asset_type: str | None = None, active_only: bool = True
    ) -> list[BrandAsset]:
        """Return a list of BrandAsset records, optionally filtered.

        Parameters
        ----------
        asset_type : str | None
            Filter by asset type (e.g. ``"logo"``).  ``None`` returns all types.
        active_only : bool
            When ``True`` (default), only assets with ``is_active=True`` are returned.

        Returns
        -------
        list[BrandAsset]
        """
        session = get_session()
        try:
            query = session.query(BrandAsset)
            if active_only:
                query = query.filter(BrandAsset.is_active.is_(True))
            if asset_type is not None:
                query = query.filter(BrandAsset.asset_type == asset_type)
            return query.order_by(BrandAsset.uploaded_at.desc()).all()
        finally:
            session.close()

    def get_asset(self, asset_id: int) -> BrandAsset:
        """Retrieve a single BrandAsset by its primary key.

        Parameters
        ----------
        asset_id : int

        Returns
        -------
        BrandAsset

        Raises
        ------
        ValueError
            If no asset with that ID exists.
        """
        session = get_session()
        try:
            asset = session.query(BrandAsset).filter(BrandAsset.id == asset_id).first()
            if asset is None:
                raise ValueError(f"No BrandAsset found with id={asset_id}")
            return asset
        finally:
            session.close()

    def delete_asset(self, asset_id: int) -> BrandAsset:
        """Soft-delete an asset by setting ``is_active = False``.

        Parameters
        ----------
        asset_id : int

        Returns
        -------
        BrandAsset
            The updated record.

        Raises
        ------
        ValueError
            If no asset with that ID exists.
        """
        session = get_session()
        try:
            asset = session.query(BrandAsset).filter(BrandAsset.id == asset_id).first()
            if asset is None:
                raise ValueError(f"No BrandAsset found with id={asset_id}")
            asset.is_active = False
            session.commit()
            session.refresh(asset)
            return asset
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_asset_stats(self) -> dict:
        """Return a dictionary with counts of active assets grouped by type.

        Returns
        -------
        dict
            Example: ``{"logo": 3, "font": 1, "total": 4}``
        """
        session = get_session()
        try:
            assets = (
                session.query(BrandAsset)
                .filter(BrandAsset.is_active.is_(True))
                .all()
            )
            stats: dict[str, int] = {}
            for asset in assets:
                stats[asset.asset_type] = stats.get(asset.asset_type, 0) + 1
            stats["total"] = len(assets)
            return stats
        finally:
            session.close()

    def organize_assets(self) -> dict:
        """Ensure every active asset's file is stored in the correct subdirectory.

        If an asset's file currently lives outside its expected subdirectory
        the file is moved and the database record is updated.

        Returns
        -------
        dict
            ``{"moved": <int>, "errors": [<str>, ...]}``
        """
        moved = 0
        errors: list[str] = []
        session = get_session()
        try:
            assets = (
                session.query(BrandAsset)
                .filter(BrandAsset.is_active.is_(True))
                .all()
            )
            for asset in assets:
                expected_subdir = ASSET_TYPE_DIRS.get(asset.asset_type)
                if expected_subdir is None:
                    errors.append(
                        f"Asset id={asset.id}: unknown type '{asset.asset_type}'"
                    )
                    continue

                expected_dir = self.base_dir / expected_subdir
                expected_dir.mkdir(parents=True, exist_ok=True)
                current_path = Path(asset.file_path)
                expected_path = expected_dir / asset.filename

                if current_path == expected_path:
                    continue

                if not current_path.exists():
                    errors.append(
                        f"Asset id={asset.id}: source file not found at {current_path}"
                    )
                    continue

                try:
                    shutil.move(str(current_path), str(expected_path))
                    asset.file_path = str(expected_path)
                    moved += 1
                except Exception as exc:
                    errors.append(f"Asset id={asset.id}: move failed - {exc}")

            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

        return {"moved": moved, "errors": errors}
