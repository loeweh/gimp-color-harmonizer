# GIMP 3.2 Color Harmonizer Plugin 🎨

Ein leistungsstarkes GIMP-Plugin zur **automatischen Farbanpassung, Beleuchtungskorrektur und Kantenverschmelzung**, wenn Auswahlen oder Ebenen von anderen Bildern eingefügt werden (ähnlich wie in *Facefusion*, *Roop* und professionellen Compositing-Pipelines).

---

## 📂 Speicherort

Das Plugin und alle zugehörigen Dateien befinden sich in Deinem Home-Verzeichnis unter:
```bash
/home/loewe/tarot/gimp-color-harmonizer/
```

Dateien im Ordner:
* [`color_harmonizer.py`](color_harmonizer.py): Das eigentliche GIMP 3.2 Python-Plugin.
* [`install.sh`](install.sh): Installations-Skript zur automatischen Verlinkung/Installation in GIMP 3.2.
* [`test_plugin.py`](test_plugin.py): Unit-Tests für alle 4 mathematischen Farbanpassungs-Methoden.
* [`README.md`](README.md): Diese Dokumentation.

---

## 🚀 Installation

Führe einfach im Terminal folgendes Installations-Skript aus:

```bash
cd /home/loewe/tarot/gimp-color-harmonizer
./install.sh
```

Das Skript kopiert das Plugin nach:
`~/.config/GIMP/3.2/plug-ins/color_harmonizer/color_harmonizer.py`

*(GIMP 3 benötigt für jedes Python-Plugin einen eigenen Unterordner mit ausführbarer Datei).*

---

## 🛠️ Verwendung in GIMP 3.2

1. Öffne Dein Zielbild in GIMP (z.B. Hintergrund / Szene).
2. Kopiere ein Objekt, Gesicht oder Element aus einem anderen Bild und füge es als **neue Ebene** ein (`Bearbeiten -> Einfügen als -> Neue Ebene`).
3. Positioniere die Ebene an die gewünschte Stelle.
4. Stelle sicher, dass die neu eingefügte Ebene aktiv ausgewählt ist.
5. Öffne im Menü:
   **`Farben` ➔ `Farben harmonisieren (Color Harmonizer)...`**
6. Wähle die gewünschte Methode und Stärke aus und klicke auf **OK**.

---

## 🎛️ Die 4 wählbaren Methoden im Detail

| Methode | Farbraum / Prinzip | Wann am besten geeignet? |
| :--- | :--- | :--- |
| **1. Reinhard Color Transfer** *(Standard)* | **CIELAB**-Farbraum $(\mu, \sigma)$ Skalierung | **Gesichter, Hauttöne, Personen, allgemeines Compositing.** Äußerst natürlich, vermeidet Farbübersteuerungen (Facefusion-Standard). |
| **2. Linear Covariance (MKL)** | Monge-Kantorovitch Kovarianz-Matrix | **Komplexe Beleuchtung** mit mehreren Lichtquellen oder Farbverläufen. Berücksichtigt die Korrelation zwischen Farbkanälen. |
| **3. Histogram Matching (CDF)** | Kumulative Häufigkeitsverteilung pro Kanal | **Strukturierte Texturen & detailreiche Objekte**, wenn nicht nur die Durchschnittsfarbe, sondern auch der Dynamikumfang/Kontrast exakt übertragen werden soll. |
| **4. Seamless Blending** | Reinhard + Multi-Band Laplace-/Gauß-Pyramiden | Wenn das eingefügte Objekt **weich mit dem Hintergrund verschmelzen** soll, um sichtbare Kanten und Beleuchtungssprünge nahtlos auszugleichen. |

---

## ⚙️ Optionen im Einstellungsdialog

* **Methode:** Auswahl aus den 4 oben genannten Algorithmen.
* **Stärke (0 – 100%):** Stufenloses Einblenden zwischen Original (0%) und vollständiger Farbanpassung (100%).
* **Helligkeit anpassen:** Wenn aktiviert, wird auch die Belichtung/Helligkeit angeglichen. Wenn deaktiviert, wird nur die Farbgebung (Farbton & Sättigung) geändert, während die eigene Helligkeit erhalten bleibt.
* **Referenz-Quelle:**
  * *Darunterliegende Ebene (Standard):* Verwendet automatisch die Ebene direkt unter dem eingefügten Element.
  * *Unterste Ebene (Hintergrund):* Verwendet immer die Basis-Hintergrundebene des Projekts.
