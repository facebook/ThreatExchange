# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Dump the HMA OpenAPI specification to a JSON file.

The spec is fetched via the Flask test client to avoid relying on
flask-openapi3 internals: whatever the live server serves at
``/openapi/openapi.json`` is what we write to disk.

Usage:
    python scripts/dump_openapi.py path/to/openapi.json

If no output path is provided, ``openapi.json`` in the current working
directory is used.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = _REPO_ROOT / "src"
# HMA uses a src/ layout but pyproject.toml does not declare it for setuptools,
# so ``pip install -e .`` does not put ``OpenMediaMatch`` on sys.path. The
# Flask CLI papers over this with ``--app src/OpenMediaMatch.app``; we do the
# equivalent here so the script works regardless of how the package is
# installed.
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

DEFAULT_CONFIG = Path(__file__).resolve().with_name("openapi_dump_config.py")
DEFAULT_OUTPUT = Path("openapi.json")


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "output",
        nargs="?",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path to write the OpenAPI JSON to (default: %(default)s).",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="OMM_CONFIG file used to build the app (default: %(default)s).",
    )
    return parser.parse_args(argv)


def dump_spec(output: Path, config: Path) -> None:
    os.environ["OMM_CONFIG"] = str(config.resolve())

    # Imported after OMM_CONFIG is set so create_app() picks it up.
    from OpenMediaMatch.app import create_app

    app = create_app()

    with app.test_client() as client:
        response = client.get("/openapi/openapi.json")
        if response.status_code != 200:
            raise RuntimeError(
                f"Unexpected status {response.status_code} fetching OpenAPI spec: "
                f"{response.data!r}"
            )
        spec = response.get_json()

    if not isinstance(spec, dict) or "openapi" not in spec:
        raise RuntimeError("Response did not look like an OpenAPI document")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    dump_spec(args.output, args.config)
    print(f"Wrote OpenAPI spec to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
