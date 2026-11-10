# Replication of Palin et al. (2019)

I used Aalto’s public participant data to reproduce the main findings on mobile typing speed, errors, and posture. The study asked volunteers to type 15 English sentences on their own devices and collected posture and typing experience by questionnaire. I applied the authors’ filters and kept 37,370 of 37,606 records. The public data omit the geographic fields needed to recreate the U.S. subsample, so I used the paper’s full-sample benchmarks. [Published paper](https://www.pokristensson.com/pubs/PalinEtAlMobileHCI2019.pdf) · [Executed replication notebook](../replication.ipynb) · [Sample audit](../results/tables/sample_flow.csv)

## Performance and group comparisons

All four Table 3 means and sample standard deviations match at the published precision, including **36.17 words per minute (WPM)** and **2.34% uncorrected errors**. The 75th percentile for errors was 3.06%, compared with 3.07% in the paper’s text. [Table 3 results](../results/tables/replication_table_3_performance.csv)

Ages 10–19 averaged 39.63 WPM, the fastest age group. I got **28.05 WPM** for ages 40–49 versus **28.9 WPM** in Table 4. Two-thumb typists averaged 38.03 WPM, the fastest of the six listed postures. They made up 74.35% of the full sample and 82.33% of participants in those six postures. [Table 4 results](../results/tables/replication_table_4_demographics.csv) · [Posture shares](../results/tables/replication_posture_shares.csv)

The age and posture Kruskal–Wallis statistics match the supplement to two decimals. The age test uses seven bins, including 0–9 and 60–69, while Table 4 prints five. I used two-sided asymptotic Mann–Whitney U tests with standard Holm adjustment within each family. The authors’ code multiplies the ranked p-values by the remaining test counts. Standard Holm also takes a cumulative maximum and caps the result at one, so adjusted p-values can differ. [Omnibus tests](../results/tables/replication_omnibus_tests.csv) · [Pairwise tests](../results/tables/replication_pairwise_tests.csv) · [Authors’ notebook](https://userinterfaces.aalto.fi/typing37k/resources/python_analysis.ipynb) · [Supplement](https://userinterfaces.aalto.fi/typing37k/resources/supplement.pdf)

## Intelligent text entry

The WPM correlations reproduced the direction of the paper’s findings. Autocorrection had a positive correlation (+0.226 versus +0.237), and prediction had a negative one (−0.227 versus −0.183). The autocorrection-plus-gesture group averaged 40.22 WPM versus 33.8 WPM in the paper. I followed the authors’ gesture-to-prediction recoding and calculated correlations from the full sample, including zeros. Their notebook leaves out the exact Table 6 matrix code. [Table 5 results](../results/tables/replication_table_5_ite_groups.csv) · [Table 6 results](../results/tables/replication_table_6_ite_correlations.csv)

The age and posture comparisons motivated my extension on whether the two-thumb speed gap varies across age groups. Since volunteers chose how they typed, both analyses describe associations in this sample. [Original research report](extension.md)
