#!/bin/bash
set -e

pip install --editable .[all]

# Find Python packages in opt and install them
for setup_script in "$(find /workspace/extensions -name setup.py)"
do
    module_dir="$(dirname "$setup_script")"
    pip install --editable "$module_dir"
    for extension in "$(echo "import setuptools; [ print (p) for p in setuptools.find_packages('${module_dir}') ]" | python)"
    do
        threatexchange config extensions add "$extension"
    done
done
