"""Full-sample participant-level replication of Palin et al. (2019)."""

from itertools import combinations
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests


AGE_BANDS = ("0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69")
POSTURES = {
    "both_hands;thumbs": "Both thumbs",
    "both_hands;index_fingers": "Both index fingers",
    "right_hand;thumbs": "Right thumb",
    "right_hand;index_fingers": "Right index finger",
    "left_hand;thumbs": "Left thumb",
    "left_hand;index_fingers": "Left index finger",
}
ENGLISH = ("native", "always", "usually", "sometimes", "rarely", "never")
ITE_COLUMNS = {"P": "ITE_PREDICT", "A": "ITE_AUTOCORR", "G": "ITE_SWYPE"}

# Published full-sample values from Tables 3–6, in table order.
PERFORMANCE = {
    "WPM": ("Words per minute", 36.17, 13.22),
    "ERROR_RATE": ("Uncorrected error (%)", 2.34, 2.08),
    "P_KSPC": ("Keystrokes per character", 1.18, 0.18),
    "P_BSP": ("Backspaces per sentence", 1.89, 1.96),
}
DEMOGRAPHIC_GROUPS = {
    "gender": ("GENDER", ("female", "male"), ((36.0, 12.5), (36.1, 14.4))),
    "age": (
        "AGE_BAND",
        AGE_BANDS,
        (None, (39.6, 14.3), (36.5, 12.6), (32.2, 10.8),
         (28.9, 9.2), (26.3, 9.9), None),
    ),
    "english_experience": (
        "TYPE_ENGLISH",
        ENGLISH,
        ((37.8, 13.6), (35.9, 13.1), (34.5, 11.8),
         (30.4, 10.5), (29.6, 11.2), (25.6, 12.4)),
    ),
    "typing_course": ("HAS_TAKEN_TYPING_COURSE", (0, 1), ((36.4, 13.1), (35.7, 13.4))),
    "finger_count": ("NUM_FINGERS", (2, 1), ((37.7, 13.2), (29.2, 10.7))),
    "posture": (
        "HAND_FINGER",
        tuple(POSTURES),
        ((38.0, 13.1), (32.6, 12.7), (30.2, 10.5),
         (26.7, 9.7), (30.8, 12.4), (25.0, 11.4)),
    ),
}
ITE_GROUPS = {
    "none": (34.8, 12.6, 2.3, 1.2),
    "P": (32.8, 12.1, 2.3, 1.2),
    "A": (43.4, 14.4, 2.4, 1.2),
    "G": (32.2, 13.4, 2.4, 1.0),
    "P+A": (35.7, 12.6, 2.4, 1.2),
    "P+G": (31.5, 13.6, 2.2, 0.9),
    "A+G": (33.8, 12.1, 2.4, 1.1),
    "P+A+G": (28.8, 11.3, 2.4, 1.1),
}
ITE_CORRELATIONS = {
    "WPM": {"G": -0.003, "A": 0.237, "P": -0.183},
    "ERROR_RATE": {"G": -0.012, "A": 0.086, "P": -0.037},
    "P_KSPC": {"G": -0.251, "A": 0.181, "P": -0.232},
}
SUPPLEMENT_H = {
    "gender": 8.8426,
    "age": 2828.3453,
    "english_experience": 1364.9895,
    "posture": 2204.22245,
    "ite": 2288.61814,
}
BLUE = "#275f84"
TEAL = "#157d75"
AMBER = "#b65a25"
INK = "#142e43"


def _summarize(values: pd.Series) -> dict:
    return {
        "n": values.count(),
        "mean": values.mean(),
        "sd": values.std(),
        "min": values.min(),
        "p25": values.quantile(0.25),
        "median": values.median(),
        "p75": values.quantile(0.75),
        "max": values.max(),
    }


def _cohen_d(first: np.ndarray, second: np.ndarray) -> float:
    """Signed mean difference divided by the pooled sample SD."""
    df = len(first) + len(second) - 2
    sum_squares = ((first - first.mean()) ** 2).sum() + ((second - second.mean()) ** 2).sum()
    pooled_sd = np.sqrt(sum_squares / df)
    return (first.mean() - second.mean()) / pooled_sd if pooled_sd else np.nan


def _comparison_tests(families: dict[str, dict]) -> tuple[pd.DataFrame, pd.DataFrame]:
    omnibus = []
    pairwise = []
    for family, groups in families.items():
        available = {name: sample for name, sample in groups.items() if len(sample)}
        if len(available) < 2:
            continue

        kw = stats.kruskal(*available.values())
        omnibus.append({
            "family": family,
            "method": "Kruskal–Wallis",
            "n": sum(map(len, available.values())),
            "groups": len(available),
            "df": len(available) - 1,
            "statistic_h": kw.statistic,
            "p_value": kw.pvalue,
            "supplement_h": SUPPLEMENT_H.get(family),
            "group_levels": " | ".join(map(str, available)),
        })
        comparisons = []
        for (name_a, sample_a), (name_b, sample_b) in combinations(available.items(), 2):
            mw = stats.mannwhitneyu(sample_a, sample_b, alternative="two-sided", method="asymptotic")
            comparisons.append({
                "family": family,
                "group_a": name_a,
                "group_b": name_b,
                "n_a": len(sample_a),
                "n_b": len(sample_b),
                "u_a": mw.statistic,
                "mean_diff_a_minus_b": sample_a.mean() - sample_b.mean(),
                "cohen_d_a_minus_b": _cohen_d(sample_a, sample_b),
                "p_raw": mw.pvalue,
            })
        adjusted = multipletests([row["p_raw"] for row in comparisons], method="holm")[1]
        for row, p_holm in zip(comparisons, adjusted):
            row["p_holm"] = p_holm
            row["reject_5pct"] = p_holm < 0.05
            pairwise.append(row)
    return pd.DataFrame(omnibus), pd.DataFrame(pairwise)


def _demographics(data: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, dict]]:
    rows = []
    families = {}
    for family, (column, levels, benchmarks) in DEMOGRAPHIC_GROUPS.items():
        groups = {}
        for level, paper in zip(levels, benchmarks):
            sample = data.loc[data[column].eq(level), "WPM"].dropna()
            groups[level] = sample.to_numpy()
            paper_mean, paper_sd = paper or (np.nan, np.nan)
            label = POSTURES.get(level, level)
            if family == "typing_course":
                label = "yes" if level else "no"
            rows.append({
                "factor": family,
                "level": level,
                "label": label,
                "shown_in_paper_table_4": paper is not None,
                "n": len(sample),
                "percent_full_sample": 100 * len(sample) / len(data),
                "mean_wpm": sample.mean(),
                "sd_wpm": sample.std(),
                "paper_mean_wpm": paper_mean,
                "paper_sd_wpm": paper_sd,
                "mean_minus_paper": sample.mean() - paper_mean,
                "sd_minus_paper": sample.std() - paper_sd,
            })
        families[family] = groups
    return pd.DataFrame(rows), families


def _ite(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    # The notebook assigns categories using released ratios before the gesture transfer.
    raw_ratios = data[list(ITE_COLUMNS.values())].fillna(0)
    membership = pd.Series("", index=data.index, dtype="str")
    for key, column in ITE_COLUMNS.items():
        membership += np.where(raw_ratios[column].ne(0), key, "")
    membership = membership.str.replace(r"(?<=.)(?=.)", "+", regex=True).replace("", "none")

    groups = {}
    group_rows = []
    for label, (paper_wpm, paper_sd, paper_error, paper_kspc) in ITE_GROUPS.items():
        subset = data.loc[membership.eq(label)]
        groups[label] = subset["WPM"].dropna().to_numpy()
        group_rows.append({
            "ite_group": label,
            "n": len(subset),
            "percent_full_sample": 100 * len(subset) / len(data),
            "mean_wpm": subset["WPM"].mean(),
            "paper_mean_wpm": paper_wpm,
            "wpm_minus_paper": subset["WPM"].mean() - paper_wpm,
            "sd_wpm": subset["WPM"].std(),
            "paper_sd_wpm": paper_sd,
            "mean_error_percent": subset["ERROR_RATE"].mean(),
            "paper_mean_error_percent": paper_error,
            "mean_kspc": subset["P_KSPC"].mean(),
            "paper_mean_kspc": paper_kspc,
        })

    # For the ratio analysis, the notebook transfers inferred gestures into prediction
    # when the participant did not report swipe typing.
    ratios = raw_ratios.copy()
    transfer = ~data["USING_FEATURES"].str.contains("swipe", regex=False, na=False)
    ratios.loc[transfer, "ITE_PREDICT"] += ratios.loc[transfer, "ITE_SWYPE"]
    ratios.loc[transfer, "ITE_SWYPE"] = 0

    correlations = []
    for outcome, paper_values in ITE_CORRELATIONS.items():
        for key, paper_r in paper_values.items():
            valid = data[outcome].notna()
            result = stats.pearsonr(data.loc[valid, outcome], ratios.loc[valid, ITE_COLUMNS[key]])
            raw = stats.pearsonr(data.loc[valid, outcome], raw_ratios.loc[valid, ITE_COLUMNS[key]])
            correlations.append({
                "outcome": outcome,
                "ite_method": key,
                "n": valid.sum(),
                "pearson_r_notebook_recoding": result.statistic,
                "p_value_notebook_recoding": result.pvalue,
                "pearson_r_released_ratios": raw.statistic,
                "paper_pearson_r": paper_r,
                "recoded_r_minus_paper": result.statistic - paper_r,
            })
    return pd.DataFrame(group_rows), pd.DataFrame(correlations), groups


def _style_axis(ax) -> None:
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#c8d6df")
    ax.grid(axis="y", color="#e5edf1", linewidth=0.75)
    ax.set_axisbelow(True)
    ax.tick_params(length=0, colors=INK)


def _distribution_figure(data: pd.DataFrame, output: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), layout="constrained")
    for ax, key, color in zip(axes, list(PERFORMANCE)[:3], [BLUE, TEAL, AMBER]):
        title = PERFORMANCE[key][0]
        values = data[key].dropna()
        ax.hist(values, bins=45, density=True, color=color, alpha=0.78)
        ax.axvline(values.mean(), color=INK, linewidth=1.4, linestyle="--")
        ax.text(
            0.98, 0.94, f"Mean {values.mean():.2f}",
            transform=ax.transAxes, ha="right", va="top", color=INK,
        )
        ax.set_xlabel(title, color=INK)
        _style_axis(ax)
    axes[0].set_ylabel("Density", color=INK)
    fig.suptitle(f"Typing performance in the full sample · n = {len(data):,}", color=INK)
    fig.savefig(output, dpi=180, facecolor="white")
    plt.close(fig)


def _compare_means(ax, groups: pd.DataFrame, label: str, color: str, horizontal: bool = False):
    positions = np.arange(len(groups))
    means = groups["mean_wpm"]
    half_width = stats.t.ppf(0.975, groups["n"] - 1) * groups["sd_wpm"] / np.sqrt(groups["n"])
    paper = groups["paper_mean_wpm"]
    if horizontal:
        ax.errorbar(means, positions, xerr=half_width, fmt="o", color=color, capsize=2,
                    label="Replication, 95% CI")
        ax.scatter(paper, positions, facecolors="none", edgecolors=INK, s=80, label="Published mean")
        ax.set_yticks(positions, groups[label])
        ax.invert_yaxis()
        ax.set_xlabel("Words per minute", color=INK)
    else:
        ax.errorbar(positions, means, yerr=half_width, fmt="o", color=color, capsize=2,
                    label="Replication, 95% CI")
        ax.scatter(positions, paper, facecolors="none", edgecolors=INK, s=80, label="Published mean")
        ax.set_xticks(positions, groups[label])
        ax.set_ylabel("Words per minute", color=INK)
    _style_axis(ax)


def _group_figures(demographics: pd.DataFrame, ite_groups: pd.DataFrame, output: Path) -> None:
    fig, (age_ax, posture_ax) = plt.subplots(1, 2, figsize=(11, 4.4), layout="constrained")
    ages = demographics.loc[demographics["factor"].eq("age") & demographics["shown_in_paper_table_4"]]
    postures = demographics.loc[demographics["factor"].eq("posture")]
    _compare_means(age_ax, ages, "label", BLUE)
    _compare_means(posture_ax, postures, "label", TEAL, horizontal=True)
    age_ax.set_title("Age bands shown in Table 4", color=INK)
    posture_ax.set_title("Six postures shown in Table 4", color=INK)
    age_ax.legend(frameon=False, loc="lower left", fontsize=8.5)
    fig.savefig(output / "replication_age_and_posture.png", dpi=180, facecolor="white")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.2, 4.4), layout="constrained")
    _compare_means(ax, ite_groups, "ite_group", AMBER)
    ax.set_title("Speed by intelligent text entry group", color=INK)
    ax.set_xlabel("P = prediction    A = autocorrection    G = gesture", color=INK, labelpad=10)
    ax.legend(frameon=False, loc="lower left")
    fig.savefig(output / "replication_ite.png", dpi=180, facecolor="white")
    plt.close(fig)


def run_replication(data: pd.DataFrame, audit: pd.DataFrame, output: Path) -> None:
    """Save aggregate full-sample comparisons, feasibility summaries and figures."""
    tables = output / "tables"
    figures = output / "figures"
    tables.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)

    performance = pd.DataFrame([
        {
            "metric": name,
            "label": label,
            **_summarize(data[name]),
            "paper_mean": paper_mean,
            "paper_sd": paper_sd,
            "mean_minus_paper": data[name].mean() - paper_mean,
            "sd_minus_paper": data[name].std() - paper_sd,
        }
        for name, (label, paper_mean, paper_sd) in PERFORMANCE.items()
    ])
    demographics, families = _demographics(data)
    ite_groups, correlations, ite_samples = _ite(data)
    families["ite"] = ite_samples
    omnibus, pairwise = _comparison_tests(families)

    posture_counts = data["HAND_FINGER"].value_counts()
    n_six_postures = posture_counts.reindex(POSTURES, fill_value=0).sum()
    postures = pd.DataFrame([
        {
            "posture": posture,
            "n": n,
            "percent_full_sample": 100 * n / len(data),
            "included_in_table_4": posture in POSTURES,
            "percent_of_six_postures": 100 * n / n_six_postures if posture in POSTURES else np.nan,
        }
        for posture, n in posture_counts.items()
    ])

    proposal_continuous = pd.DataFrame([
        {"variable": name, "missing": data[name].isna().sum(), **_summarize(data[name])}
        for name in ("AGE", "WPM", "ERROR_RATE", "TIME_SPENT_TYPING")
    ])
    proposal_categories = data.assign(
        TWO_THUMBS=data["HAND_FINGER"].eq("both_hands;thumbs")
    )[["AGE_BAND", "TWO_THUMBS", "KEYBOARD_TYPE", "LAYOUT", "TYPE_ENGLISH"]]
    proposal_categorical = pd.DataFrame([
        {"variable": name, "level": level, "n": n, "percent_full_sample": 100 * n / len(data)}
        for name in proposal_categories
        for level, n in proposal_categories[name].value_counts(dropna=False).items()
    ])
    frames = {
        "replication_table_3_performance": performance,
        "replication_table_4_demographics": demographics,
        "replication_table_5_ite_groups": ite_groups,
        "replication_table_6_ite_correlations": correlations,
        "replication_omnibus_tests": omnibus,
        "replication_pairwise_tests": pairwise,
        "replication_posture_shares": postures,
        "sample_flow": audit,
        "proposal_continuous": proposal_continuous,
        "proposal_categorical": proposal_categorical,
    }
    for filename, frame in frames.items():
        frame.to_csv(tables / f"{filename}.csv", index=False, float_format="%.10g")

    _distribution_figure(data, figures / "replication_performance_distributions.png")
    _group_figures(demographics, ite_groups, figures)
