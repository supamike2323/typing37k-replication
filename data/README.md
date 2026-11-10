# Aalto Typing37K data

The `raw/` folder contains byte-for-byte copies of the two files used in the replication. Both come from the processed release by Palin et al. (2019). [Aalto project page](https://userinterfaces.aalto.fi/typing37k/) · [Official CSV archive](https://userinterfaces.aalto.fi/typing37k/data/csv_raw_and_processed.zip)

| Archive member | SHA-256 of uncompressed bytes |
| --- | --- |
| `Data_Processed/open_participants.csv` | `26c1abdc46c1f98121b1189969e084a73f9d10228c69e0c8035a4290e82e74ba` |
| `Data_Processed/open_participants_header.csv` | `79d7b717343ad61287c36c702998de22dd1f6385e9dc39a9d4da6366acbe87a4` |

The notebook and command-line runner verify both files against these checksums. If you run the notebook by itself, it can fetch the two members from Aalto using a 3.8 MB HTTP byte range. The command-line runner can also read a local copy of the official ZIP with `--archive /path/to/csv_raw_and_processed.zip`.

The participant CSV has 28 fields and no embedded column header. The schema file supplies the column names. The CSV uses Latin-1 decoding and MySQL backslash escapes. The pipeline rejects unexpected field widths and duplicate participant IDs before analysis. It works with the released participant-level aggregates, including the already computed words per minute (WPM), percentage of uncorrected errors, keystrokes per character, and average backspaces per sentence.

The study design and processing decisions are described in the paper and the authors’ notebook. [Paper](https://doi.org/10.1145/3338286.3340120) · [Authors’ notebook](https://userinterfaces.aalto.fi/typing37k/resources/python_analysis.ipynb)
