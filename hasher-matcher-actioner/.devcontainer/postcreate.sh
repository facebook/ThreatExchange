#!/bin/bash
set -e

pip install --editable .[all]

# Find Python packages in opt and install them
for setup_script in "$(find /workspace/opt -name setup.py)"
do
    module_dir="$(dirname "$setup_script")"
    pip install --editable "$module_dir"
done
