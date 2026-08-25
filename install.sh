#!/usr/bin/env bash
# ==============================================================================
# Installations-Skript für das GIMP 3.2 Color Harmonizer Plugin
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GIMP_PLUGIN_DIR="${HOME}/.config/GIMP/3.2/plug-ins/color_harmonizer"

echo "=== GIMP 3.2 Color Harmonizer Installer ==="
echo "Quellordner: ${SCRIPT_DIR}"
echo "Zielordner:  ${GIMP_PLUGIN_DIR}"

# Zielverzeichnis erstellen
mkdir -p "${GIMP_PLUGIN_DIR}"

# Plugin kopieren und ausführbar machen
cp "${SCRIPT_DIR}/color_harmonizer.py" "${GIMP_PLUGIN_DIR}/color_harmonizer.py"
chmod +x "${GIMP_PLUGIN_DIR}/color_harmonizer.py"

echo ""
echo "✅ Installation erfolgreich abgeschlossen!"
echo "Das Plugin ist installiert unter: ${GIMP_PLUGIN_DIR}/color_harmonizer.py"
echo ""
echo "In GIMP 3.2 findest Du das Plugin unter:"
echo "Menü: Farben -> Farben harmonisieren (Color Harmonizer)..."
echo "==========================================="
