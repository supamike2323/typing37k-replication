"""Command-line entry point for the Typing37K replication."""

import argparse
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from .data import load_data


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
    from .replication import run_replication

    data, audit = load_data(args.raw_dir, offline=args.offline, archive=args.archive)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".typing37k-", dir=args.output.parent) as staging_dir:
        staged = Path(staging_dir)
        for name in ("tables", "figures"):
            (staged / name).mkdir()
        run_replication(data, audit, staged)
        run_extension(data, staged)
        for name in ("tables", "figures"):
            destination = args.output / name
            destination.mkdir(parents=True, exist_ok=True)
            for result in sorted((staged / name).iterdir()):
                result.replace(destination / result.name)

    print(f"Analyzed {len(data):,} participants. Results are in {args.output.resolve()}.")


if __name__ == "__main__":
    main()
