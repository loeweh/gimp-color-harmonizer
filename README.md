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
5. *(Optional targeted color sample)*: If you want to sample from a specific skin region (e.g. cheek/forehead on the background), make a quick selection with the **Lasso or Ellipse tool** before running the plugin!
6. In the top menu, go to:
   **`Colors` ➔ `Farben harmonisieren (Color Harmonizer)...`**
7. Adjust the sliders to your liking and click **OK**.

---

## ✨ Advanced Features & Protections

### 👁️ Eye White, Teeth & Highlight Protection (Sclera Protection)
Standard color transfer algorithms tend to shift the entire layer into the target color, often leaving eye sclera and teeth with an unnatural yellow or reddish tint.
* **How it works:** In CIELAB color space, eye whites, teeth, and specular glints exhibit high luminance combined with very low chromaticity ($C \le 16$). The plugin automatically detects these areas and preserves their clean, neutral white tones.
* **Control:** `Augenweiß & Glanzlichter schützen (%)` (0% to 100%, default 100%).

### 💡 Spatial Shading Transfer (Directional Lighting Harmonization)
Solves the mismatch when the copied face was lit from the left, but the background scene is lit from the right.
* **How it works:** Uses frequency separation to isolate the broad, low-frequency lighting gradient of the target background and transfers that light direction onto the pasted element without destroying skin pores or facial details.
* **Control:** `Lichtgradient übertragen / Shading (%)` (0% to 100%, default 50%).

### 🎯 Automatic Overlap & Custom Selection Sampling
* **Automatic Mode (No selection):** Restricts the background color sampling to the exact spatial silhouette directly underneath the non-transparent cutout.
* **Targeted Selection Mode:** If an active selection exists on the canvas (Lasso / Ellipse), colors are sampled specifically from within that selection.

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
| **Augenweiß & Glanzlichter schützen (%)** | Slider (0–100) | `100 %` | Prevents sclera, teeth, and glints from discoloring |
| **Lichtgradient übertragen / Shading (%)** | Slider (0–100) | `50 %` | Transmits background lighting direction & shadows |
| **Globale Helligkeit anpassen** | Checkbox | `Enabled` | Matches overall exposure (disable for hue-only tinting) |
| **Referenz-Quelle** | Dropdown | *Layer Below* | Source layer for color sampling (or uses active selection) |

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
