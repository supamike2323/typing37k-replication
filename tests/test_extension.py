"""Checks for age-specific contrasts and extension sample accounting."""

from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")

from typing37k.extension import AGE_BANDS, run_extension


class ExtensionTests(TestCase):
    def test_known_gaps_and_model_samples(self):
        rows = []
        expected_gaps = np.array([9, 7, 6, 4, 3])
        postures = {
            "both_hands;thumbs": 1,
            "right_hand;thumbs": 0,
            "left_hand;thumbs": 0,
            "right_hand;index_fingers": 0,
        }
        covariates = product(
            enumerate(AGE_BANDS), postures.items(), enumerate(("mobile", "tablet")),
            enumerate(("native", "usually")), enumerate(("qwerty", "other")), (-0.5, 0.5),
        )
        for age, posture, keyboard, english, layout, noise in covariates:
            age_index, age_band = age
            posture_name, two_thumb = posture
            keyboard_index, keyboard_name = keyboard
            english_index, english_name = english
            layout_index, layout_name = layout
            wpm = 31 + age_index + two_thumb * expected_gaps[age_index]
            rows.append({
                "AGE_BAND": age_band,
                "HAND_FINGER": posture_name,
                "KEYBOARD_TYPE": keyboard_name,
                "TYPE_ENGLISH": english_name,
                "LAYOUT": layout_name,
                "WPM": wpm + 2 * keyboard_index - english_index + layout_index + noise,
            })
        rows.append({**rows[0], "AGE_BAND": "60-69"})
        rows.append({**rows[0], "TYPE_ENGLISH": None})
        rows.append({**rows[0], "LAYOUT": " "})

        with TemporaryDirectory() as directory:
            output = Path(directory)
            run_extension(pd.DataFrame(rows), output)
            self.assertGreater((output / "figures/extension_age_gaps.png").stat().st_size, 0)
            contrasts = pd.read_csv(output / "tables/extension_age_gaps.csv")
            tests = pd.read_csv(output / "tables/extension_interaction_tests.csv").set_index("model")
            audit = pd.read_csv(output / "tables/extension_sample_audit.csv").pivot(
                index="model", columns="metric", values="n"
            )

        primary = contrasts.loc[contrasts["model"].eq("primary")]
        self.assertEqual(tuple(primary["age_band"]), AGE_BANDS)
        np.testing.assert_allclose(primary["adjusted_gap_wpm"], expected_gaps, atol=0.12)
        self.assertTrue((primary["ci95_low_wpm"] < primary["adjusted_gap_wpm"]).all())
        self.assertTrue((primary["ci95_high_wpm"] > primary["adjusted_gap_wpm"]).all())
        self.assertEqual(tests.loc["primary", "df_num"], 4)
        self.assertLess(tests.loc["primary", "p_value"], 0.001)

        self.assertEqual(audit.loc["primary", "cleaned_sample"], len(rows))
        self.assertEqual(audit.loc["primary", "eligible_age"], len(rows) - 1)
        self.assertEqual(audit.loc["primary", "missing_type_english"], 1)
        self.assertEqual(audit.loc["primary", "complete_cases"], 241)
        self.assertEqual(audit.loc["plus_layout", "missing_layout"], 1)
        self.assertEqual(audit.loc["plus_layout", "complete_cases"], 240)
        self.assertEqual(audit.loc["mobile_keyboard_only", "complete_cases"], 121)
        self.assertEqual(audit.loc["other_named_postures", "complete_cases"], 321)
        for model, group in contrasts.groupby("model"):
            total = group["n_comparison"].sum() + group["n_two_thumb"].sum()
            self.assertEqual(total, tests.loc[model, "n"])
            self.assertEqual(total, audit.loc[model, "complete_cases"])
