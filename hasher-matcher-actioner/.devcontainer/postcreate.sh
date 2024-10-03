#!/bin/bash
set -e

pip install --editable .[all]

# Find Python packages in the extensions directory, and install them
for setup_script in "$(find /workspace/extensions -name setup.py)"
do
    module_dir="$(dirname "$setup_script")"
    pip install --editable "$module_dir"
    # Once they're installed by PIP we also need to enumerate
    # the Python package names (which aren't necessarily the same
    # as the module dir names), then enable them in the 
    # ThreatExchangeconfig using the threatexchange CLI.
    # TODO: Find a nicer way to do this.
    # It's quite an ugly hack
    for extension in "$(echo "import setuptools; [ print(p) for p in setuptools.find_packages('${module_dir}') ]" | python)"
    do
        if [ "$extension" != "" ]
        then
            threatexchange config extensions add "$extension"
        fi
    done
done
