"""
Brand Intelligence Content Hub - Brand Repository Page

Six-tab interface for managing every aspect of brand identity:
Brand Wizard, Assets, Colors & Fonts, Voice Profile, Terminology, Templates.
"""

import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import (
    BASE_DIR,
    BRAND_ASSETS_DIR,
    DATA_DIR,
    LOGOS_DIR,
    FONTS_DIR,
    TEMPLATES_DIR,
    UPLOADS_DIR,
    ensure_directories,
)
from app.database.models import (
    BrandAsset,
    BrandConfig,
    BrandProfile,
    Template,
    get_session,
    init_db,
)

import logging

logger = logging.getLogger(__name__)

try:
    from app.ingestion.smart_classifier import SmartClassifier
    CLASSIFIER_AVAILABLE = True
except ImportError:
    CLASSIFIER_AVAILABLE = False

# Optional parsers for auto-analysis
try:
    from app.ingestion.pdf_parser import PDFParser
    _PDF_OK = True
except ImportError:
    _PDF_OK = False

try:
    from app.ingestion.docx_parser import DOCXParser
    _DOCX_OK = True
except ImportError:
    _DOCX_OK = False

try:
    from app.ingestion.pptx_parser import PPTXParser
    _PPTX_OK = True
except ImportError:
    _PPTX_OK = False

try:
    from app.brand.voice_analyzer import VoiceAnalyzer
    _VOICE_OK = True
except ImportError:
    _VOICE_OK = False

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Brand Repository - Brand Intelligence",
    page_icon="\U0001f3a8",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Initialise
# ---------------------------------------------------------------------------
ensure_directories()

if "db_ok" not in st.session_state:
    try:
        init_db()
        st.session_state["db_ok"] = True
    except Exception as exc:
        st.session_state["db_ok"] = False
        st.session_state["db_error"] = str(exc)


# ===================================================================
# Utility helpers
# ===================================================================

def _load_brand_config() -> dict:
    """Load the brand_config from the database, falling back to JSON file."""
    try:
        session = get_session()
        row = (
            session.query(BrandConfig)
            .filter(BrandConfig.config_key == "brand_config")
            .first()
        )
        session.close()
        if row and row.config_value:
            return json.loads(row.config_value)
    except Exception:
        pass

    # Fallback: try brand_config.json on disk
    json_path = BASE_DIR / "brand_config.json"
    if json_path.exists():
        try:
            return json.loads(json_path.read_text())
        except Exception:
            pass

    return {}


def _save_brand_config(config: dict) -> bool:
    """Persist brand config to both the database and a JSON file."""
    try:
        session = get_session()
        row = (
            session.query(BrandConfig)
            .filter(BrandConfig.config_key == "brand_config")
            .first()
        )
        serialized = json.dumps(config, indent=2, default=str)
        if row:
            row.config_value = serialized
            row.updated_at = datetime.utcnow()
        else:
            row = BrandConfig(config_key="brand_config", config_value=serialized)
            session.add(row)
        session.commit()
        session.close()

        # Also write JSON file for easy inspection
        json_path = BASE_DIR / "brand_config.json"
        json_path.write_text(serialized)

        return True
    except Exception as exc:
        st.error(f"Failed to save brand config: {exc}")
        return False


def _load_voice_profile() -> dict:
    """Load voice profile from DB or brand config."""
    try:
        session = get_session()
        row = (
            session.query(BrandConfig)
            .filter(BrandConfig.config_key == "voice_profile")
            .first()
        )
        session.close()
        if row and row.config_value:
            return json.loads(row.config_value)
    except Exception:
        pass

    # Fallback to brand_config
    bc = _load_brand_config()
    return bc.get("voice_profile", {})


def _save_voice_profile(profile: dict) -> bool:
    """Persist voice profile to the database."""
    try:
        session = get_session()
        row = (
            session.query(BrandConfig)
            .filter(BrandConfig.config_key == "voice_profile")
            .first()
        )
        serialized = json.dumps(profile, indent=2, default=str)
        if row:
            row.config_value = serialized
            row.updated_at = datetime.utcnow()
        else:
            row = BrandConfig(config_key="voice_profile", config_value=serialized)
            session.add(row)
        session.commit()
        session.close()
        return True
    except Exception as exc:
        st.error(f"Failed to save voice profile: {exc}")
        return False


def _load_terminology() -> dict:
    """Load terminology config from the database."""
    try:
        session = get_session()
        row = (
            session.query(BrandConfig)
            .filter(BrandConfig.config_key == "terminology")
            .first()
        )
        session.close()
        if row and row.config_value:
            return json.loads(row.config_value)
    except Exception:
        pass

    bc = _load_brand_config()
    return bc.get("terminology", {})


def _save_terminology(terminology: dict) -> bool:
    """Persist terminology to the database."""
    try:
        session = get_session()
        row = (
            session.query(BrandConfig)
            .filter(BrandConfig.config_key == "terminology")
            .first()
        )
        serialized = json.dumps(terminology, indent=2, default=str)
        if row:
            row.config_value = serialized
            row.updated_at = datetime.utcnow()
        else:
            row = BrandConfig(config_key="terminology", config_value=serialized)
            session.add(row)
        session.commit()
        session.close()
        return True
    except Exception as exc:
        st.error(f"Failed to save terminology: {exc}")
        return False


# ===================================================================
# Auto-analysis helpers
# ===================================================================


def _extract_text_from_assets(asset_types: list[str]) -> str:
    """Extract combined text from all active BrandAssets of the given types.

    Uses PDFParser, DOCXParser, PPTXParser based on file extension.
    Returns concatenated text or empty string on failure.
    """
    session = get_session()
    try:
        assets = (
            session.query(BrandAsset)
            .filter(
                BrandAsset.asset_type.in_(asset_types),
                BrandAsset.is_active.is_(True),
            )
            .all()
        )
    finally:
        session.close()

    chunks: list[str] = []
    for asset in assets:
        fp = Path(asset.file_path)
        if not fp.exists():
            continue
        ext = fp.suffix.lower()
        try:
            if ext == ".pdf" and _PDF_OK:
                parsed = PDFParser().parse(str(fp))
                chunks.append(parsed.get("text", ""))
            elif ext == ".docx" and _DOCX_OK:
                parsed = DOCXParser().parse(str(fp))
                chunks.append(parsed.get("text", ""))
            elif ext == ".pptx" and _PPTX_OK:
                parsed = PPTXParser().parse(str(fp))
                for slide in parsed.get("slides", []):
                    chunks.append(slide.get("title", ""))
                    chunks.extend(slide.get("content", []))
            elif ext in (".txt", ".md"):
                chunks.append(fp.read_text(encoding="utf-8", errors="replace"))
        except Exception as exc:
            logger.warning("Failed to parse %s: %s", fp.name, exc)
    return "\n\n".join(c for c in chunks if c and c.strip())


def _parse_json_response(raw_text: str) -> dict:
    """Extract JSON from a Claude response that may contain markdown fences."""
    import re
    text = raw_text.strip()
    m = re.search(r"```(?:json)?\s*\n(.*?)```", text, re.DOTALL)
    if m:
        text = m.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


# ===================================================================
# Profile management helpers
# ===================================================================

def _get_or_create_default_profile():
    """Ensure a default brand profile exists and return all profiles."""
    session = get_session()
    try:
        profiles = session.query(BrandProfile).order_by(BrandProfile.name).all()
        if not profiles:
            # Create default profile
            default = BrandProfile(
                name="Default",
                description="Default brand profile",
                is_active=True,
                config_json="{}",
            )
            session.add(default)
            session.commit()
            profiles = [default]
        # Ensure exactly one is active
        active = [p for p in profiles if p.is_active]
        if not active:
            profiles[0].is_active = True
            session.commit()
        return [(p.id, p.name, p.is_active) for p in profiles]
    except Exception as exc:
        logger.warning("Failed to load profiles: %s", exc)
        return [(0, "Default", True)]
    finally:
        session.close()


def _switch_profile(profile_id: int):
    """Set the active brand profile."""
    session = get_session()
    try:
        session.query(BrandProfile).update({BrandProfile.is_active: False})
        profile = session.query(BrandProfile).filter(BrandProfile.id == profile_id).first()
        if profile:
            profile.is_active = True
            # Write profile config to brand_config.json
            if profile.config_json:
                config = json.loads(profile.config_json) if profile.config_json else {}
                config_path = BRAND_ASSETS_DIR / "brand_config.json"
                BRAND_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
                config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
            session.commit()
            return True
    except Exception as exc:
        session.rollback()
        logger.warning("Failed to switch profile: %s", exc)
    finally:
        session.close()
    return False


def _create_profile(name: str, description: str = ""):
    """Create a new brand profile."""
    session = get_session()
    try:
        profile = BrandProfile(name=name, description=description, config_json="{}")
        session.add(profile)
        session.commit()
        return profile.id
    except Exception as exc:
        session.rollback()
        logger.warning("Failed to create profile: %s", exc)
        return None
    finally:
        session.close()


def _delete_profile(profile_id: int):
    """Delete a brand profile (cannot delete active)."""
    session = get_session()
    try:
        profile = session.query(BrandProfile).filter(BrandProfile.id == profile_id).first()
        if profile and not profile.is_active:
            session.delete(profile)
            session.commit()
            return True
    except Exception:
        session.rollback()
    finally:
        session.close()
    return False


def _save_config_to_profile():
    """Save current brand_config.json to the active profile."""
    config_path = BRAND_ASSETS_DIR / "brand_config.json"
    if not config_path.exists():
        return
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        session = get_session()
        try:
            active = session.query(BrandProfile).filter(BrandProfile.is_active.is_(True)).first()
            if active:
                active.config_json = json.dumps(config)
                session.commit()
        finally:
            session.close()
    except Exception as exc:
        logger.warning("Failed to save config to profile: %s", exc)


# ===================================================================
# Page header
# ===================================================================
# ---------------------------------------------------------------------------
# Sidebar: Brand Profile Switcher
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### \U0001f3f7\ufe0f Brand Profile")

    profiles = _get_or_create_default_profile()
    profile_names = [p[1] for p in profiles]
    profile_ids = [p[0] for p in profiles]
    active_idx = next((i for i, p in enumerate(profiles) if p[2]), 0)

    selected_name = st.selectbox(
        "Active Profile",
        profile_names,
        index=active_idx,
        key="profile_select",
    )
    selected_idx = profile_names.index(selected_name)
    selected_id = profile_ids[selected_idx]

    if selected_id != profile_ids[active_idx]:
        _switch_profile(selected_id)
        st.rerun()

    with st.expander("Manage Profiles", expanded=False):
        new_name = st.text_input("New Profile Name", key="new_profile_name")
        new_desc = st.text_input("Description", key="new_profile_desc")
        if st.button("\u2795 Create Profile", key="btn_create_profile"):
            if new_name:
                _create_profile(new_name, new_desc)
                st.rerun()

        if len(profiles) > 1:
            del_options = [p[1] for p in profiles if not p[2]]
            if del_options:
                del_name = st.selectbox("Delete Profile", del_options, key="del_profile")
                if st.button("\U0001f5d1\ufe0f Delete", key="btn_del_profile"):
                    del_id = next(p[0] for p in profiles if p[1] == del_name)
                    _delete_profile(del_id)
                    st.rerun()

    if st.button("\U0001f4be Save Config to Profile", key="btn_save_to_profile", use_container_width=True):
        _save_config_to_profile()
        st.success("Saved!")

    st.markdown("---")

st.title("\U0001f3a8 Brand Repository")
st.caption("Manage every aspect of your brand identity")

# ---------------------------------------------------------------------------
# Smart Drop Zone — AI-powered file classification
# ---------------------------------------------------------------------------
st.markdown("### \U0001f4e5 Smart Drop Zone")
st.caption("Drop any brand files here \u2014 logos, guidelines, templates, marketing materials \u2014 and they'll be auto-analyzed and organized.")

drop_files = st.file_uploader(
    "Drop files here for auto-classification",
    accept_multiple_files=True,
    type=["pdf", "docx", "pptx", "xlsx", "csv", "png", "jpg", "jpeg", "gif", "svg",
          "txt", "md", "json", "ttf", "otf", "woff", "woff2", "bmp", "webp", "tiff"],
    key="smart_drop_zone",
    label_visibility="collapsed",
)

# Initialise classification cache in session state
if "drop_zone_classified" not in st.session_state:
    st.session_state["drop_zone_classified"] = {}  # filename -> classification result
if "drop_zone_saved" not in st.session_state:
    st.session_state["drop_zone_saved"] = set()  # filenames already saved

if drop_files:
    if not CLASSIFIER_AVAILABLE:
        st.warning("Smart classifier not available. Files will be uploaded with manual classification.")

    # --- Step 1: classify only NEW files (not already cached) ---
    new_files = [f for f in drop_files if f.name not in st.session_state["drop_zone_classified"]]
    if new_files:
        classifier = SmartClassifier() if CLASSIFIER_AVAILABLE else None
        progress = st.progress(0, text="Analyzing files...")
        for idx, uploaded_file in enumerate(new_files):
            temp_path = UPLOADS_DIR / uploaded_file.name
            temp_path.parent.mkdir(parents=True, exist_ok=True)
            with open(temp_path, "wb") as fout:
                fout.write(uploaded_file.getbuffer())

            if classifier:
                progress.progress((idx) / len(new_files), text=f"Analyzing {uploaded_file.name}...")
                result = classifier.classify_file(str(temp_path))
            else:
                ext = Path(uploaded_file.name).suffix.lower()
                result = {
                    "asset_type": "collateral",
                    "tags": [ext.lstrip(".")],
                    "description": uploaded_file.name,
                    "confidence": 0.3,
                }
            st.session_state["drop_zone_classified"][uploaded_file.name] = result

        progress.progress(1.0, text="Analysis complete!")

    # --- Step 2: helper to save a single file ---
    def _save_single(filename: str, asset_type: str, tags_str: str, classification: dict) -> str | None:
        """Save one file to the brand repository. Returns error string or None."""
        temp_path = UPLOADS_DIR / filename
        if not temp_path.exists():
            return f"File not found: {filename}"
        try:
            from app.brand.asset_manager import AssetManager
            manager = AssetManager()
            with open(temp_path, "rb") as fobj:
                asset = manager.upload_asset(
                    file_obj=fobj,
                    asset_type=asset_type,
                    tags=[t.strip() for t in tags_str.split(",") if t.strip()],
                )
            session = get_session()
            try:
                active_profile = session.query(BrandProfile).filter(BrandProfile.is_active.is_(True)).first()
                if active_profile and asset:
                    asset = session.merge(asset)
                    asset.brand_profile_id = active_profile.id
                    asset.metadata_json = json.dumps(classification.get("metadata", {}))
                    session.commit()
            finally:
                session.close()
            return None
        except Exception as exc:
            return str(exc)

    # --- Step 3: Show Save All button at the top ---
    unsaved = [f for f in drop_files if f.name not in st.session_state["drop_zone_saved"]]
    if unsaved:
        if st.button(f"Save All ({len(unsaved)} files)", key="save_all_drop", type="primary"):
            saved_count = 0
            errors = []
            save_bar = st.progress(0, text="Saving...")
            for idx, uploaded_file in enumerate(unsaved):
                fname = uploaded_file.name
                classification = st.session_state["drop_zone_classified"].get(fname, {})
                a_type = st.session_state.get(f"type_{fname}", classification.get("asset_type", "collateral"))
                a_tags = st.session_state.get(f"tags_{fname}", ", ".join(classification.get("tags", [])))
                save_bar.progress((idx) / len(unsaved), text=f"Saving {fname}...")
                err = _save_single(fname, a_type, a_tags, classification)
                if err:
                    errors.append(f"{fname}: {err}")
                else:
                    st.session_state["drop_zone_saved"].add(fname)
                    saved_count += 1
            save_bar.progress(1.0, text="Done!")
            if saved_count:
                st.success(f"Saved {saved_count} file(s) to Brand Repository!")
            for e in errors:
                st.error(e)

    # --- Step 4: Show each file with override options ---
    for uploaded_file in drop_files:
        fname = uploaded_file.name
        result = st.session_state["drop_zone_classified"].get(fname, {})
        already_saved = fname in st.session_state["drop_zone_saved"]

        if already_saved:
            st.success(f"Saved: {fname}")
            continue

        with st.expander(f"\U0001f4c4 {fname} \u2014 {result.get('asset_type', 'unknown').title()} ({result.get('confidence', 0):.0%})", expanded=True):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.selectbox(
                    "Asset Type",
                    ["logo", "font", "color", "template", "collateral", "sample"],
                    index=["logo", "font", "color", "template", "collateral", "sample"].index(
                        result.get("asset_type", "collateral")
                    ),
                    key=f"type_{fname}",
                )
            with col2:
                st.text_input(
                    "Tags",
                    value=", ".join(result.get("tags", [])),
                    key=f"tags_{fname}",
                )
            with col3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Save", key=f"save_{fname}"):
                    a_type = st.session_state.get(f"type_{fname}", result.get("asset_type", "collateral"))
                    a_tags = st.session_state.get(f"tags_{fname}", ", ".join(result.get("tags", [])))
                    err = _save_single(fname, a_type, a_tags, result)
                    if err:
                        st.error(f"Failed: {err}")
                    else:
                        st.session_state["drop_zone_saved"].add(fname)
                        st.rerun()

            st.caption(f"Description: {result.get('description', '')}")

st.markdown("---")

# ===================================================================
# Tabs
# ===================================================================
(
    tab_wizard,
    tab_assets,
    tab_colors,
    tab_voice,
    tab_terms,
    tab_templates,
) = st.tabs(
    [
        "\U0001f9d9 Brand Wizard",
        "\U0001f4e6 Assets",
        "\U0001f3a8 Colors & Fonts",
        "\U0001f5e3\ufe0f Voice Profile",
        "\U0001f4d6 Terminology",
        "\U0001f4c4 Templates",
    ]
)

# ===================================================================
# TAB 1: Brand Wizard
# ===================================================================
with tab_wizard:
    st.subheader("Brand Wizard")
    st.markdown(
        "Extract your brand identity automatically from your website and existing documents."
    )

    # Initialise wizard session state
    if "wizard_results" not in st.session_state:
        st.session_state["wizard_results"] = None

    col_url, col_btn = st.columns([3, 1])
    with col_url:
        brand_url = st.text_input(
            "Brand Website URL",
            placeholder="https://yourcompany.com",
            key="wizard_url",
        )
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        extract_btn = st.button("Extract Brand", key="wizard_extract", use_container_width=True)

    st.markdown("---")

    # Logo upload
    st.markdown("#### Upload Logo")
    logo_file = st.file_uploader(
        "Upload your primary logo",
        type=["png", "jpg", "jpeg", "svg", "webp"],
        key="wizard_logo",
    )
    if logo_file is not None:
        # Save uploaded logo
        LOGOS_DIR.mkdir(parents=True, exist_ok=True)
        logo_dest = LOGOS_DIR / logo_file.name
        logo_dest.write_bytes(logo_file.getvalue())

        # Register in database
        try:
            session = get_session()
            existing = (
                session.query(BrandAsset)
                .filter(
                    BrandAsset.filename == logo_file.name,
                    BrandAsset.asset_type == "logo",
                )
                .first()
            )
            if not existing:
                asset = BrandAsset(
                    filename=logo_file.name,
                    file_path=str(logo_dest),
                    asset_type="logo",
                    tags="logo,primary",
                )
                session.add(asset)
                session.commit()
            session.close()
        except Exception:
            pass

        st.success(f"Logo saved: {logo_file.name}")
        if logo_file.type and logo_file.type.startswith("image/"):
            st.image(logo_file, width=200)

    st.markdown("---")

    # Sample documents upload
    st.markdown("#### Upload Sample Documents")
    st.caption("Upload existing branded documents for voice and style analysis.")
    sample_files = st.file_uploader(
        "Upload sample brand documents",
        type=["pdf", "docx", "pptx", "txt"],
        accept_multiple_files=True,
        key="wizard_samples",
    )
    if sample_files:
        sample_dir = BRAND_ASSETS_DIR / "sample_content"
        sample_dir.mkdir(parents=True, exist_ok=True)
        for f in sample_files:
            dest = sample_dir / f.name
            dest.write_bytes(f.getvalue())
        st.success(f"Saved {len(sample_files)} sample document(s)")

    st.markdown("---")

    # Run Full Wizard
    if st.button("Run Full Wizard", key="wizard_run_full", type="primary", use_container_width=True):
        with st.spinner("Running Brand Wizard -- extracting identity from all sources..."):
            results = {}

            # Attempt to call BrandWizard if available
            try:
                from app.brand.brand_wizard import BrandWizard

                wizard = BrandWizard()

                if brand_url:
                    with st.status("Extracting from website...", expanded=True) as status:
                        web_result = wizard.extract_from_url(brand_url)
                        results["website"] = web_result
                        status.update(label="Website extraction complete", state="complete")

                if logo_file is not None:
                    with st.status("Analyzing logo colors...", expanded=True) as status:
                        color_result = wizard.extract_colors(str(LOGOS_DIR / logo_file.name))
                        results["colors"] = color_result
                        status.update(label="Color extraction complete", state="complete")

                if sample_files:
                    with st.status("Analyzing voice and style...", expanded=True) as status:
                        sample_paths = [
                            str(BRAND_ASSETS_DIR / "sample_content" / f.name)
                            for f in sample_files
                        ]
                        voice_result = wizard.analyze_voice(sample_paths)
                        results["voice"] = voice_result
                        status.update(label="Voice analysis complete", state="complete")

                st.session_state["wizard_results"] = results

            except ImportError:
                st.warning(
                    "BrandWizard module not yet available. "
                    "The wizard will be fully functional once `app/brand/brand_wizard.py` is created. "
                    "You can still manually configure your brand in the other tabs."
                )
                # Create placeholder results
                results = {
                    "status": "wizard_module_pending",
                    "url_provided": brand_url or None,
                    "logo_uploaded": logo_file.name if logo_file else None,
                    "samples_uploaded": [f.name for f in sample_files] if sample_files else [],
                }
                st.session_state["wizard_results"] = results

            except Exception as exc:
                st.error(f"Wizard error: {exc}")

    # Display wizard results
    if st.session_state.get("wizard_results"):
        results = st.session_state["wizard_results"]
        st.markdown("---")
        st.subheader("Wizard Results")

        if "website" in results:
            with st.expander("Website Extraction", expanded=True):
                st.json(results["website"])

        if "colors" in results:
            with st.expander("Extracted Colors", expanded=True):
                color_data = results["colors"]
                if isinstance(color_data, dict) and "palette" in color_data:
                    cols = st.columns(min(len(color_data["palette"]), 6))
                    for i, color in enumerate(color_data["palette"][:6]):
                        with cols[i]:
                            st.color_picker(f"Color {i+1}", color, key=f"wiz_color_{i}")
                else:
                    st.json(color_data)

        if "voice" in results:
            with st.expander("Voice Analysis", expanded=True):
                st.json(results["voice"])

        if results.get("status") == "wizard_module_pending":
            st.info("Wizard module pending. Inputs recorded:")
            st.json(results)

        # Save button
        if st.button("Save Brand Config", key="wizard_save", type="primary"):
            config = _load_brand_config()
            config["wizard_results"] = results
            config["last_wizard_run"] = datetime.utcnow().isoformat()
            if _save_brand_config(config):
                st.success("Brand configuration saved successfully.")
                st.balloons()


# ===================================================================
# TAB 2: Assets
# ===================================================================
with tab_assets:
    st.subheader("Brand Assets")
    st.markdown("Upload and manage logos, fonts, images, and other brand collateral.")

    # Upload section
    st.markdown("#### Upload New Assets")
    upload_col1, upload_col2 = st.columns([2, 1])

    with upload_col1:
        uploaded_files = st.file_uploader(
            "Drag and drop files here",
            accept_multiple_files=True,
            type=["png", "jpg", "jpeg", "svg", "webp", "gif", "pdf", "docx", "pptx", "ttf", "otf", "woff", "woff2"],
            key="asset_upload",
        )

    with upload_col2:
        asset_type = st.selectbox(
            "Asset Type",
            ["logo", "font", "color", "template", "collateral", "sample"],
            key="asset_type_select",
        )
        asset_tags = st.text_input(
            "Tags (comma-separated)",
            placeholder="primary, header, dark-bg",
            key="asset_tags",
        )

    if uploaded_files:
        if st.button("Save Uploaded Assets", key="save_assets", type="primary"):
            # Determine target directory
            type_dir_map = {
                "logo": LOGOS_DIR,
                "font": FONTS_DIR,
                "template": TEMPLATES_DIR,
                "collateral": BRAND_ASSETS_DIR / "collateral",
                "sample": BRAND_ASSETS_DIR / "sample_content",
                "color": BRAND_ASSETS_DIR / "colors",
            }
            target_dir = type_dir_map.get(asset_type, UPLOADS_DIR)
            target_dir.mkdir(parents=True, exist_ok=True)

            saved_count = 0
            for f in uploaded_files:
                dest = target_dir / f.name
                dest.write_bytes(f.getvalue())

                # Register in database
                try:
                    session = get_session()
                    existing = (
                        session.query(BrandAsset)
                        .filter(
                            BrandAsset.filename == f.name,
                            BrandAsset.asset_type == asset_type,
                        )
                        .first()
                    )
                    if existing:
                        existing.file_path = str(dest)
                        existing.tags = asset_tags
                        existing.uploaded_at = datetime.utcnow()
                    else:
                        asset = BrandAsset(
                            filename=f.name,
                            file_path=str(dest),
                            asset_type=asset_type,
                            tags=asset_tags,
                        )
                        session.add(asset)
                    session.commit()
                    session.close()
                    saved_count += 1
                except Exception as exc:
                    st.error(f"DB error for {f.name}: {exc}")

            st.success(f"Saved {saved_count} asset(s) to {asset_type} directory.")
            st.rerun()

    st.markdown("---")

    # Asset gallery
    st.markdown("#### Asset Gallery")

    filter_type = st.selectbox(
        "Filter by type",
        ["all", "logo", "font", "color", "template", "collateral", "sample"],
        key="gallery_filter",
    )

    try:
        session = get_session()
        query = session.query(BrandAsset).filter(BrandAsset.is_active.is_(True))
        if filter_type != "all":
            query = query.filter(BrandAsset.asset_type == filter_type)
        assets = query.order_by(BrandAsset.uploaded_at.desc()).all()
        session.close()

        if assets:
            # Display in a grid
            cols_per_row = 4
            for i in range(0, len(assets), cols_per_row):
                row_assets = assets[i : i + cols_per_row]
                cols = st.columns(cols_per_row)
                for j, asset in enumerate(row_assets):
                    with cols[j]:
                        st.markdown(
                            f"<div class='brand-card'>"
                            f"<strong>{asset.filename}</strong><br>"
                            f"<small>Type: {asset.asset_type}</small><br>"
                            f"<small>Tags: {asset.tags or 'none'}</small><br>"
                            f"<small>Uploaded: {asset.uploaded_at.strftime('%Y-%m-%d') if asset.uploaded_at else 'N/A'}</small>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )

                        # Show preview for images
                        asset_path = Path(asset.file_path)
                        if asset_path.exists() and asset_path.suffix.lower() in [
                            ".png", ".jpg", ".jpeg", ".webp", ".gif",
                        ]:
                            try:
                                st.image(str(asset_path), width=150)
                            except Exception:
                                pass

                        # Delete button
                        if st.button(
                            "Delete",
                            key=f"del_asset_{asset.id}",
                            type="secondary",
                        ):
                            try:
                                session = get_session()
                                db_asset = session.query(BrandAsset).get(asset.id)
                                if db_asset:
                                    db_asset.is_active = False
                                    session.commit()
                                session.close()
                                st.success(f"Deleted: {asset.filename}")
                                st.rerun()
                            except Exception as exc:
                                st.error(f"Delete failed: {exc}")
        else:
            st.info("No assets uploaded yet. Use the uploader above to add brand assets.")

    except Exception as exc:
        st.error(f"Error loading assets: {exc}")


# ===================================================================
# TAB 3: Colors & Fonts
# ===================================================================
with tab_colors:
    st.subheader("Colors & Fonts")
    st.markdown("View and edit your brand color palette and typography settings.")

    config = _load_brand_config()
    colors_data = config.get("colors", {})
    fonts_data = config.get("fonts", {})

    # --- Color Palette ---
    st.markdown("#### Color Palette")

    # Default palette structure
    default_palette = {
        "primary": "#0066cc",
        "secondary": "#1a1a2e",
        "accent": "#00d2ff",
        "background": "#ffffff",
        "text": "#333333",
        "success": "#28a745",
        "warning": "#ffc107",
        "error": "#dc3545",
    }

    current_palette = colors_data.get("palette", default_palette)
    if isinstance(current_palette, list):
        # Convert list format to dict
        current_palette = {f"color_{i+1}": c for i, c in enumerate(current_palette)}

    updated_palette = {}
    color_cols = st.columns(min(len(current_palette), 4))
    for idx, (name, hex_val) in enumerate(current_palette.items()):
        col_idx = idx % len(color_cols)
        with color_cols[col_idx]:
            new_color = st.color_picker(
                f"{name.replace('_', ' ').title()}",
                hex_val if isinstance(hex_val, str) else "#000000",
                key=f"color_{name}",
            )
            updated_palette[name] = new_color
            st.caption(new_color.upper())

    # Add color button
    st.markdown("")
    add_col1, add_col2, add_col3 = st.columns([2, 2, 1])
    with add_col1:
        new_color_name = st.text_input("New color name", placeholder="highlight", key="new_color_name")
    with add_col2:
        new_color_val = st.color_picker("New color value", "#ff6600", key="new_color_val")
    with add_col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Add Color", key="add_color"):
            if new_color_name:
                updated_palette[new_color_name.strip().lower().replace(" ", "_")] = new_color_val
                st.success(f"Added color: {new_color_name}")

    st.markdown("---")

    # --- Fonts ---
    st.markdown("#### Typography")

    default_fonts = {
        "heading_font": "Inter",
        "body_font": "Open Sans",
        "mono_font": "Fira Code",
    }
    current_fonts = fonts_data if fonts_data else default_fonts

    font_col1, font_col2, font_col3 = st.columns(3)
    with font_col1:
        heading_font = st.text_input(
            "Heading Font",
            value=current_fonts.get("heading_font", "Inter"),
            key="heading_font",
        )
    with font_col2:
        body_font = st.text_input(
            "Body Font",
            value=current_fonts.get("body_font", "Open Sans"),
            key="body_font",
        )
    with font_col3:
        mono_font = st.text_input(
            "Monospace Font",
            value=current_fonts.get("mono_font", "Fira Code"),
            key="mono_font",
        )

    st.markdown("---")

    # Save button
    if st.button("Save Colors & Fonts", key="save_colors_fonts", type="primary"):
        config = _load_brand_config()
        config["colors"] = {"palette": updated_palette}
        config["fonts"] = {
            "heading_font": heading_font,
            "body_font": body_font,
            "mono_font": mono_font,
        }
        if _save_brand_config(config):
            st.success("Colors and fonts saved successfully.")


# ===================================================================
# TAB 4: Voice Profile
# ===================================================================
with tab_voice:
    st.subheader("Voice Profile")
    st.markdown("Define how your brand communicates: tone, formality, vocabulary, and messaging.")

    # --- Auto-analyze voice from brand documents ---
    if _VOICE_OK:
        if st.button("Auto-analyze Voice from Brand Documents", key="auto_voice"):
            with st.spinner("Extracting text from brand assets and analyzing voice..."):
                combined = _extract_text_from_assets(["template", "collateral", "sample"])
                if not combined.strip():
                    st.warning("No text found in uploaded assets. Upload brand documents first.")
                else:
                    analyzer = VoiceAnalyzer()
                    # Limit text to ~8000 chars to keep API call reasonable
                    analysis = analyzer.analyze_text(combined[:8000])

                    if analysis and not analysis.get("error"):
                        # Map formality int (1-5) to label
                        formality_map = {1: "Very Formal", 2: "Formal", 3: "Semi-Formal", 4: "Casual", 5: "Very Casual"}
                        raw_formality = analysis.get("formality", 3)
                        if isinstance(raw_formality, int):
                            formality_label = formality_map.get(raw_formality, "Semi-Formal")
                        else:
                            formality_label = str(raw_formality) if raw_formality else "Semi-Formal"

                        # Map vocabulary level
                        vocab_raw = analysis.get("vocabulary_level", "Moderate")
                        vocab_map = {"basic": "Simple", "simple": "Simple", "intermediate": "Moderate",
                                     "moderate": "Moderate", "advanced": "Advanced",
                                     "technical": "Technical", "expert": "Expert"}
                        vocab_label = vocab_map.get(str(vocab_raw).lower(), "Moderate")

                        voice_profile = {
                            "tone": analysis.get("tone", "Professional"),
                            "formality": formality_label,
                            "vocabulary_level": vocab_label,
                            "key_phrases": analysis.get("key_phrases", []),
                            "avoid_phrases": [],
                            "messaging_themes": analysis.get("messaging_themes", []),
                        }
                        _save_voice_profile(voice_profile)
                        config = _load_brand_config()
                        config["voice_profile"] = voice_profile
                        _save_brand_config(config)
                        st.success("Voice profile auto-populated from your brand documents!")
                        st.rerun()
                    else:
                        st.error(f"Analysis failed: {analysis.get('error', 'Unknown error')}")
        st.markdown("---")

    voice = _load_voice_profile()

    # Tone
    st.markdown("#### Tone")
    tone = st.text_input(
        "Brand Tone",
        value=voice.get("tone", "Professional, approachable, confident"),
        key="voice_tone",
        help="Describe the overall tone of your brand's communications.",
    )

    # Formality
    st.markdown("#### Formality Level")
    formality_options = ["Very Formal", "Formal", "Semi-Formal", "Casual", "Very Casual"]
    current_formality = voice.get("formality", "Semi-Formal")
    formality_index = formality_options.index(current_formality) if current_formality in formality_options else 2
    formality = st.select_slider(
        "Formality",
        options=formality_options,
        value=formality_options[formality_index],
        key="voice_formality",
    )

    # Vocabulary level
    st.markdown("#### Vocabulary Level")
    vocab_options = ["Simple", "Moderate", "Advanced", "Technical", "Expert"]
    current_vocab = voice.get("vocabulary_level", "Moderate")
    vocab_index = vocab_options.index(current_vocab) if current_vocab in vocab_options else 1
    vocabulary = st.select_slider(
        "Vocabulary Level",
        options=vocab_options,
        value=vocab_options[vocab_index],
        key="voice_vocabulary",
    )

    st.markdown("---")

    # Key phrases
    st.markdown("#### Key Phrases")
    st.caption("Phrases that should be used frequently in brand communications.")
    current_key_phrases = voice.get("key_phrases", [])
    key_phrases_text = st.text_area(
        "Key Phrases (one per line)",
        value="\n".join(current_key_phrases) if current_key_phrases else "",
        height=120,
        key="voice_key_phrases",
    )

    # Avoid phrases
    st.markdown("#### Phrases to Avoid")
    st.caption("Phrases or words that should never appear in brand communications.")
    current_avoid_phrases = voice.get("avoid_phrases", [])
    avoid_phrases_text = st.text_area(
        "Avoid Phrases (one per line)",
        value="\n".join(current_avoid_phrases) if current_avoid_phrases else "",
        height=120,
        key="voice_avoid_phrases",
    )

    st.markdown("---")

    # Messaging themes
    st.markdown("#### Messaging Themes")
    st.caption("Core themes and messages that underpin all brand communications.")
    current_themes = voice.get("messaging_themes", [])
    themes_text = st.text_area(
        "Messaging Themes (one per line)",
        value="\n".join(current_themes) if current_themes else "",
        height=120,
        key="voice_themes",
    )

    st.markdown("---")

    # Save voice profile
    if st.button("Save Voice Profile", key="save_voice", type="primary"):
        updated_voice = {
            "tone": tone,
            "formality": formality,
            "vocabulary_level": vocabulary,
            "key_phrases": [
                p.strip() for p in key_phrases_text.split("\n") if p.strip()
            ],
            "avoid_phrases": [
                p.strip() for p in avoid_phrases_text.split("\n") if p.strip()
            ],
            "messaging_themes": [
                t.strip() for t in themes_text.split("\n") if t.strip()
            ],
        }
        if _save_voice_profile(updated_voice):
            # Also update brand_config
            config = _load_brand_config()
            config["voice_profile"] = updated_voice
            _save_brand_config(config)
            st.success("Voice profile saved successfully.")


# ===================================================================
# TAB 5: Terminology
# ===================================================================
with tab_terms:
    st.subheader("Terminology")
    st.markdown(
        "Manage preferred terms, program names, and acronyms to ensure consistent language."
    )

    # --- Auto-extract terminology from brand documents ---
    if st.button("Auto-extract Terminology from Brand Documents", key="auto_terminology"):
        with st.spinner("Extracting terminology from brand assets..."):
            combined = _extract_text_from_assets(["template", "collateral", "sample"])
            if not combined.strip():
                st.warning("No text found in uploaded assets. Upload brand documents first.")
            else:
                try:
                    import anthropic
                    client = anthropic.Anthropic()
                    prompt = (
                        "Analyze the following brand/corporate documents and extract:\n\n"
                        "1. **preferred_terms**: A dictionary where keys are informal/incorrect terms "
                        "and values are the preferred/official replacements. Focus on brand-specific "
                        "language, product names that should always be written a certain way, etc.\n\n"
                        "2. **program_names**: A list of official program names, product names, "
                        "service names, and initiative names mentioned.\n\n"
                        "3. **acronyms**: A dictionary where keys are acronyms (uppercase) and "
                        "values are their full expansions.\n\n"
                        "Return ONLY a JSON object with these three keys. No explanation.\n\n"
                        "---\n\n"
                        f"{combined[:6000]}"
                    )
                    resp = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=2048,
                        messages=[{"role": "user", "content": prompt}],
                    )
                    result = _parse_json_response(resp.content[0].text)

                    if result:
                        # Merge with existing terminology (don't overwrite manual entries)
                        existing = _load_terminology()
                        merged = {
                            "preferred_terms": {
                                **result.get("preferred_terms", {}),
                                **existing.get("preferred_terms", {}),
                            },
                            "program_names": list(set(
                                existing.get("program_names", [])
                                + result.get("program_names", [])
                            )),
                            "acronyms": {
                                **result.get("acronyms", {}),
                                **existing.get("acronyms", {}),
                            },
                        }
                        _save_terminology(merged)
                        config = _load_brand_config()
                        config["terminology"] = merged
                        _save_brand_config(config)

                        # Reset session state rows so UI reflects new data
                        st.session_state["term_rows"] = (
                            list(merged["preferred_terms"].items()) if merged["preferred_terms"] else [("", "")]
                        )
                        st.session_state["acronym_rows"] = (
                            list(merged["acronyms"].items()) if merged["acronyms"] else [("", "")]
                        )

                        st.success(
                            f"Extracted {len(result.get('preferred_terms', {}))} terms, "
                            f"{len(result.get('program_names', []))} programs, "
                            f"{len(result.get('acronyms', {}))} acronyms!"
                        )
                        st.rerun()
                    else:
                        st.error("Could not parse terminology from AI response.")
                except Exception as exc:
                    st.error(f"Auto-extraction failed: {exc}")

    st.markdown("---")

    terminology = _load_terminology()

    # --- Preferred Terms ---
    st.markdown("#### Preferred Terms")
    st.caption(
        "Key-value pairs: the key is the term to avoid, the value is the preferred replacement."
    )

    preferred_terms = terminology.get("preferred_terms", {})
    if "term_rows" not in st.session_state:
        st.session_state["term_rows"] = (
            list(preferred_terms.items()) if preferred_terms else [("", "")]
        )

    updated_terms = {}
    terms_to_remove = []

    for i, (avoid, preferred) in enumerate(st.session_state["term_rows"]):
        t_col1, t_col2, t_col3 = st.columns([2, 2, 0.5])
        with t_col1:
            new_avoid = st.text_input(
                "Avoid",
                value=avoid,
                key=f"term_avoid_{i}",
                label_visibility="collapsed" if i > 0 else "visible",
            )
        with t_col2:
            new_preferred = st.text_input(
                "Use Instead",
                value=preferred,
                key=f"term_preferred_{i}",
                label_visibility="collapsed" if i > 0 else "visible",
            )
        with t_col3:
            if i > 0:
                st.markdown("<br>", unsafe_allow_html=True)
            if st.button("\u2716", key=f"term_del_{i}"):
                terms_to_remove.append(i)

        if new_avoid.strip():
            updated_terms[new_avoid.strip()] = new_preferred.strip()

    if terms_to_remove:
        st.session_state["term_rows"] = [
            row for idx, row in enumerate(st.session_state["term_rows"])
            if idx not in terms_to_remove
        ]
        st.rerun()

    if st.button("Add Term", key="add_term"):
        st.session_state["term_rows"].append(("", ""))
        st.rerun()

    st.markdown("---")

    # --- Program Names ---
    st.markdown("#### Program Names")
    st.caption("Official names for programs, products, or services.")

    program_names = terminology.get("program_names", [])
    programs_text = st.text_area(
        "Program Names (one per line)",
        value="\n".join(program_names) if program_names else "",
        height=120,
        key="term_programs",
    )

    st.markdown("---")

    # --- Acronyms ---
    st.markdown("#### Acronyms")
    st.caption("Key-value pairs: acronym and its full expansion.")

    acronyms = terminology.get("acronyms", {})
    if "acronym_rows" not in st.session_state:
        st.session_state["acronym_rows"] = (
            list(acronyms.items()) if acronyms else [("", "")]
        )

    updated_acronyms = {}
    acronyms_to_remove = []

    for i, (acr, expansion) in enumerate(st.session_state["acronym_rows"]):
        a_col1, a_col2, a_col3 = st.columns([1, 3, 0.5])
        with a_col1:
            new_acr = st.text_input(
                "Acronym",
                value=acr,
                key=f"acr_key_{i}",
                label_visibility="collapsed" if i > 0 else "visible",
            )
        with a_col2:
            new_expansion = st.text_input(
                "Full Name",
                value=expansion,
                key=f"acr_val_{i}",
                label_visibility="collapsed" if i > 0 else "visible",
            )
        with a_col3:
            if i > 0:
                st.markdown("<br>", unsafe_allow_html=True)
            if st.button("\u2716", key=f"acr_del_{i}"):
                acronyms_to_remove.append(i)

        if new_acr.strip():
            updated_acronyms[new_acr.strip().upper()] = new_expansion.strip()

    if acronyms_to_remove:
        st.session_state["acronym_rows"] = [
            row for idx, row in enumerate(st.session_state["acronym_rows"])
            if idx not in acronyms_to_remove
        ]
        st.rerun()

    if st.button("Add Acronym", key="add_acronym"):
        st.session_state["acronym_rows"].append(("", ""))
        st.rerun()

    st.markdown("---")

    # Save terminology
    if st.button("Save Terminology", key="save_terminology", type="primary"):
        updated_terminology = {
            "preferred_terms": updated_terms,
            "program_names": [
                p.strip() for p in programs_text.split("\n") if p.strip()
            ],
            "acronyms": updated_acronyms,
        }
        if _save_terminology(updated_terminology):
            # Also update brand_config
            config = _load_brand_config()
            config["terminology"] = updated_terminology
            _save_brand_config(config)

            # Update session state rows to reflect saved data
            st.session_state["term_rows"] = (
                list(updated_terms.items()) if updated_terms else [("", "")]
            )
            st.session_state["acronym_rows"] = (
                list(updated_acronyms.items()) if updated_acronyms else [("", "")]
            )

            st.success("Terminology saved successfully.")


# ===================================================================
# TAB 6: Templates
# ===================================================================
with tab_templates:
    st.subheader("Templates")
    st.markdown("Upload and manage reusable document and presentation templates.")

    # --- Auto-detect templates from uploaded assets ---
    if st.button("Auto-detect Templates from Assets", key="auto_detect_templates"):
        with st.spinner("Scanning brand assets for templates..."):
            session = get_session()
            try:
                template_assets = (
                    session.query(BrandAsset)
                    .filter(BrandAsset.asset_type == "template", BrandAsset.is_active.is_(True))
                    .all()
                )
                registered = 0
                skipped = 0
                for asset in template_assets:
                    # Skip if already registered
                    existing = session.query(Template).filter(Template.file_path == asset.file_path).first()
                    if existing:
                        skipped += 1
                        continue

                    fp = Path(asset.file_path)
                    ext = fp.suffix.lower().lstrip(".")
                    description = ""

                    # Parse for metadata
                    try:
                        if ext == "pptx" and _PPTX_OK:
                            parsed = PPTXParser().parse(str(fp))
                            meta = parsed.get("metadata", {})
                            tmpl_props = parsed.get("template_properties", {})
                            slide_count = meta.get("slide_count", 0)
                            layouts = tmpl_props.get("layouts", [])
                            description = f"{slide_count} slides"
                            if layouts:
                                description += f" | Layouts: {', '.join(layouts[:5])}"
                        elif ext == "docx" and _DOCX_OK:
                            parsed = DOCXParser().parse(str(fp))
                            styles = parsed.get("styles", [])
                            description = f"Styles: {', '.join(styles[:5])}" if styles else "Word template"
                    except Exception:
                        description = f"{ext.upper()} template"

                    display_name = fp.stem.replace("_", " ").replace("-", " ")
                    tmpl = Template(
                        name=display_name,
                        template_type=ext,
                        file_path=asset.file_path,
                        description=description,
                    )
                    session.add(tmpl)
                    registered += 1

                session.commit()
            finally:
                session.close()

            if registered:
                st.success(f"Registered {registered} template(s) from assets. ({skipped} already registered)")
                st.rerun()
            elif skipped:
                st.info(f"All {skipped} template assets are already registered.")
            else:
                st.warning("No template assets found. Upload files via the Smart Drop Zone first.")

    st.markdown("---")

    # Upload section
    st.markdown("#### Upload Template")
    tmpl_col1, tmpl_col2 = st.columns([3, 1])

    with tmpl_col1:
        template_file = st.file_uploader(
            "Upload a template file",
            type=["pptx", "docx"],
            key="template_upload",
        )

    with tmpl_col2:
        template_name = st.text_input(
            "Template Name",
            placeholder="Quarterly Report Template",
            key="template_name",
        )
        template_desc = st.text_input(
            "Description",
            placeholder="Standard quarterly report layout",
            key="template_desc",
        )

    if template_file and st.button("Save Template", key="save_template", type="primary"):
        # Determine sub-directory
        suffix = Path(template_file.name).suffix.lower().lstrip(".")
        target_dir = TEMPLATES_DIR / suffix
        target_dir.mkdir(parents=True, exist_ok=True)
        dest = target_dir / template_file.name
        dest.write_bytes(template_file.getvalue())

        # Register in database
        display_name = template_name.strip() if template_name.strip() else template_file.name
        try:
            session = get_session()
            tmpl = Template(
                name=display_name,
                template_type=suffix,
                file_path=str(dest),
                description=template_desc.strip() or None,
            )
            session.add(tmpl)
            session.commit()
            session.close()
            st.success(f"Template '{display_name}' saved successfully.")
            st.rerun()
        except Exception as exc:
            st.error(f"Failed to save template: {exc}")

    st.markdown("---")

    # Template list
    st.markdown("#### Available Templates")

    try:
        session = get_session()
        templates = session.query(Template).order_by(Template.created_at.desc()).all()
        session.close()

        if templates:
            for tmpl in templates:
                with st.container():
                    tc1, tc2, tc3, tc4 = st.columns([3, 1, 1, 1])
                    with tc1:
                        st.markdown(f"**{tmpl.name}**")
                        if tmpl.description:
                            st.caption(tmpl.description)
                    with tc2:
                        st.markdown(f"`{tmpl.template_type.upper()}`")
                    with tc3:
                        st.metric("Uses", tmpl.usage_count or 0)
                    with tc4:
                        created = (
                            tmpl.created_at.strftime("%Y-%m-%d")
                            if tmpl.created_at
                            else "N/A"
                        )
                        st.caption(f"Created: {created}")
                    st.markdown("---")
        else:
            st.info(
                "No templates uploaded yet. Upload a `.pptx` or `.docx` file above "
                "to get started."
            )

    except Exception as exc:
        st.error(f"Error loading templates: {exc}")
