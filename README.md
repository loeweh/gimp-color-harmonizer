# GIMP 3.2 Color Harmonizer Plugin 🎨

A powerful GIMP 3.x plugin for **automatic color transfer, lighting harmonization, facial feature protection, and seamless edge blending** when pasting elements, faces, or objects from other images (Facefusion / Roop / professional compositing style).

---

## 🚀 Quick Start & Installation

Clone the repository and run the installer script:

```bash
git clone https://github.com/loeweh/gimp-color-harmonizer.git
cd gimp-color-harmonizer
./install.sh
```

The script copies the plugin to your GIMP 3.2 plug-ins directory:
`~/.config/GIMP/3.2/plug-ins/color_harmonizer/color_harmonizer.py`

---

## 🛠️ How to Use in GIMP 3.2

1. Open your target image or background in GIMP.
2. Copy an element, person, or face from another image and paste it as a **new layer** (`Edit -> Paste As -> New Layer`).
3. Position the layer where you want it.
4. Ensure the newly pasted layer is selected in the layer stack.
5. In the top menu, go to:
   **`Colors` ➔ `Farben harmonisieren (Color Harmonizer)...`**
6. Adjust the sliders with the **Live Preview**, pick a target color with the **Pipette**, and click **OK**.

---

## ✨ Features & Highlights

### 🔍 Live Preview (Echtzeit-Vorschau)
* Interactive zoomable preview rendered directly inside the dialog.
* Immediately reflects adjustments to the algorithm, sliders, shading, and white protection.

### 🧪 Pipette (Eyedropper Color Picker)
* In addition to automatic layer overlap and Lasso selections, you can select **`Pipette / Manuelle Farbe`** in the `Referenz-Quelle` dropdown.
* Click the color button, select the **Pipette (Eyedropper tool)**, and click anywhere on the canvas (e.g. cheek, forehead, background light) to pick the exact target skin tone.

### 👁️ Eye White, Teeth & Highlight Protection (Sclera Protection)
* In CIELAB color space, eye whites, teeth, and specular glints exhibit high luminance combined with very low chromaticity ($C \le 16$).
* The plugin automatically detects these areas and preserves their clean, neutral white tones to prevent discolored eyes or yellowed teeth.
* **Control:** `Augenweiß- und Glanzlichtschutz (%)` (0% to 100%, default 100%).

### 💡 Spatial Shading Transfer (Directional Lighting Harmonization)
* Solves the mismatch when the copied face was lit from the left, but the background scene is lit from the right.
* Uses frequency separation to isolate the low-frequency lighting gradient of the background and transfers that directional shading onto the pasted element without destroying skin pores or facial details.
* **Control:** `Lichtgradient übertragen / Shading (%)` (0% to 100%, default 50%).

---

## 🎛️ The 4 Selectable Algorithms

| Method | Principle & Color Space | Best Use Case |
| :--- | :--- | :--- |
| **1. Reinhard Color Transfer** *(Default)* | **CIELAB** $(\mu, \sigma)$ mean & standard deviation matching | **Faces, skin tones, portraits, and general photo compositing.** Extremely natural, avoids over-saturation (Facefusion standard). |
| **2. Linear Covariance (MKL)** | Monge-Kantorovitch linear covariance matrix transfer | **Complex lighting conditions** with multiple light sources or cross-channel color casts. |
| **3. Histogram Matching (CDF)** | Cumulative distribution function matching per channel | **Textured surfaces & detailed objects** where both color tone and local tonal contrast need to match. |
| **4. Seamless Blending** | Reinhard LAB + Multi-Band Laplacian/Gaussian Pyramids | When the pasted object needs to **smoothly blend into the background** without harsh cut-out edges or lighting seams. |

---

## ⚙️ Plugin Options

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| **Methode** | Dropdown | *Reinhard* | Core color matching algorithm |
| **Stärke (%)** | Slider (0–100) | `100 %` | Overall intensity of the color adjustment |
| **Augenweiß- und Glanzlichtschutz (%)** | Slider (0–100) | `100 %` | Prevents sclera, teeth, and glints from discoloring |
| **Lichtgradient übertragen / Shading (%)** | Slider (0–100) | `50 %` | Transmits background lighting direction & shadows |
| **Globale Helligkeit anpassen** | Checkbox | `Enabled` | Matches overall exposure (disable for hue-only tinting) |
| **Referenz-Quelle** | Dropdown | *Layer Below* | `Darunterliegende Ebene`, `Unterste Ebene`, or `Pipette / Manuelle Farbe` |
| **Pipetten-Farbe** | Color Picker | *Skin Tone* | Color button with pipette tool for manual color picking |

---

## 📦 Requirements

* **GIMP 3.0 / 3.2+** (with Python 3 support)
* **NumPy**

---

## 🧪 Testing

Run the test suite:

```bash
python3 test_plugin.py
```

---

## 📄 License

MIT License. Free to use and modify for personal and commercial projects.
