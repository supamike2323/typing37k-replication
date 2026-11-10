# Aalto Typing37K data

The [Aalto project page](https://userinterfaces.aalto.fi/typing37k/) links the public CSV archive, processed database, analysis notebook, and statistical supplement. The replication uses two members of the [official CSV archive](https://userinterfaces.aalto.fi/typing37k/data/csv_raw_and_processed.zip). The archive contains both raw and processed releases.

| Archive member | SHA-256 of uncompressed bytes |
| --- | --- |
| `Data_Processed/open_participants.csv` | `26c1abdc46c1f98121b1189969e084a73f9d10228c69e0c8035a4290e82e74ba` |
| `Data_Processed/open_participants_header.csv` | `79d7b717343ad61287c36c702998de22dd1f6385e9dc39a9d4da6366acbe87a4` |

The downloader uses an HTTP byte range to read both members in about 3.8 MB. It checks the server response and the extracted bytes. The same members can be read directly from a local copy of the official ZIP with `--archive /path/to/csv_raw_and_processed.zip`. Subsequent runs verify the cached files in `data/raw/`. Keep both files there for offline runs.

The participant CSV has 28 fields and no embedded column header. The schema file supplies the column names. The CSV uses Latin-1 decoding and MySQL backslash escapes. The pipeline rejects unexpected field widths and duplicate participant IDs before analysis. It works with the released participant-level aggregates, including the already computed words per minute (WPM), percentage of uncorrected errors, keystrokes per character, and average backspaces per sentence.

The repository distributes original code and aggregate results. Obtain participant-level files from Aalto. See the [paper](https://doi.org/10.1145/3338286.3340120) and [authors’ notebook](https://userinterfaces.aalto.fi/typing37k/resources/python_analysis.ipynb) for the study design and processing decisions.
