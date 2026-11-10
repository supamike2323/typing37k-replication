"""Estimate how the typing-speed difference associated with posture varies by age."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from patsy import build_design_matrices


AGE_BANDS = ("10-19", "20-29", "30-39", "40-49", "50-59")
REFERENCE_AGE = "20-29"
TWO_THUMBS = "both_hands;thumbs"
THUMB_POSTURES = (TWO_THUMBS, "left_hand;thumbs", "right_hand;thumbs")
NAMED_POSTURES = THUMB_POSTURES + (
    "both_hands;index_fingers",
    "left_hand;index_fingers",
    "right_hand;index_fingers",
)
MODEL_SPECS = (
    ("primary", THUMB_POSTURES, False, False),
    ("plus_layout", THUMB_POSTURES, False, True),
    ("mobile_keyboard_only", THUMB_POSTURES, True, False),
    ("other_named_postures", NAMED_POSTURES, False, False),
)


def _sample_for_model(data, postures, mobile_only, include_layout):
    """Return eligible complete cases with counts for each selection step."""
    age_eligible = data.loc[data["AGE_BAND"].isin(AGE_BANDS)]
    posture_eligible = age_eligible.loc[age_eligible["HAND_FINGER"].isin(postures)]
    sample = posture_eligible
    if mobile_only:
        sample = sample.loc[sample["KEYBOARD_TYPE"].eq("mobile")]

    variables = ["WPM", "KEYBOARD_TYPE", "TYPE_ENGLISH"]
    if include_layout:
        variables.append("LAYOUT")
    sample = sample.copy()
    for column in variables[1:]:
        sample[column] = sample[column].astype("string").str.strip().replace("", pd.NA)
    audit = {
        "cleaned_sample": len(data),
        "eligible_age": len(age_eligible),
        "eligible_posture": len(posture_eligible),
        "eligible_keyboard": len(sample),
        **{f"missing_{column.lower()}": int(sample[column].isna().sum()) for column in variables},
    }
    sample = sample.dropna(subset=variables).copy()
    audit["complete_cases"] = len(sample)
    sample["TWO_THUMB"] = sample["HAND_FINGER"].eq(TWO_THUMBS).astype(int)
    for column in variables[1:]:
        sample[column] = sample[column].astype(str)
    return sample, audit


def _fit_model(sample, include_layout):
    """Return the five adjusted gaps and a joint test of equal gaps."""
    cell_counts = sample.groupby(["AGE_BAND", "TWO_THUMB"], observed=True).size()
    if any(cell_counts.get((age, posture), 0) < 2 for age in AGE_BANDS for posture in (0, 1)):
        raise ValueError("The extension requires at least two observations per age and posture cell.")

    formula = (
        f"WPM ~ C(AGE_BAND, Treatment(reference='{REFERENCE_AGE}')) * TWO_THUMB"
        " + C(KEYBOARD_TYPE) + C(TYPE_ENGLISH)"
    )
    if include_layout:
        formula += " + C(LAYOUT)"
    fit = smf.ols(formula, data=sample, missing="raise").fit(cov_type="HC3", use_t=True)
    if fit.model.rank != len(fit.params) or not np.isfinite(fit.cov_params()).all().all():
        raise ValueError("The extension requires an identified model and finite HC3 covariance.")

    # Covariates enter additively, so their values cancel within each contrast.
    profiles = pd.DataFrame([sample.iloc[0].to_dict()] * (2 * len(AGE_BANDS)))
    profiles["AGE_BAND"] = np.repeat(AGE_BANDS, 2)
    profiles["TWO_THUMB"] = np.tile([0, 1], len(AGE_BANDS))
    design = np.asarray(build_design_matrices([fit.model.data.design_info], profiles)[0])
    gaps = design[1::2] - design[::2]
    estimates = fit.t_test(gaps)
    intervals = estimates.conf_int(alpha=0.05)
    reference = AGE_BANDS.index(REFERENCE_AGE)
    differences = np.delete(gaps - gaps[reference], reference, axis=0)
    joint_test = fit.f_test(differences)

    rows = []
    for index, age in enumerate(AGE_BANDS):
        group = sample.loc[sample["AGE_BAND"].eq(age)].groupby("TWO_THUMB")["WPM"]
        means = group.mean()
        rows.append(
            {
                "age_band": age,
                "n_comparison": int(cell_counts[age, 0]),
                "n_two_thumb": int(cell_counts[age, 1]),
                "mean_wpm_comparison": means[0],
                "mean_wpm_two_thumb": means[1],
                "raw_gap_wpm": means[1] - means[0],
                "adjusted_gap_wpm": float(estimates.effect[index]),
                "se_hc3_wpm": float(estimates.sd[index]),
                "ci95_low_wpm": intervals[index, 0],
                "ci95_high_wpm": intervals[index, 1],
            }
        )
    test = {
        "n": int(fit.nobs),
        "f_statistic_hc3": float(joint_test.fvalue),
        "df_num": int(joint_test.df_num),
        "df_denom": int(joint_test.df_denom),
        "p_value": float(joint_test.pvalue),
        "r_squared": float(fit.rsquared),
    }
    return rows, test


def _plot_gaps(primary, filename):
    """Draw adjusted and raw gaps with comparison counts in a separate column."""
    teal = "#006f72"
    dark = "#162b35"
    gray = "#58696f"
    with plt.rc_context({"font.family": "DejaVu Sans"}):
        fig, ax = plt.subplots(figsize=(8.8, 4.7))
        fig.subplots_adjust(left=0.145, right=0.76, top=0.72, bottom=0.22)
        y = np.arange(len(primary))
        center = primary["adjusted_gap_wpm"]
        adjusted = ax.errorbar(
            center, y + 0.08,
            xerr=[center - primary["ci95_low_wpm"], primary["ci95_high_wpm"] - center],
            fmt="o", color=teal, markersize=7, elinewidth=2, capsize=3,
            label="Adjusted gap with 95% CI", zorder=3,
        )
        raw = ax.scatter(
            primary["raw_gap_wpm"], y - 0.15, s=36, facecolor="white",
            edgecolor=gray, label="Raw gap", zorder=4,
        )
        for pos in y[:-1]:
            ax.axhline(pos + 0.5, color="#e7edef", linewidth=0.8, zorder=0)
        ax.axvline(0, color="#a0aeb3", linestyle="--", linewidth=0.9, zorder=1)
        ax.set_xlim(left=min(-0.6, ax.get_xlim()[0]))
        ax.set_ylim(len(y) - 0.55, -0.45)
        ax.set_yticks(y, labels=[age.replace("-", "–") for age in primary["age_band"]])
        ax.set_xlabel("Two-thumb minus one-thumb speed (words per minute)", labelpad=10, color=dark)
        ax.tick_params(axis="both", length=0, colors=dark, labelsize=10)
        ax.tick_params(axis="y", pad=12)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.spines["bottom"].set_visible(True)
        ax.spines["bottom"].set_color("#cbd7db")
        ax.legend(handles=[adjusted, raw], loc="lower left", bbox_to_anchor=(-0.02, 1.025), ncols=2,
                  frameon=False, labelcolor=dark, fontsize=9)
        ax.text(1.07, 1.06, "Participants", transform=ax.transAxes,
                color=dark, fontsize=10, fontweight="bold")
        for pos, row in zip(y, primary.itertuples(index=False), strict=True):
            ax.text(1.07, pos, f"{row.n_two_thumb:,} / {row.n_comparison:,}",
                    va="center", color=gray, fontsize=10, transform=ax.get_yaxis_transform())
        fig.text(0.065, 0.92, "The two-thumb typing-speed gap by age", color=dark,
                 fontsize=20, fontweight="bold")
        fig.text(0.065, 0.855, "Mobile transcription volunteers ages 10–59", color=gray, fontsize=11)
        fig.text(0.065, 0.066, "Counts show two-thumb / one-thumb users. Adjustment uses keyboard type and English typing experience.",
                 color=gray, fontsize=8.5)
        fig.savefig(filename, dpi=180, facecolor="white")
        plt.close(fig)


def run_extension(data: pd.DataFrame, output: Path) -> None:
    """Fit the primary and sensitivity models and save aggregate results."""
    contrast_rows, tests, audits = [], [], []
    for name, postures, mobile_only, include_layout in MODEL_SPECS:
        sample, audit = _sample_for_model(data, postures, mobile_only, include_layout)
        contrasts, test = _fit_model(sample, include_layout)
        contrast_rows.extend({"model": name, **row} for row in contrasts)
        tests.append({"model": name, **test})
        audits.extend({"model": name, "metric": metric, "n": count} for metric, count in audit.items())

    tables = output / "tables"
    figures = output / "figures"
    tables.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    contrasts = pd.DataFrame(contrast_rows)
    contrasts.to_csv(tables / "extension_age_gaps.csv", index=False)
    pd.DataFrame(tests).to_csv(tables / "extension_interaction_tests.csv", index=False)
    pd.DataFrame(audits).to_csv(tables / "extension_sample_audit.csv", index=False)
    _plot_gaps(contrasts.loc[contrasts["model"].eq("primary")], figures / "extension_age_gaps.png")
