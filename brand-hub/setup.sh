#!/usr/bin/env bash
# --------------------------------------------------------------------------
# Brand Intelligence Content Hub - Setup Script
#
# Creates the virtual environment, installs dependencies, scaffolds
# directories, seeds the database, and optionally starts Presenton via
# Docker Compose.
# --------------------------------------------------------------------------

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_DIR}/venv"

echo "============================================"
echo "  Brand Intelligence Content Hub - Setup"
echo "============================================"
echo ""

# ------------------------------------------------------------------
# 1. Virtual environment
# ------------------------------------------------------------------
if [ ! -d "${VENV_DIR}" ]; then
    echo "[1/6] Creating Python virtual environment..."
    python3 -m venv "${VENV_DIR}"
else
    echo "[1/6] Virtual environment already exists - skipping creation."
fi

echo "[2/6] Activating virtual environment..."
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

# ------------------------------------------------------------------
# 2. Install dependencies
# ------------------------------------------------------------------
echo "[3/6] Installing Python dependencies..."
pip install --upgrade pip -q
pip install -r "${PROJECT_DIR}/requirements.txt" -q

# ------------------------------------------------------------------
# 3. Create directory structure
# ------------------------------------------------------------------
echo "[4/6] Creating project directories..."

directories=(
    "${PROJECT_DIR}/data"
    "${PROJECT_DIR}/data/chromadb"
    "${PROJECT_DIR}/data/presenton"
    "${PROJECT_DIR}/data/uploads"
    "${PROJECT_DIR}/data/cache"
    "${PROJECT_DIR}/brand_assets"
    "${PROJECT_DIR}/brand_assets/logos"
    "${PROJECT_DIR}/brand_assets/fonts"
    "${PROJECT_DIR}/brand_assets/templates"
    "${PROJECT_DIR}/output"
    "${PROJECT_DIR}/output/presentations"
    "${PROJECT_DIR}/output/infographics"
    "${PROJECT_DIR}/output/translations"
    "${PROJECT_DIR}/output/reports"
)

for dir in "${directories[@]}"; do
    mkdir -p "${dir}"
done

# ------------------------------------------------------------------
# 4. Seed .env from example if needed
# ------------------------------------------------------------------
if [ ! -f "${PROJECT_DIR}/.env" ]; then
    echo "[5/6] Copying .env.example to .env - please fill in your API keys."
    cp "${PROJECT_DIR}/.env.example" "${PROJECT_DIR}/.env"
else
    echo "[5/6] .env already exists - skipping copy."
fi

# ------------------------------------------------------------------
# 5. Initialize the database
# ------------------------------------------------------------------
echo "[6/6] Initializing SQLite database..."
(cd "${PROJECT_DIR}" && python -c "from app.database.models import init_db; init_db()")

# ------------------------------------------------------------------
# 6. Optionally start Presenton via Docker
# ------------------------------------------------------------------
if command -v docker &>/dev/null; then
    echo ""
    echo "Docker detected. Starting Presenton container..."
    if command -v docker-compose &>/dev/null; then
        docker-compose -f "${PROJECT_DIR}/docker-compose.yml" up -d
    elif docker compose version &>/dev/null 2>&1; then
        docker compose -f "${PROJECT_DIR}/docker-compose.yml" up -d
    else
        echo "  WARNING: docker-compose / docker compose not found. Start Presenton manually."
    fi
else
    echo ""
    echo "Docker not found - skipping Presenton container startup."
    echo "Install Docker and run 'docker compose up -d' to start Presenton later."
fi

# ------------------------------------------------------------------
# Done
# ------------------------------------------------------------------
echo ""
echo "============================================"
echo "  Setup complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your API keys (ANTHROPIC_API_KEY, NAPKIN_API_TOKEN, etc.)"
echo "  2. Activate the virtual environment:  source venv/bin/activate"
echo "  3. Run the app:                       streamlit run app/main.py"
echo ""
