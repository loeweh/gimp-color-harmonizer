#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit-Tests für die Farbanpassungs-Algorithmen
"""

import unittest
import numpy as np
import color_harmonizer as ch

class TestColorHarmonizerAlgorithms(unittest.TestCase):

    def setUp(self):
        np.random.seed(42)
        # Source: Orange-Rot (z.B. Hautton bei warmem Licht)
        self.src_rgb = np.full((64, 64, 3), [0.85, 0.45, 0.25], dtype=np.float32)
        self.src_alpha = np.ones((64, 64), dtype=np.float32)
        
        # Target/Reference: Kühl/Bläulich (z.B. Schatten / kaltes Umgebungslicht)
        self.ref_rgb = np.full((128, 128, 3), [0.20, 0.40, 0.70], dtype=np.float32)
        self.ref_alpha = np.ones((128, 128), dtype=np.float32)

        self.src_samples = self.src_rgb.reshape(-1, 3)
        self.ref_samples = self.ref_rgb.reshape(-1, 3)

    def test_rgb_lab_roundtrip(self):
        rgb = np.random.uniform(0.0, 1.0, (32, 32, 3)).astype(np.float32)
        lab = ch.rgb_to_lab(rgb)
        rgb_rec = ch.lab_to_rgb(lab)
        err = np.max(np.abs(rgb - rgb_rec))
        self.assertLess(err, 1e-4, f"Farbraum-Rückkonvertierungsfehler zu groß: {err}")

    def test_reinhard(self):
        out = ch.apply_reinhard(self.src_rgb, self.src_samples, self.ref_samples, match_luminance=True, strength=1.0)
        self.assertEqual(out.shape, self.src_rgb.shape)
        self.assertTrue(np.all(out >= 0.0) and np.all(out <= 1.0))
        # Der Farbton sollte sich in Richtung Blau/Kühl verschoben haben
        self.assertGreater(np.mean(out[..., 2]), np.mean(self.src_rgb[..., 2]))

    def test_mkl(self):
        out = ch.apply_mkl(self.src_rgb, self.src_samples, self.ref_samples, strength=1.0)
        self.assertEqual(out.shape, self.src_rgb.shape)
        self.assertTrue(np.all(out >= 0.0) and np.all(out <= 1.0))

    def test_histogram(self):
        out = ch.apply_histogram(self.src_rgb, self.src_samples, self.ref_samples, match_luminance=True, strength=1.0)
        self.assertEqual(out.shape, self.src_rgb.shape)
        self.assertTrue(np.all(out >= 0.0) and np.all(out <= 1.0))

    def test_seamless(self):
        bg_crop = self.ref_rgb[:64, :64]
        out = ch.apply_seamless(self.src_rgb, self.src_alpha, bg_crop, self.src_samples, self.ref_samples, match_luminance=True, strength=1.0)
        self.assertEqual(out.shape, self.src_rgb.shape)
        self.assertTrue(np.all(out >= 0.0) and np.all(out <= 1.0))

    def test_strength_slider(self):
        # Bei Stärke 0% muss das Ergebnis exakt dem Original entsprechen
        out_0 = ch.apply_reinhard(self.src_rgb, self.src_samples, self.ref_samples, match_luminance=True, strength=0.0)
        np.testing.assert_allclose(out_0, self.src_rgb, atol=1e-5)

        out_mkl_0 = ch.apply_mkl(self.src_rgb, self.src_samples, self.ref_samples, strength=0.0)
        np.testing.assert_allclose(out_mkl_0, self.src_rgb, atol=1e-5)

if __name__ == '__main__':
    unittest.main()
