# Does the two-thumb typing gap vary with age?

STAT 5200 applied econometrics project by Mike Deng. The notebook replicates the study’s full-sample results, and the extension estimates how the typing-speed gap between one-thumb and two-thumb users varies by age. [Palin et al. (2019)](https://doi.org/10.1145/3338286.3340120)

- **[Start with the executed replication notebook](replication.ipynb)**
- [Replication report](docs/replication.md)
- [Original research report](docs/extension.md)
- [One-page project proposal](docs/proposal.pdf)
- [Class presentation with speaker notes](docs/presentation.pptx)

## Reproduce the results

Set up Python 3.12 from the repository root.

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

Open `replication.ipynb` in a Jupyter kernel using this environment and select **Run All**. If you need JupyterLab, install it with `python -m pip install jupyterlab` and start it with `python -m jupyterlab replication.ipynb`.

Run `python -m typing37k run` to regenerate the replication and extension outputs under `results/`. Add `--offline` to use verified cached data or use `--help` for archive, cache, and output options. [Data source and checksums](data/README.md) · [Result tables](results/tables/) · [Figures](results/figures/)
