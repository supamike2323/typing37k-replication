"""Command-line entry point for the Typing37K replication."""

import argparse
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType


REPLICATION_NOTEBOOK = Path(__file__).resolve().parent.parent / "replication.ipynb"


def load_replication_notebook() -> ModuleType:
    """Evaluate the tagged code cells from this repository's notebook in order."""
    path = REPLICATION_NOTEBOOK
    notebook = json.loads(path.read_text(encoding="utf-8"))
    module = ModuleType("typing37k.replication_notebook")
    module.__file__ = str(path)

    for number, cell in enumerate(notebook["cells"], start=1):
        tags = cell.get("metadata", {}).get("tags", [])
        if cell["cell_type"] != "code" or "replication-code" not in tags:
            continue
        source = "".join(cell["source"])
        code = compile(source, f"{path}:cell {number}", "exec", dont_inherit=True)
        exec(code, module.__dict__)

    return module


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["run"], help="regenerate both analyses")
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--output", type=Path, default=Path("results"))
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--offline", action="store_true", help="use verified cached data only")
    source.add_argument("--archive", type=Path, help="read members from the local official CSV ZIP")
    args = parser.parse_args()

    os.environ.setdefault("MPLBACKEND", "Agg")
    from .extension import run_extension

    replication = load_replication_notebook()
    data, audit = replication.load_data(args.raw_dir, offline=args.offline, archive=args.archive)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".typing37k-", dir=args.output.parent) as staging_dir:
        staged = Path(staging_dir)
        for name in ("tables", "figures"):
            (staged / name).mkdir()
        replication.run_replication(data, audit, staged)
        run_extension(data, staged)
        for name in ("tables", "figures"):
            destination = args.output / name
            destination.mkdir(parents=True, exist_ok=True)
            for result in sorted((staged / name).iterdir()):
                result.replace(destination / result.name)

    print(f"Analyzed {len(data):,} participants. Results are in {args.output.resolve()}.")


if __name__ == "__main__":
    main()
