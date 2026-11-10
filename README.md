# Does the two-thumb typing gap vary with age?

STAT 5200 applied econometrics project by Mike Deng. This repository replicates the full-sample participant-level findings from [Palin et al. (2019)](https://doi.org/10.1145/3338286.3340120) and estimates how the association between typing posture and speed varies by age.

- [One-page project proposal](docs/proposal.pdf)
- [Replication report](docs/replication.md)
- [Original research report](docs/extension.md)
- [Class presentation with speaker notes](docs/presentation.pptx)

The replication recovers **36.17 WPM** and **2.34% uncorrected errors** in 37,370 volunteers. In the 31,198-person extension sample, the adjusted two-thumb gap is **8.56 WPM** at ages 10–19 and ranges from **5.09 to 6.25 WPM** across the four older bands.

## Reproduce the results

From the repository root, use Python 3.12 in an isolated environment.

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m typing37k run
python -m unittest discover -s tests -v
```

The first run fetches two checksummed members of the public Aalto CSV ZIP in a single 3.8 MB range request. Subsequent runs can use `python -m typing37k run --offline`. If the server does not honor range requests, download the [official CSV archive](https://userinterfaces.aalto.fi/typing37k/data/csv_raw_and_processed.zip) and pass `--archive /path/to/csv_raw_and_processed.zip`. Use `--raw-dir` for a different cache and `--output` to build results in a separate directory. [Data provenance and checksums](data/README.md)

The command regenerates CSVs and figures under `results/`. The [sample audit](results/tables/sample_flow.csv) records sequential exclusions. The four files named `replication_table_*` provide the paper benchmarks and reproduced estimates. The [extension contrast table](results/tables/extension_age_gaps.csv) includes raw and adjusted gaps, confidence intervals and sample counts for every specification. The reports and class deck explain the results. The repository tracks aggregate results, while participant data stay in the local cache.
