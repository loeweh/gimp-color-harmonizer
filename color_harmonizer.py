#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Color Harmonizer GIMP 3 Plugin
==============================
Passt Farben, Beleuchtungsrichtung und Kantenübergänge einer eingefügten Ebene / Auswahl
an das Zielbild oder eine Referenzebene an (Facefusion / Compositing Style).

Erweiterte Features:
- 4 Farbanpassungs-Algorithmen (Reinhard LAB, MKL Covariance, Histogram Matching, Seamless Multi-Band)
- Schutz vor Verfärbung von Augenweiß, Zähnen und Glanzlichtern (Sclera & Highlight Protection)
- Räumlicher Lichtgradienten-Transfer (Shading Transfer für unterschiedliche Lichtrichtungen)
- Automatische Überlappungs-Erkennung oder gezielte Pipetten-Referenz via Auswahl (Lasso/Ellipse)
"""

import sys
import os
import time
import numpy as np

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
gi.require_version('Babl', '0.1')
from gi.repository import Babl
from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Gio

def _(message):
    return GLib.dgettext(None, message)


# ============================================================================
# 1. FARBRAUM-KONVERTIERUNG (sRGB <-> CIELAB) in reinem NumPy
# ============================================================================

def srgb_to_linear(rgb):
    """Konvertiert sRGB [0..1] zu linearem RGB."""
    mask = rgb > 0.04045
    return np.where(mask, ((rgb + 0.055) / 1.055) ** 2.4, rgb / 12.92)

def linear_to_srgb(rgb_lin):
    """Konvertiert lineares RGB zu sRGB [0..1]."""
    mask = rgb_lin > 0.0031308
    srgb = np.where(mask, 1.055 * (np.maximum(rgb_lin, 0.0) ** (1.0 / 2.4)) - 0.055, 12.92 * rgb_lin)
    return np.clip(srgb, 0.0, 1.0)

def rgb_to_lab(rgb):
    """Konvertiert sRGB [0..1] zu CIELAB (L: 0..100, a: -128..127, b: -128..127)."""
    rgb_lin = srgb_to_linear(rgb)
    M = np.array([
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041]
    ], dtype=np.float32)
    xyz = np.dot(rgb_lin, M.T)
    
    xyz_ref = np.array([0.95047, 1.00000, 1.08883], dtype=np.float32)
    xyz_norm = xyz / xyz_ref
    
    delta = 6.0 / 29.0
    mask_xyz = xyz_norm > (delta ** 3)
    f_xyz = np.where(mask_xyz, np.maximum(xyz_norm, 1e-10) ** (1.0 / 3.0), (xyz_norm / (3.0 * delta ** 2)) + (4.0 / 29.0))
    
    L = 116.0 * f_xyz[..., 1] - 16.0
    a = 500.0 * (f_xyz[..., 0] - f_xyz[..., 1])
    b = 200.0 * (f_xyz[..., 1] - f_xyz[..., 2])
    return np.stack([L, a, b], axis=-1)

def lab_to_rgb(lab):
    """Konvertiert CIELAB zu sRGB [0..1]."""
    L = lab[..., 0]
    a = lab[..., 1]
    b = lab[..., 2]
    
    fy = (L + 16.0) / 116.0
    fx = (a / 500.0) + fy
    fz = fy - (b / 200.0)
    
    delta = 6.0 / 29.0
    x = np.where(fx > delta, fx ** 3, 3.0 * (delta ** 2) * (fx - 4.0 / 29.0))
    y = np.where(fy > delta, fy ** 3, 3.0 * (delta ** 2) * (fy - 4.0 / 29.0))
    z = np.where(fz > delta, fz ** 3, 3.0 * (delta ** 2) * (fz - 4.0 / 29.0))
    
    xyz_ref = np.array([0.95047, 1.00000, 1.08883], dtype=np.float32)
    xyz = np.stack([x, y, z], axis=-1) * xyz_ref
    
    M_inv = np.array([
        [ 3.2404542, -1.5371385, -0.4985314],
        [-0.9692660,  1.8760108,  0.0415560],
        [ 0.0556434, -0.2040259,  1.0572252]
    ], dtype=np.float32)
    rgb_lin = np.dot(xyz, M_inv.T)
    return linear_to_srgb(rgb_lin)


# ============================================================================
# 2. HILFSFUNKTIONEN (FILTER, SCHUTZMASKEN & SHADING)
# ============================================================================

def fast_gaussian_blur(img, radius=4, passes=3):
    """Schneller Multi-Pass Box-Blur zur Gauß-Approximation in reinem NumPy."""
    if radius <= 0:
        return img
    kernel_size = 2 * radius + 1
    out = img.astype(np.float32)
    is_3d = (out.ndim == 3)
    
    for _ in range(passes):
        # Horizontal
        pad_shape = ((0, 0), (radius + 1, radius), (0, 0)) if is_3d else ((0, 0), (radius + 1, radius))
        padded = np.pad(out, pad_shape, mode='edge')
        cs = np.cumsum(padded, axis=1)
        out = (cs[:, kernel_size:] - cs[:, :-kernel_size]) / kernel_size
            
        # Vertikal
        pad_shape = ((radius + 1, radius), (0, 0), (0, 0)) if is_3d else ((radius + 1, radius), (0, 0))
        padded = np.pad(out, pad_shape, mode='edge')
        cs = np.cumsum(padded, axis=0)
        out = (cs[kernel_size:, :] - cs[:-kernel_size, :]) / kernel_size
            
    return out


def compute_whites_protection_mask(src_rgb):
    """
    Erkennt Augenweiß (Sclera), Zähne und helle Glanzlichter im CIELAB-Farbraum.
    Gibt eine weiche Schutzmaske [0..1] zurück:
    1.0 = Schützen (Originalfarbe erhalten)
    0.0 = Vollständige Farbanpassung
    """
    src_lab = rgb_to_lab(src_rgb)
    L = src_lab[..., 0]
    a = src_lab[..., 1]
    b = src_lab[..., 2]
    chroma = np.sqrt(a**2 + b**2)
    
    # 1. Glanzlichter (sehr helle Spitzlichter/Reflexionen)
    specular = np.clip((L - 85.0) / 10.0, 0.0, 1.0)
    
    # 2. Augenweiß & Zähne (hohe Helligkeit L >= 55 bei geringer Sättigung Chroma <= 16)
    lum_factor = np.clip((L - 55.0) / 15.0, 0.0, 1.0)
    neutral_factor = np.clip((16.0 - chroma) / 10.0, 0.0, 1.0)
    sclera = lum_factor * neutral_factor
    
    return np.clip(np.maximum(specular, sclera), 0.0, 1.0)


def apply_shading_transfer(adjusted_rgb, ref_bg_crop, shading_strength=0.5):
    """
    Überträgt den räumlichen Hell-Dunkel-Verlauf (Lichtrichtung) des Hintergrunds
    auf das eingefügte Element via Frequenz-Separation.
    """
    if shading_strength <= 0.0 or ref_bg_crop is None or ref_bg_crop.shape != adjusted_rgb.shape:
        return adjusted_rgb
        
    src_lab = rgb_to_lab(adjusted_rgb)
    ref_lab = rgb_to_lab(ref_bg_crop)
    
    h, w = adjusted_rgb.shape[:2]
    blur_rad = max(4, min(h, w) // 8)
    
    # Großflächige Beleuchtung von Quelle und Hintergrund isolieren
    low_src_l = fast_gaussian_blur(src_lab[..., 0], radius=blur_rad, passes=2)
    low_ref_l = fast_gaussian_blur(ref_lab[..., 0], radius=blur_rad, passes=2)
    
    # Beleuchtungsdifferenz berechnen und auf die Helligkeitskarte addieren
    delta_l = (low_ref_l - low_src_l) * shading_strength
    src_lab[..., 0] = np.clip(src_lab[..., 0] + delta_l, 0.0, 100.0)
    
    return lab_to_rgb(src_lab)


# ============================================================================
# 3. FARBANPASSUNGS-METHODEN (ALGORITHMEN)
# ============================================================================

def apply_reinhard(src_rgb, src_samples, ref_samples, match_luminance=True):
    """1. Reinhard Color Transfer (CIELAB)"""
    src_lab_samples = rgb_to_lab(src_samples)
    ref_lab_samples = rgb_to_lab(ref_samples)
    
    mu_s = np.mean(src_lab_samples, axis=0)
    sigma_s = np.std(src_lab_samples, axis=0) + 1e-5
    
    mu_r = np.mean(ref_lab_samples, axis=0)
    sigma_r = np.std(ref_lab_samples, axis=0) + 1e-5
    
    src_lab = rgb_to_lab(src_rgb)
    out_lab = np.zeros_like(src_lab)
    
    if match_luminance:
        out_lab[..., 0] = ((src_lab[..., 0] - mu_s[0]) / sigma_s[0]) * sigma_r[0] + mu_r[0]
    else:
        out_lab[..., 0] = src_lab[..., 0]
        
    out_lab[..., 1] = ((src_lab[..., 1] - mu_s[1]) / sigma_s[1]) * sigma_r[1] + mu_r[1]
    out_lab[..., 2] = ((src_lab[..., 2] - mu_s[2]) / sigma_s[2]) * sigma_r[2] + mu_r[2]
    
    out_lab[..., 0] = np.clip(out_lab[..., 0], 0.0, 100.0)
    return lab_to_rgb(out_lab)


def apply_mkl(src_rgb, src_samples, ref_samples):
    """2. Monge-Kantorovitch Linear (MKL) / Kovarianz-Anpassung"""
    X_s = src_samples.reshape(-1, 3).astype(np.float64)
    X_r = ref_samples.reshape(-1, 3).astype(np.float64)
    
    mu_s = np.mean(X_s, axis=0)
    mu_r = np.mean(X_r, axis=0)
    
    cov_s = np.cov(X_s, rowvar=False) + 1e-5 * np.eye(3)
    cov_r = np.cov(X_r, rowvar=False) + 1e-5 * np.eye(3)
    
    w_s, v_s = np.linalg.eigh(cov_s)
    w_s = np.maximum(w_s, 1e-6)
    cov_s_sqrt = v_s @ np.diag(np.sqrt(w_s)) @ v_s.T
    cov_s_inv_sqrt = v_s @ np.diag(1.0 / np.sqrt(w_s)) @ v_s.T
    
    inner = cov_s_sqrt @ cov_r @ cov_s_sqrt
    w_i, v_i = np.linalg.eigh(inner)
    w_i = np.maximum(w_i, 1e-6)
    inner_sqrt = v_i @ np.diag(np.sqrt(w_i)) @ v_i.T
    
    T = cov_s_inv_sqrt @ inner_sqrt @ cov_s_inv_sqrt
    
    orig_shape = src_rgb.shape
    X_src_all = src_rgb.reshape(-1, 3).astype(np.float64)
    X_out = (X_src_all - mu_s) @ T + mu_r
    return np.clip(X_out.reshape(orig_shape).astype(np.float32), 0.0, 1.0)


def apply_histogram(src_rgb, src_samples, ref_samples, match_luminance=True):
    """3. Histogram Matching (CDF)"""
    src_lab_samples = rgb_to_lab(src_samples)
    ref_lab_samples = rgb_to_lab(ref_samples)
    
    src_lab = rgb_to_lab(src_rgb)
    out_lab = np.zeros_like(src_lab)
    
    for c in range(3):
        if c == 0 and not match_luminance:
            out_lab[..., 0] = src_lab[..., 0]
            continue
            
        s_sample_chan = src_lab_samples[..., c].flatten()
        r_sample_chan = ref_lab_samples[..., c].flatten()
        
        r_sorted = np.sort(r_sample_chan)
        r_quantiles = np.linspace(0.0, 1.0, len(r_sorted))
        
        s_chan_full = src_lab[..., c]
        flat_s = s_chan_full.flatten()
        
        hist_s, bin_edges = np.histogram(s_sample_chan, bins=256)
        cdf_s = np.cumsum(hist_s).astype(np.float64)
        cdf_s /= (cdf_s[-1] + 1e-10)
        
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0
        ranks = np.interp(flat_s, bin_centers, cdf_s, left=0.0, right=1.0)
        mapped = np.interp(ranks, r_quantiles, r_sorted)
        out_lab[..., c] = mapped.reshape(s_chan_full.shape)
        
    out_lab[..., 0] = np.clip(out_lab[..., 0], 0.0, 100.0)
    return lab_to_rgb(out_lab)


def apply_seamless(src_rgb, src_alpha, ref_bg_crop, src_samples, ref_samples, match_luminance=True):
    """4. Seamless Blending (Multi-Band / Laplace Hybrid)"""
    harmonized = apply_reinhard(src_rgb, src_samples, ref_samples, match_luminance)
    
    if ref_bg_crop is not None and ref_bg_crop.shape == src_rgb.shape:
        smooth_alpha = fast_gaussian_blur(src_alpha, radius=3, passes=2)
        smooth_alpha = np.clip(smooth_alpha[..., None], 0.0, 1.0)
        
        low_src = fast_gaussian_blur(harmonized, radius=8, passes=2)
        low_bg = fast_gaussian_blur(ref_bg_crop, radius=8, passes=2)
        high_src = harmonized - low_src
        
        blended_low = low_src * smooth_alpha + low_bg * (1.0 - smooth_alpha)
        return np.clip(blended_low + high_src, 0.0, 1.0)
    
    return harmonized


# ============================================================================
# 4. GIMP 3 PLUGIN AUSFÜHRUNG
# ============================================================================

def color_harmonizer_run(procedure, run_mode, image, drawables, config, data):
    if len(drawables) == 0:
        msg = _("Keine Ebene ausgewählt.")
        error = GLib.Error.new_literal(Gimp.PlugIn.error_quark(), msg, 0)
        return procedure.new_return_values(Gimp.PDBStatusType.CALLING_ERROR, error)

    # Interaktiver Dialog
    if run_mode == Gimp.RunMode.INTERACTIVE:
        GimpUi.init('python-fu-color-harmonizer')
        dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
        dialog.fill(None)
        if not dialog.run():
            dialog.destroy()
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
        dialog.destroy()

    method = config.get_property('method')
    strength = config.get_property('strength') / 100.0
    protect_whites = config.get_property('protect_whites') / 100.0
    shading_transfer = config.get_property('shading_transfer') / 100.0
    match_luminance = config.get_property('match_luminance')
    ref_mode = config.get_property('ref_mode')

    Gimp.context_push()
    image.undo_group_start()

    all_layers = image.get_layers()

    # Prüfen, ob eine gezielte Auswahl (Pipette/Lasso) im Bild aktiv ist
    has_selection = not Gimp.Selection.is_empty(image)

    for drawable in drawables:
        if not isinstance(drawable, Gimp.Layer):
            continue

        # 1. Referenz-Ebene ermitteln
        ref_layer = None
        if ref_mode == 'background' and len(all_layers) > 1:
            ref_layer = all_layers[-1]
            if ref_layer == drawable:
                ref_layer = all_layers[0] if len(all_layers) > 1 else None
        else:
            try:
                cur_idx = all_layers.index(drawable)
                if cur_idx + 1 < len(all_layers):
                    ref_layer = all_layers[cur_idx + 1]
                elif cur_idx > 0:
                    ref_layer = all_layers[cur_idx - 1]
            except ValueError:
                if len(all_layers) > 1:
                    ref_layer = all_layers[-1]

        if ref_layer is None:
            ref_layer = drawable

        # 2. Pixel der Quelle auslesen
        s_w = drawable.get_width()
        s_h = drawable.get_height()
        s_ok, s_ox, s_oy = drawable.get_offsets()
        
        s_buf = drawable.get_buffer()
        s_rect = Gegl.Rectangle.new(0, 0, s_w, s_h)
        s_bytes = s_buf.get(s_rect, 1.0, "R'G'B'A u8", Gegl.AbyssPolicy.NONE)
        s_arr = np.frombuffer(s_bytes, dtype=np.uint8).reshape((s_h, s_w, 4)).copy()

        s_rgb = s_arr[..., :3].astype(np.float32) / 255.0
        s_alpha = s_arr[..., 3].astype(np.float32) / 255.0

        # Sichtbare Quellpixel
        valid_src = (s_alpha > 0.05)
        if np.sum(valid_src) < 10:
            valid_src = np.ones((s_h, s_w), dtype=bool)
        src_samples = s_rgb[valid_src]

        # 3. Referenzpixel ermitteln (mit Auswahl ODER räumlicher Schnittmenge)
        r_w = ref_layer.get_width()
        r_h = ref_layer.get_height()
        r_ok, r_ox, r_oy = ref_layer.get_offsets()
        r_buf = ref_layer.get_buffer()

        ref_samples = None
        ref_crop = np.zeros((s_h, s_w, 3), dtype=np.float32)

        # Schnittmenge beider Ebenen für Hintergrund-Crop und Shading berechnen
        inter_x1 = max(s_ox, r_ox)
        inter_y1 = max(s_oy, r_oy)
        inter_x2 = min(s_ox + s_w, r_ox + r_w)
        inter_y2 = min(s_oy + s_h, r_oy + r_h)

        if inter_x2 > inter_x1 and inter_y2 > inter_y1:
            sx_start = inter_x1 - s_ox
            sy_start = inter_y1 - s_oy
            sx_end = inter_x2 - s_ox
            sy_end = inter_y2 - s_oy
            
            rx_start = inter_x1 - r_ox
            ry_start = inter_y1 - r_oy
            rw_inter = inter_x2 - inter_x1
            rh_inter = inter_y2 - inter_y1

            r_sub_rect = Gegl.Rectangle.new(rx_start, ry_start, rw_inter, rh_inter)
            r_sub_bytes = r_buf.get(r_sub_rect, 1.0, "R'G'B'A u8", Gegl.AbyssPolicy.NONE)
            r_sub_arr = np.frombuffer(r_sub_bytes, dtype=np.uint8).reshape((rh_inter, rw_inter, 4))
            
            r_sub_rgb = r_sub_arr[..., :3].astype(np.float32) / 255.0
            r_sub_alpha = r_sub_arr[..., 3].astype(np.float32) / 255.0
            s_sub_alpha = s_alpha[sy_start:sy_end, sx_start:sx_end]

            # Hintergrund-Crop für Shading Transfer und Seamless Blending
            ref_crop[sy_start:sy_end, sx_start:sx_end] = r_sub_rgb

            # Falls KEINE aktive Auswahl da ist: Schnittmenge nutzen
            if not has_selection:
                valid_overlap = (s_sub_alpha > 0.05) & (r_sub_alpha > 0.05)
                if np.sum(valid_overlap) >= 10:
                    ref_samples = r_sub_rgb[valid_overlap]

        # FALL A: Gezielte Farbauswahl (Auswahl im Bild aktiv)
        if has_selection and ref_samples is None:
            succ, non_empty, bx1, by1, bx2, by2 = Gimp.Selection.bounds(image)
            if non_empty:
                # Schnittmenge Auswahl mit Referenzebene
                sel_x1 = max(bx1, r_ox)
                sel_y1 = max(by1, r_oy)
                sel_x2 = min(bx2, r_ox + r_w)
                sel_y2 = min(by2, r_oy + r_h)
                
                if sel_x2 > sel_x1 and sel_y2 > sel_y1:
                    sel_rx = sel_x1 - r_ox
                    sel_ry = sel_y1 - r_oy
                    sel_rw = sel_x2 - sel_x1
                    sel_rh = sel_y2 - sel_y1
                    
                    sel_rect = Gegl.Rectangle.new(sel_rx, sel_ry, sel_rw, sel_rh)
                    sel_bytes = r_buf.get(sel_rect, 1.0, "R'G'B'A u8", Gegl.AbyssPolicy.NONE)
                    sel_arr = np.frombuffer(sel_bytes, dtype=np.uint8).reshape((sel_rh, sel_rw, 4))
                    
                    sel_rgb = sel_arr[..., :3].astype(np.float32) / 255.0
                    sel_alpha = sel_arr[..., 3].astype(np.float32) / 255.0
                    valid_sel = (sel_alpha > 0.05)
                    if np.sum(valid_sel) >= 10:
                        ref_samples = sel_rgb[valid_sel]

        # FALL B: Fallback (ganze Referenzebene)
        if ref_samples is None:
            r_rect = Gegl.Rectangle.new(0, 0, r_w, r_h)
            r_bytes = r_buf.get(r_rect, 1.0, "R'G'B'A u8", Gegl.AbyssPolicy.NONE)
            r_arr = np.frombuffer(r_bytes, dtype=np.uint8).reshape((r_h, r_w, 4))
            r_rgb_full = r_arr[..., :3].astype(np.float32) / 255.0
            r_alpha_full = r_arr[..., 3].astype(np.float32) / 255.0
            valid_ref = (r_alpha_full > 0.05)
            if np.sum(valid_ref) < 10:
                valid_ref = np.ones((r_h, r_w), dtype=bool)
            ref_samples = r_rgb_full[valid_ref]

        # 4. Gewählte Basismethode anwenden
        if method == 'reinhard':
            base_out_rgb = apply_reinhard(s_rgb, src_samples, ref_samples, match_luminance)
        elif method == 'mkl':
            base_out_rgb = apply_mkl(s_rgb, src_samples, ref_samples)
        elif method == 'histogram':
            base_out_rgb = apply_histogram(s_rgb, src_samples, ref_samples, match_luminance)
        elif method == 'seamless':
            base_out_rgb = apply_seamless(s_rgb, s_alpha, ref_crop, src_samples, ref_samples, match_luminance)
        else:
            base_out_rgb = apply_reinhard(s_rgb, src_samples, ref_samples, match_luminance)

        # 5. Räumlichen Lichtgradienten übertragen (Shading Transfer)
        if shading_transfer > 0.0:
            base_out_rgb = apply_shading_transfer(base_out_rgb, ref_crop, shading_strength=shading_transfer)

        # 6. Schutz für Augenweiß, Zähne & Glanzlichter anwenden
        if protect_whites > 0.0:
            p_mask = compute_whites_protection_mask(s_rgb) * protect_whites
            base_out_rgb = base_out_rgb * (1.0 - p_mask[..., None]) + s_rgb * p_mask[..., None]

        # 7. Gesamtstärke stufenlos einblenden
        final_rgb = np.clip((1.0 - strength) * s_rgb + strength * base_out_rgb, 0.0, 1.0)

        # 8. In Shadow-Buffer schreiben
        s_arr[..., :3] = np.clip(np.round(final_rgb * 255.0), 0, 255).astype(np.uint8)

        shadow = drawable.get_shadow_buffer()
        shadow.set(s_rect, "R'G'B'A u8", s_arr.tobytes())
        shadow.flush()

        drawable.merge_shadow(True)
        drawable.update(0, 0, s_w, s_h)

    Gimp.displays_flush()
    image.undo_group_end()
    Gimp.context_pop()

    return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


# ============================================================================
# 5. GIMP 3 PLUGIN REGISTRIERUNG & UI DEFINITION
# ============================================================================

class ColorHarmonizerPlugin(Gimp.PlugIn):
    def do_set_i18n(self, procname):
        return True, 'gimp30-python', None

    def do_query_procedures(self):
        return ['python-fu-color-harmonizer']

    def do_create_procedure(self, name):
        Gegl.init(None)

        procedure = Gimp.ImageProcedure.new(
            self,
            name,
            Gimp.PDBProcType.PLUGIN,
            color_harmonizer_run,
            None
        )

        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask(
            Gimp.ProcedureSensitivityMask.DRAWABLE |
            Gimp.ProcedureSensitivityMask.DRAWABLES
        )

        procedure.set_documentation(
            _("Farben von Ebenen und Auswahlen harmonisieren"),
            _("Passt Farben, Kontrast, Lichtrichtung und Kanten einer Ebene an den Hintergrund an (Facefusion / Compositing Style)."),
            name
        )
        procedure.set_menu_label(_("Farben harmonisieren (Color Harmonizer)..."))
        procedure.set_attribution("Antigravity", "Antigravity", "2026")
        procedure.add_menu_path("<Image>/Colors/")

        # 1. Methode (Dropdown)
        choice_method = Gimp.Choice.new()
        choice_method.add("reinhard", 0, _("1. Reinhard (LAB - Natürlich / Hauttöne)"), _("Passt Mittelwert und Varianz im CIELAB-Farbraum an. Sehr natürlich."))
        choice_method.add("mkl", 1, _("2. Linear Covariance (MKL)"), _("Monge-Kantorovitch Kovarianzmatrix-Anpassung."))
        choice_method.add("histogram", 2, _("3. Histogram Matching (CDF)"), _("Gleicht die kumulierte Tonwertkurve pro Farbkanal an."))
        choice_method.add("seamless", 3, _("4. Seamless Blending (Multi-Band / Laplace)"), _("Farbanpassung + weiche Gradienten-Verschmelzung der Ränder."))

        procedure.add_choice_argument(
            "method",
            _("Methode"),
            _("Farbangleichungs-Algorithmus"),
            choice_method,
            "reinhard",
            GObject.ParamFlags.READWRITE
        )

        # 2. Gesamtstärke (Schieberegler 0..100)
        procedure.add_double_argument(
            "strength",
            _("Stärke (%)"),
            _("Gesamtstärke der Farbanpassung von 0% (Original) bis 100% (Vollständig)"),
            0.0, 100.0, 100.0,
            GObject.ParamFlags.READWRITE
        )

        # 3. Augenweiß & Glanzlichter schützen (Schieberegler 0..100)
        procedure.add_double_argument(
            "protect_whites",
            _("Augenweiß & Glanzlichter schützen (%)"),
            _("Schützt Augenweiß (Sclera), Zähne und Glanzlichter vor rötlichen/gelblichen Verfärbungen"),
            0.0, 100.0, 100.0,
            GObject.ParamFlags.READWRITE
        )

        # 4. Lichtgradient / Shading übertragen (Schieberegler 0..100)
        procedure.add_double_argument(
            "shading_transfer",
            _("Lichtgradient übertragen / Shading (%)"),
            _("Überträgt den räumlichen Hell-Dunkel-Verlauf (Lichtrichtung) der Zielszene auf das Gesicht"),
            0.0, 100.0, 50.0,
            GObject.ParamFlags.READWRITE
        )

        # 5. Helligkeit berücksichtigen (Checkbox)
        procedure.add_boolean_argument(
            "match_luminance",
            _("Globale Helligkeit anpassen"),
            _("Helligkeit und Kontrast ebenfalls anpassen (deaktivieren für reine Farbtonangleichung)"),
            True,
            GObject.ParamFlags.READWRITE
        )

        # 6. Referenzquelle (Dropdown)
        choice_ref = Gimp.Choice.new()
        choice_ref.add("layer_below", 0, _("Darunterliegende Ebene (Standard)"), _("Verwendet den Bereich der direkt darunter liegenden Ebene"))
        choice_ref.add("background", 1, _("Unterste Ebene (Hintergrund)"), _("Verwendet den Bereich der untersten Ebene im Bild"))

        procedure.add_choice_argument(
            "ref_mode",
            _("Referenz-Quelle"),
            _("Welche Ebene als Farbvorlage dienen soll (oder aktive Bildauswahl nutzen)"),
            choice_ref,
            "layer_below",
            GObject.ParamFlags.READWRITE
        )

        return procedure

if __name__ == '__main__':
    Gimp.main(ColorHarmonizerPlugin.__gtype__, sys.argv)