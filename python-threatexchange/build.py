#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

from pathlib import Path
from typing import Dict, List

def get_extension_dependencies() -> Dict[str, List[str]]:
    """Get dependencies from extension directories."""
    here = Path(__file__).parent
    extensions_dir = here / "threatexchange" / "extensions"
    
    extras_require = {}
    
    # Process each extension directory
    for extension_dir in extensions_dir.iterdir():
        requirements = extension_dir / "requirements.txt"
        if requirements.is_file():
            extras_require[f"extensions.{extension_dir.name}"] = (
                requirements.read_text().strip().split("\n")
            )
    
    return extras_require

if __name__ == "__main__":
    # This can be used by build tools to dynamically generate dependencies
    extras = get_extension_dependencies()
    print(extras) 