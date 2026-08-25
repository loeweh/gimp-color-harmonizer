# GIMP 3.2 Color Harmonizer Plugin 🎨

A powerful GIMP 3.x plugin for **automatic color transfer, lighting harmonization, and seamless edge blending** when pasting elements, faces, or objects from other images (Facefusion / Roop / professional compositing style).

---

## 🚀 Quick Start & Installation

Clone the repository and run the installer script:

```bash
git clone https://github.com/loeweh/gimp-color-harmonizer.git
cd gimp-color-harmonizer
./install.sh
```

The script automatically copies the plugin to your GIMP 3.2 plug-ins directory:
`~/.config/GIMP/3.2/plug-ins/color_harmonizer/color_harmonizer.py`

*(Note: GIMP 3 requires each Python plugin to reside in its own folder with executable permissions).*

---

## 🛠️ How to Use in GIMP 3.2

1. Open your target image or background in GIMP.
2. Copy an element, person, or face from another image and paste it as a **new layer** (`Edit -> Paste As -> New Layer`).
3. Position the layer where you want it.
4. Ensure the newly pasted layer is selected/active in the layer stack.
5. In the top menu, go to:
   **`Colors` ➔ `Farben harmonisieren (Color Harmonizer)...`**
6. Choose your preferred algorithm, adjust the strength slider, and click **OK**.

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

* **Method:** Choose between the 4 color transfer and harmonization algorithms.
* **Strength (0 – 100%):** Smooth slider to blend between original colors (0%) and fully matched colors (100%).
* **Match Luminance:** When enabled, brightness and contrast are matched as well. When disabled, only color tint/hue/chrominance is transferred while preserving original brightness.
* **Reference Source:**
  * *Layer Below (Default):* Automatically samples colors from the layer directly underneath the active layer.
  * *Bottom Layer (Background):* Samples colors from the bottom-most background layer of the project.

---

## 📦 Requirements

* **GIMP 3.0 / 3.2+** (with Python 3 support)
* **NumPy** (standard in Python environments)

---

## 🧪 Testing

To run the built-in algorithm test suite:

```bash
python3 test_plugin.py
```

---

## 📄 License

MIT License. Free to use and modify for personal and commercial projects.
