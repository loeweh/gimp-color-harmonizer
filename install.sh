#!/usr/bin/env bash
# ==============================================================================
# Installations-Skript für das GIMP 3 Color Harmonizer Plugin
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== GIMP 3.x Color Harmonizer Installer ==="
echo "Quellordner: ${SCRIPT_DIR}"

TARGET_DIRS=(
    "${HOME}/.config/GIMP/3.2/plug-ins/color_harmonizer"
    "${HOME}/.config/GIMP/3.2/plug-ins/color-harmonizer"
    "${HOME}/.config/GIMP/3.0/plug-ins/color_harmonizer"
    "${HOME}/.config/GIMP/3.0/plug-ins/color-harmonizer"
)

for DIR in "${TARGET_DIRS[@]}"; do
    mkdir -p "${DIR}"
    cp "${SCRIPT_DIR}/color_harmonizer.py" "${DIR}/color_harmonizer.py"
    cp "${SCRIPT_DIR}/color_harmonizer.py" "${DIR}/color-harmonizer.py"
    chmod +x "${DIR}/color_harmonizer.py" "${DIR}/color-harmonizer.py"
    echo "  -> Installiert in: ${DIR}"
done

echo ""
echo "✅ Installation erfolgreich abgeschlossen!"
echo ""
echo "WICHTIG:"
echo "1. Falls GIMP bereits geöffnet ist: Bitte GIMP KOMPLETT SCHLIESSEN und NEU STARTEN."
echo "2. Das Plugin findest Du dann im Menü unter:"
echo "   Colors -> Farben harmonisieren (Color Harmonizer)..."
echo "==========================================="
