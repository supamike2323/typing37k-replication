# Typing37K replication and research project

STAT 5200 applied econometrics project by Mike Deng.

## Replication

I reproduce full-sample results on mobile typing speed, errors, posture, and keyboard assistance. [Palin et al. (2019)](https://doi.org/10.1145/3338286.3340120)

- [Executed replication notebook](replication.ipynb)
- [Replication report](docs/replication.md)
- [Replication presentation with speaker notes](docs/presentation.pptx)

## Original research

I estimate how the typing-speed gap between one-thumb and two-thumb users varies by age.

- [Executed extension notebook](extension.ipynb)
- [Original research report](docs/extension.md)
- [One-page project proposal](docs/proposal.pdf)

## Reproduce the results

Set up Python 3.12 from the repository root.

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

Open `replication.ipynb` or `extension.ipynb` from the repository root in a Jupyter kernel using this environment and select **Run All**. Each notebook can run in a fresh kernel. The extension reuses the replication’s data preparation and the model code in `typing37k/extension.py`. If you need JupyterLab, install it with `python -m pip install jupyterlab` and start it with `python -m jupyterlab`.

The repository includes both Aalto CSVs used in the analysis. Once the dependencies are installed, run `python -m typing37k run --offline` to verify those files and regenerate the replication and extension outputs under `results/`. [Participant files](data/raw/) · [Data source and checksums](data/README.md) · [Result tables](results/tables/) · [Figures](results/figures/)
