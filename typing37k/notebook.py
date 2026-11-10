"""Load the replication definitions shared by the notebook and command line."""

import json
from pathlib import Path
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
