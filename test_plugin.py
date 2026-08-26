#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit-Tests für die erweiterten Farbanpassungs- und Schutz-Algorithmen
"""

import unittest
import numpy as np
import color_harmonizer as ch

class TestColorHarmonizerAlgorithms(unittest.TestCase):

    def setUp(self):
        np.random.seed(42)
        # Source: Orange-Rot (Hautton)
        self.src_rgb = np.full((64, 64, 3), [0.85, 0.45, 0.25], dtype=np.float32)
        self.src_alpha = np.ones((64, 64), dtype=np.float32)
        
        # Target/Reference: Kühl/Bläulich
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
        out = ch.apply_reinhard(self.src_rgb, self.src_samples, self.ref_samples, match_luminance=True)
        self.assertEqual(out.shape, self.src_rgb.shape)
        self.assertTrue(np.all(out >= 0.0) and np.all(out <= 1.0))
        self.assertGreater(np.mean(out[..., 2]), np.mean(self.src_rgb[..., 2]))

    def test_mkl(self):
        out = ch.apply_mkl(self.src_rgb, self.src_samples, self.ref_samples)
        self.assertEqual(out.shape, self.src_rgb.shape)
        self.assertTrue(np.all(out >= 0.0) and np.all(out <= 1.0))

    def test_histogram(self):
        out = ch.apply_histogram(self.src_rgb, self.src_samples, self.ref_samples, match_luminance=True)
        self.assertEqual(out.shape, self.src_rgb.shape)
        self.assertTrue(np.all(out >= 0.0) and np.all(out <= 1.0))

    def test_seamless(self):
        bg_crop = self.ref_rgb[:64, :64]
        out = ch.apply_seamless(self.src_rgb, self.src_alpha, bg_crop, self.src_samples, self.ref_samples, match_luminance=True)
        self.assertEqual(out.shape, self.src_rgb.shape)
        self.assertTrue(np.all(out >= 0.0) and np.all(out <= 1.0))

    def test_eye_white_and_highlight_protection(self):
        # Image with skin and eye white / highlight region
        img = np.full((32, 32, 3), [0.85, 0.60, 0.45], dtype=np.float32) # Warm skin
        img[10:15, 10:15] = [0.92, 0.92, 0.93] # Eye white
        img[20:22, 20:22] = [0.99, 0.99, 0.99] # Specular highlight

        mask = ch.compute_whites_protection_mask(img)
        self.assertEqual(mask.shape, (32, 32))
        
        # Skin should have low/zero protection
        self.assertLess(mask[0, 0], 0.1)
        # Eye white should have high protection (~1.0)
        self.assertGreater(mask[12, 12], 0.85)
        # Highlight should have full protection (1.0)
        self.assertAlmostEqual(mask[21, 21], 1.0, places=1)

    def test_shading_transfer(self):
        # Source is flat gray
        src = np.full((40, 40, 3), 0.5, dtype=np.float32)
        # Background is dark on left, bright on right
        bg = np.zeros((40, 40, 3), dtype=np.float32)
        bg[..., 0] = np.linspace(0.1, 0.9, 40)[None, :]
        bg[..., 1] = np.linspace(0.1, 0.9, 40)[None, :]
        bg[..., 2] = np.linspace(0.1, 0.9, 40)[None, :]

        shaded = ch.apply_shading_transfer(src, bg, shading_strength=0.8)
        self.assertEqual(shaded.shape, src.shape)
        # Left edge should become darker than right edge
        self.assertLess(np.mean(shaded[:, 0, :]), np.mean(shaded[:, -1, :]))

if __name__ == '__main__':
    unittest.main()
